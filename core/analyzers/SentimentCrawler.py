import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import re
import logging
import importlib
import random
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from html import unescape
from urllib.parse import urljoin
import httpx
from colorama import Fore, Style, init
from fake_useragent import UserAgent
from core.market import MarketLists

init(autoreset=True)
logger = logging.getLogger(__name__)

def _optional_import(module_name):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None

try:
    from playwright.sync_api import sync_playwright
    # Try to import Stealth from playwright_stealth
    try:
        from playwright_stealth import Stealth
        _stealth_obj = Stealth()
        def stealth_sync(page):
            _stealth_obj.apply_stealth_sync(page)
    except (ImportError, Exception):
        logger.warning("SentimentCrawler: playwright-stealth assets missing or failed to load. Browser stealth disabled.")
        stealth_sync = None
except (ImportError, Exception):
    sync_playwright = None
    stealth_sync = None

# SOURCES
ENTERPRISE_URL = "https://enterpriseam.com/egypt/"
MUBASHER_NEWS_URL = "https://english.mubasher.info/markets/EGX"
MUBASHER_LATEST_URL = "https://www.mubasher.info/news/eg/now/latest"
MUBASHER_STOCKS_PULSE_URL = "https://www.mubasher.info/news/eg/pulse/stocks"
ARAB_FINANCE_NEWS_URL = "https://www.arabfinance.com/en/news/newscategory"
ARAB_FINANCE_RSS_URLS = (
    "https://www.arabfinance.com/en/rss/rssbycat/1",
    "https://www.arabfinance.com/en/rss/rssbycat/2",
    "https://www.arabfinance.com/en/rss/rssbycat/10",
)
AMWAL_AL_GHAD_EGX_URL = "https://en.amwalalghad.com/category/stocks/c1-egx/"
ARGAAM_SAUDI_URL = "https://www.argaam.com/en"
# Reuters blocks all non-browser requests with 401 Forbidden.
# Kept for reference; async_fetch_us_news() now returns [] immediately.
REUTERS_MACRO_URL = "https://www.reuters.com/business/finance/"

SAUDI_NEWS_SOURCES = {"argaam"}
SAUDI_MARKET_CONTEXT_MARKERS = (
    "argaam",
    "tadawul",
    "saudi exchange",
    "saudi capital market",
    "saudi market",
    "saudi stock",
    "saudi stocks",
    "saudi market intelligence",
    "aljazira capital",
    "ades holding",
    "cenomi",
    "kingdom holding",
    "aramco",
    "\u0627\u0644\u0633\u0648\u0642 \u0627\u0644\u0633\u0639\u0648\u062f\u064a",
    "\u0627\u0644\u0623\u0633\u0647\u0645 \u0627\u0644\u0633\u0639\u0648\u062f\u064a\u0629",
    "\u062a\u062f\u0627\u0648\u0644 \u0627\u0644\u0633\u0639\u0648\u062f\u064a\u0629",
    "\u0627\u0644\u0633\u0648\u0642 \u0627\u0644\u0645\u0627\u0644\u064a\u0629 \u0627\u0644\u0633\u0639\u0648\u062f\u064a\u0629",
)
EGX_CONTEXT_MARKERS = (
    "egx",
    ".ca",
    "egp",
    "egypt",
    "egyptian",
    "cairo",
    "enterpriseam.com",
    "enterprise.press",
    "mubasher.info/markets/egx",
    "arabfinance.com",
    "amwalalghad.com",
    "en.amwalalghad.com",
)
COMPANY_NAME_SUFFIXES = (
    " s.a.e",
    " co.",
    " sae",
    " group",
    " holding",
    " holdings",
    " egyptian",
    " co",
)
GENERIC_COMPANY_NAME_WORDS = {
    "capital",
    "holding",
    "holdings",
    "group",
    "company",
    "co",
    "bank",
    "development",
    "investment",
    "investments",
    "financial",
    "finance",
    "international",
    "industrial",
    "industries",
    "services",
    "sae",
    "s.a.e",
    "egyptian",
}
LOCATION_NAME_WORDS = {
    "alexandria",
    "cairo",
    "egypt",
}
CONNECTOR_NAME_WORDS = {
    "and",
    "of",
    "the",
}
TRAILING_BUSINESS_WORDS = {
    "goods",
    "services",
    "products",
}
NEWS_TICKER_ALIASES = {
    "ALCN": ("alexandria container", "alexandria containers"),
    "VALU": ("valu",),
}

# KEYWORDS FOR SENTIMENT (Institutional Weighting)
BULLISH_KEYWORDS = {
    "acquisition": 2, "profit": 2, "increase": 1, "dividend": 2, "growth": 1, 
    "expansion": 1, "partnership": 1, "positive": 1, "signed": 2, "recovery": 1, 
    "surge": 2, "outperform": 2, "buyback": 2, "launch": 1, "contract": 2, 
    "approval": 1, "merger": 2, "revenue": 1, "jump": 1, "rebound": 1
}

BEARISH_KEYWORDS = {
    "loss": 2, "decrease": 1, "decline": 1, "lawsuit": 2, "crash": 2, "fall": 1, 
    "corruption": 3, "fine": 2, "deficit": 2, "negative": 1, "cancellation": 2, 
    "dispute": 1, "default": 3, "bankruptcy": 3, "suspension": 2, "underperform": 2,
    "probe": 2, "raid": 3, "resignation": 2
}

# ARABIC SENTIMENT (Institutional weighting for EGX news)
ARABIC_BULLISH = {
    "فوز": 2, "ربح": 2, "ارباح": 2, "ارتفاع": 1, "صعود": 1, "نمو": 1, "توزيع": 2, 
    "استحواذ": 2, "شراكة": 1, "إيجابي": 1, "إيجابية": 1, "قفزة": 2, "انتعاش": 1, "توقعات": 1
}

ARABIC_BEARISH = {
    "خسارة": 2, "خسائر": 2, "انخفاض": 1, "هبوط": 1, "تراجع": 1, "سلبى": 1, 
    "سلبية": 1, "قضية": 2, "تحقيق": 2, "إفلاس": 3, "استقالة": 2, "توقف": 2, "انهيار": 3, "أزمة": 2
}

# BIFROST - Mortal chatter analyzer
BIFROST_BULLISH_RUNES = ['rocket', 'buy', 'green', 'breakout', 'moon', 'profit', 'up']
BIFROST_BEARISH_RUNES = ['crash', 'sell', 'blood', 'dump', 'red', 'loss', 'down', 'halas']

@dataclass
class ScrapingResult:
    content: str
    title: str
    method: str
    html: str = ""

class PoisonPillDetector:
    """Detects blocks, paywalls, and anti-bot challenges."""
    PATTERNS = {
        "bot_challenge": [r"checking your browser", r"verify you are human", r"cloudflare", r"ddos protection"],
        "paywall": [r"subscribe to continue", r"subscription required", r"become a member"],
        "rate_limit": [r"too many requests", r"rate limit exceeded", r"slow down"]
    }

    def detect(self, html: str) -> Optional[str]:
        html_lower = html.lower()
        for ptype, patterns in self.PATTERNS.items():
            for p in patterns:
                if re.search(p, html_lower):
                    return ptype
        return None

class Scraper(ABC):
    @abstractmethod
    def fetch(self, url: str) -> Optional[ScrapingResult]:
        pass

class TrafilaturaScraper(Scraper):
    """Extremely fast, lightweight text extraction."""
    def fetch(self, url: str) -> Optional[ScrapingResult]:
        trafilatura = _optional_import("trafilatura")
        if not trafilatura: return None
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded: return None
            
            content = trafilatura.extract(downloaded, include_comments=False, favor_recall=True)
            if not content or len(content) < 100: return None
            
            soup = BeautifulSoup(downloaded, 'html.parser')
            title = soup.find('title').get_text(strip=True) if soup.find('title') else ""
            
            return ScrapingResult(content, title, "trafilatura", downloaded)
        except Exception:
            return None

class RequestsScraper(Scraper):
    """Standard HTTP extraction with rotating headers."""
    def __init__(self):
        self.ua = UserAgent()

    def fetch(self, url: str) -> Optional[ScrapingResult]:
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200: return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            # Basic cleanup
            for s in soup(['script', 'style', 'nav', 'footer']): s.decompose()
            
            content = soup.get_text(separator=' ', strip=True)
            title = soup.find('title').get_text(strip=True) if soup.find('title') else ""
            
            return ScrapingResult(content, title, "requests", response.text)
        except Exception:
            return None

class PlaywrightScraper(Scraper):
    """Heavyweight JS rendering fallback for anti-bot bypass."""
    def fetch(self, url: str) -> Optional[ScrapingResult]:
        if not sync_playwright: return None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                if stealth_sync:
                    stealth_sync(page)
                
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(1000) # Micro-sleep for dynamic content
                
                content = page.evaluate("() => document.body.innerText")
                title = page.title()
                html = page.content()
                
                browser.close()
                return ScrapingResult(content, title, "playwright", html)
        except Exception as e:
            logger.debug(f"SentimentCrawler: Playwright failed: {e}")
            return None

class ScrapingCascade:
    """Orchestrates scrapers with fallback logic and poison pill detection."""
    def __init__(self):
        self.scrapers = [TrafilaturaScraper(), RequestsScraper(), PlaywrightScraper()]
        self.detector = PoisonPillDetector()

    def fetch(self, url: str) -> Optional[ScrapingResult]:
        for scraper in self.scrapers:
            result = scraper.fetch(url)
            if not result: continue
            
            block_type = self.detector.detect(result.html)
            if block_type:
                logger.warning(f"SentimentCrawler: {scraper.__class__.__name__} hit {block_type} pill at {url}")
                continue
                
            return result
        return None

# Singleton instance
CASCADE = ScrapingCascade()

def analyze_mortal_whispers(text_list):
    """Analyzes a list of messages for bullish/bearish keyword pressure."""
    bull_count = 0
    bear_count = 0
    # Combine informal "runes" with professional and Arabic keywords
    all_bull = BIFROST_BULLISH_RUNES + list(BULLISH_KEYWORDS.keys()) + list(ARABIC_BULLISH.keys())
    all_bear = BIFROST_BEARISH_RUNES + list(BEARISH_KEYWORDS.keys()) + list(ARABIC_BEARISH.keys())

    bull_patterns = [re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE) for word in all_bull]
    bear_patterns = [re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE) for word in all_bear]

    for msg in text_list:
        text = str(msg or "")
        for pattern in bull_patterns: bull_count += len(pattern.findall(text))
        for pattern in bear_patterns: bear_count += len(pattern.findall(text))

    total = bull_count + bear_count
    if total == 0:
        return {"score": 50.0, "regime": "NEUTRAL", "bull_count": 0, "bear_count": 0, "total_hits": 0, "sample_size": len(text_list)}

    sentiment_score = (bull_count / total) * 100.0
    if sentiment_score >= 75: status = "BULLISH EXUBERANCE"
    elif sentiment_score >= 60: status = "MODERATE OPTIMISM"
    elif sentiment_score <= 25: status = "BEARISH PANIC"
    elif sentiment_score <= 40: status = "CAUTIOUS PESSIMISM"
    else: status = "NEUTRAL / STABLE"

    return {"score": round(sentiment_score, 2), "regime": status, "bull_count": bull_count, "bear_count": bear_count, "total_hits": total, "sample_size": len(text_list)}

def get_bifrost_sentiment(news_input):
    """Converts processed news items into mortal whispers and evaluates sentiment.
    Handles both raw lists of stories and the full SentimentCrawler gossip dictionary.
    """
    if not news_input:
        return analyze_mortal_whispers([])

    stories = []
    if isinstance(news_input, dict):
        stories = news_input.get("stories", [])
    elif isinstance(news_input, list):
        stories = news_input

    texts = []
    for item in stories:
        title = item.get("title") or item.get("Headline") or ""
        summary = item.get("summary") or ""
        text = f"{title} {summary}".strip()
        if text: texts.append(text)
    return analyze_mortal_whispers(texts)


def _clean_news_text(value) -> str:
    text = str(value or "")
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    else:
        text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _news_link(base_url: str, href: str) -> str:
    href = str(href or "").strip()
    if not href:
        return ""
    if href.startswith("#") or href.lower().startswith(("javascript:", "mailto:")):
        return ""
    return urljoin(base_url, href)


def _append_story(stories: list, *, source: str, title: str, link: str, summary: str = "") -> None:
    title = _clean_news_text(title)
    link = str(link or "").strip()
    summary = _clean_news_text(summary)[:250]
    if len(title) <= 25 or not link:
        return

    title_key = title.lower()
    link_key = link.lower()
    if any(story["title"].lower() == title_key or story["link"].lower() == link_key for story in stories):
        return

    stories.append({"source": source, "title": title, "link": link, "summary": summary})


def _dedupe_news_stories(stories: list, *, limit: int) -> list:
    deduped = []
    for story in stories:
        _append_story(
            deduped,
            source=story.get("source", ""),
            title=story.get("title", ""),
            link=story.get("link", ""),
            summary=story.get("summary", ""),
        )
    return deduped[:limit]


def _extract_rss_stories(xml_text: str, *, source: str, base_url: str, limit: int = 12) -> list:
    soup = BeautifulSoup(xml_text or "", "xml")
    stories = []
    for item in soup.find_all("item"):
        title_tag = item.find("title")
        link_tag = item.find("link")
        description_tag = item.find("description")
        _append_story(
            stories,
            source=source,
            title=title_tag.get_text(" ", strip=True) if title_tag else "",
            link=_news_link(base_url, link_tag.get_text(" ", strip=True) if link_tag else ""),
            summary=description_tag.get_text(" ", strip=True) if description_tag else "",
        )
        if len(stories) >= limit:
            break
    return stories


def _extract_arabfinance_stories(html: str, *, limit: int = 18) -> list:
    soup = BeautifulSoup(html or "", "html.parser")
    stories = []
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href", "")
        if "/en/news/newdetails/" not in href:
            continue
        _append_story(
            stories,
            source="Arab Finance",
            title=a_tag.get_text(" ", strip=True),
            link=_news_link(ARAB_FINANCE_NEWS_URL, href),
        )
        if len(stories) >= limit:
            break
    return stories


def _extract_amwal_alghad_stories(html: str, *, limit: int = 16) -> list:
    marker_index = (html or "").find("Browsing Category")
    category_html = html[marker_index:] if marker_index >= 0 else html
    soup = BeautifulSoup(category_html or "", "html.parser")
    stories = []
    skip_paths = ("/category/", "/tag/", "/author/", "/wp-content/")
    for article in soup.find_all("article"):
        a_tag = (
            article.select_one("a.post-title[href]")
            or article.select_one("a.post-url[href]")
            or article.find("a", href=True)
        )
        if not a_tag:
            continue
        summary_tag = article.select_one(".post-summary")
        _append_story(
            stories,
            source="Amwal Al Ghad",
            title=a_tag.get_text(" ", strip=True) or a_tag.get("title", ""),
            link=_news_link(AMWAL_AL_GHAD_EGX_URL, a_tag.get("href", "")),
            summary=summary_tag.get_text(" ", strip=True) if summary_tag else "",
        )
        if len(stories) >= limit:
            return stories

    for a_tag in soup.find_all("a"):
        href = a_tag.get("href", "")
        link = _news_link(AMWAL_AL_GHAD_EGX_URL, href)
        if not link or "amwalalghad.com" not in link:
            continue
        if any(path in link for path in skip_paths):
            continue
        _append_story(
            stories,
            source="Amwal Al Ghad",
            title=a_tag.get_text(" ", strip=True),
            link=link,
        )
        if len(stories) >= limit:
            break
    return stories


async def async_fetch_enterprise_news():
    logger.debug("SentimentCrawler: fetching Enterprise.press stories via Async Cascade")
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            headers = {'User-Agent': UserAgent().random}
            response = await client.get(ENTERPRISE_URL, headers=headers)
            if response.status_code != 200: return []
            html = response.text
        except Exception as e:
            logger.warning(f"SentimentCrawler: Async Enterprise fetch failed: {e}")
            return []
            
    soup = BeautifulSoup(html, 'html.parser')
    stories = []
    potential_tags = soup.find_all(['h2', 'h3', 'article'], limit=20)
    for tag in potential_tags:
        link_tag = tag.find('a') if tag.name != 'a' else tag
        if not link_tag: continue
        href = link_tag.get('href', "")
        title = link_tag.get_text(strip=True)
        if len(title) > 20 and ('enterpriseam.com' in href or 'enterprise.press' in href):
            if any(s['title'] == title for s in stories): continue
            summary = ""
            if tag.name == 'article':
                summary_tag = tag.find('div', class_='entry-content') or tag.find('p')
                if summary_tag: summary = summary_tag.get_text(strip=True)[:250]
            stories.append({'source': 'Enterprise', 'title': title, 'link': href, 'summary': summary})
    return stories[:12]

async def async_fetch_mubasher_news():
    """Fetches stories from both English and Arabic feeds."""
    logger.debug("SentimentCrawler: fetching Mubasher.info stories")
    urls = [MUBASHER_NEWS_URL, MUBASHER_LATEST_URL, MUBASHER_STOCKS_PULSE_URL]
    all_stories = []
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for url in urls:
            try:
                headers = {'User-Agent': UserAgent().random}
                response = await client.get(url, headers=headers)
                if response.status_code != 200: continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                for a_tag in soup.find_all('a'):
                    title = a_tag.get_text(strip=True)
                    href = a_tag.get('href', "")
                    if len(title) > 25 and ('/news/' in href or 'article' in href):
                        link = "https://www.mubasher.info" + href if not href.startswith('http') else href
                        if any(s['title'] == title for s in all_stories): continue
                        all_stories.append({'source': 'Mubasher', 'title': title, 'link': link, 'summary': ""})
            except Exception as e:
                logger.warning(f"SentimentCrawler: Mubasher fetch failed for {url}: {e}")
                
    return all_stories[:20]


async def async_fetch_arabfinance_news():
    """Fetches Arab Finance EGX-relevant stories from the news page and RSS feeds."""
    logger.debug("SentimentCrawler: fetching Arab Finance stories")
    all_stories = []

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        headers = {'User-Agent': UserAgent().random}
        try:
            response = await client.get(ARAB_FINANCE_NEWS_URL, headers=headers)
            if response.status_code == 200:
                all_stories.extend(_extract_arabfinance_stories(response.text))
        except Exception as e:
            logger.warning(f"SentimentCrawler: Arab Finance page fetch failed: {e}")

        for url in ARAB_FINANCE_RSS_URLS:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    all_stories.extend(
                        _extract_rss_stories(
                            response.text,
                            source="Arab Finance",
                            base_url=ARAB_FINANCE_NEWS_URL,
                        )
                    )
            except Exception as e:
                logger.warning(f"SentimentCrawler: Arab Finance RSS fetch failed for {url}: {e}")

    return _dedupe_news_stories(all_stories, limit=20)


async def async_fetch_amwal_alghad_news():
    """Fetches Amwal Al Ghad English EGX category stories."""
    logger.debug("SentimentCrawler: fetching Amwal Al Ghad EGX stories")
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            headers = {'User-Agent': UserAgent().random}
            response = await client.get(AMWAL_AL_GHAD_EGX_URL, headers=headers)
            if response.status_code != 200:
                return []
            return _extract_amwal_alghad_stories(response.text)
        except Exception as e:
            logger.warning(f"SentimentCrawler: Amwal Al Ghad fetch failed: {e}")
            return []


async def async_fetch_saudi_news():
    logger.debug("SentimentCrawler: fetching Saudi Argaam stories")
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            headers = {'User-Agent': UserAgent().random}
            response = await client.get(ARGAAM_SAUDI_URL, headers=headers)
            if response.status_code != 200: return []
            html = response.text
        except Exception as e:
            logger.warning(f"SentimentCrawler: Argaam fetch failed: {e}")
            return []
            
    soup = BeautifulSoup(html, 'html.parser')
    stories = []
    for tag in soup.find_all('a'):
        title = tag.get_text(strip=True)
        href = tag.get('href', "")
        if len(title) > 30 and ('/article/' in href or '/financial-reports/' in href or '/reports/' in href):
            link = "https://www.argaam.com" + href if not href.startswith('http') else href
            if any(s['title'] == title for s in stories): continue
            stories.append({'source': 'Argaam', 'title': title, 'link': link, 'summary': "Saudi Market Intelligence"})
    return stories[:10]

async def async_fetch_us_news():
    """Reuters actively blocks non-browser requests (401 Forbidden).
    Disabled to avoid noisy log spam. Returns [] until a Playwright
    stealth-based fallback is implemented."""
    logger.debug("SentimentCrawler: Reuters scrape disabled (401 blocked). Skipping.")
    return []


def _story_text(story: dict) -> str:
    return " ".join(
        str(story.get(key) or "")
        for key in ("source", "title", "Headline", "summary", "link")
    )


def is_saudi_market_story(story: dict) -> bool:
    """Returns True for Saudi/Tadawul market items that should not appear in the EGX feed."""
    if not isinstance(story, dict):
        return False

    source = str(story.get("source") or "").strip().lower()
    link = str(story.get("link") or "").lower()
    if source in SAUDI_NEWS_SOURCES or "argaam.com" in link:
        return True

    text_lower = _story_text(story).lower()
    return any(marker in text_lower for marker in SAUDI_MARKET_CONTEXT_MARKERS)


def filter_market_news_stories(stories: list) -> list:
    """Filters and normalizes stories for the EGX-facing Market News feed."""
    if not isinstance(stories, list):
        return []

    filtered = []
    seen_titles = set()
    for raw_story in stories:
        if not isinstance(raw_story, dict) or is_saudi_market_story(raw_story):
            continue

        story = dict(raw_story)
        title = str(story.get("title") or story.get("Headline") or "").strip()
        if not title or title in seen_titles:
            continue

        seen_titles.add(title)
        full_text = f"{title} {story.get('summary', '')}"
        story["tickers"] = extract_tickers(full_text)
        if "gossip_score" not in story:
            story["gossip_score"] = calculate_gossip_score(full_text)
        filtered.append(story)

    return filtered


def sanitize_market_news_payload(news_payload):
    """Removes non-EGX market items from fresh and cached news payloads."""
    if isinstance(news_payload, dict):
        payload = dict(news_payload)
        original_stories = payload.get("stories", [])
        payload["stories"] = filter_market_news_stories(original_stories)
        if len(payload["stories"]) != len(original_stories):
            payload["macro_correlation"] = get_macro_correlation_score(payload["stories"])
        elif "macro_correlation" not in payload:
            payload["macro_correlation"] = get_macro_correlation_score(payload["stories"])
        return payload
    if isinstance(news_payload, list):
        return filter_market_news_stories(news_payload)
    return news_payload


def _has_saudi_market_context(text_lower: str) -> bool:
    if any(marker in text_lower for marker in SAUDI_MARKET_CONTEXT_MARKERS):
        return not any(marker in text_lower for marker in EGX_CONTEXT_MARKERS)
    return False


def _clean_name_part(part: str) -> str:
    clean_part = re.sub(r"\s+", " ", str(part or "").strip().lower())
    for suffix in COMPANY_NAME_SUFFIXES:
        if clean_part.endswith(suffix):
            clean_part = clean_part[:-len(suffix)].strip()
    return clean_part


def _is_usable_name_part(clean_part: str) -> bool:
    if len(clean_part) < 4:
        return False

    tokens = [token for token in re.split(r"[^a-z0-9]+", clean_part) if token]
    if not tokens:
        return False
    if len(tokens) == 1 and tokens[0] in LOCATION_NAME_WORDS:
        return False
    if len(tokens) == 1 and tokens[0] in GENERIC_COMPANY_NAME_WORDS:
        return False
    if len(tokens[0]) == 1 and len(tokens) <= 2:
        return False
    return True


def _singularize_name_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 5:
        return f"{token[:-3]}y"
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    return token


def _name_part_candidates(clean_part: str) -> list[str]:
    candidates = {clean_part}
    tokens = [token for token in re.split(r"[^a-z0-9]+", clean_part) if token]
    compact_tokens = [token for token in tokens if token not in CONNECTOR_NAME_WORDS]
    if len(compact_tokens) >= 2:
        singular_tokens = [_singularize_name_token(token) for token in compact_tokens]
        candidates.add(" ".join(compact_tokens))
        candidates.add(" ".join(singular_tokens))
        if compact_tokens[-1] in TRAILING_BUSINESS_WORDS:
            candidates.add(" ".join(singular_tokens[:-1]))
    return sorted(candidates, key=len, reverse=True)


def extract_tickers(text):
    """Identifies EGX tickers mentioned in the news text."""
    mentioned_tickers = set()
    text = str(text or "")
    text_lower = text.lower()
    if _has_saudi_market_context(text_lower):
        return []

    all_tickers = MarketLists.get_market_list('ALL')
    for ticker in all_tickers:
        ticker_pattern = r'\b' + re.escape(ticker) + r'(?:\.CA)?\b'
        if re.search(ticker_pattern, text):
            mentioned_tickers.add(ticker)

    for ticker, aliases in NEWS_TICKER_ALIASES.items():
        for alias in aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                mentioned_tickers.add(ticker)
                break
            
    for ticker, name in MarketLists.NAME_MAP.items():
        if not name or len(name) < 4: continue
        parts = re.split(r' - |\(|\)', name)
        for part in parts:
            clean_part = _clean_name_part(part)
            if not _is_usable_name_part(clean_part):
                continue
            for candidate in _name_part_candidates(clean_part):
                if re.search(r'\b' + re.escape(candidate) + r'\b', text_lower):
                    mentioned_tickers.add(ticker); break
            if ticker in mentioned_tickers:
                break
    return sorted(mentioned_tickers)

def calculate_gossip_score(text):
    """Calculates a sentiment score -10 to +10 using weighted keywords (EN + AR)."""
    if not text:
        return 0
    score = 0
    text_lower = str(text).lower()
    
    # English keywords
    BULLS = {**BULLISH_KEYWORDS, "soar": 2, "skyrocket": 3, "undervalued": 2, "bullish": 2, "exceed": 1, "record": 1}
    BEARS = {**BEARISH_KEYWORDS, "plunge": 2, "tank": 3, "overvalued": 2, "bearish": 2, "miss": 1, "warn": 2}
    
    for word, weight in BULLS.items():
        if word in text_lower: score += weight
    for word, weight in BEARS.items():
        if word in text_lower: score -= weight
        
    # Arabic keywords
    try:
        for word, weight in ARABIC_BULLISH.items():
            if word in text_lower: score += weight
        for word, weight in ARABIC_BEARISH.items():
            if word in text_lower: score -= weight
    except NameError:
        pass # Handle potential definition order issues
        
    return max(-10, min(10, score))

def get_macro_correlation_score(processed_news):
    """
    Analyzes global/regional sentiment to derive a macro pressure score for EGX.
    Oil prices (Saudi) and Interest Rates (US) are key.
    """
    total_score = 0
    saudi_stories = [s for s in processed_news if s['source'] == 'Argaam']
    us_stories = [s for s in processed_news if f"source" in s and s['source'] == 'Reuters']
    
    # 1. US Macro Pressure (Interest Rates / Fed)
    fed_keywords = ["fed", "interest rate", "inflation", "cpi", "powell", "hike", "cut"]
    for s in us_stories:
        text = (s.get('title', '') + s.get('summary', '')).lower()
        if any(k in text for k in fed_keywords):
            # If sentiment is negative in US macro, it's usually bad for EM (EGX)
            total_score += s.get('gossip_score', 0) * 0.5
            
    # 2. Regional/Oil Pressure (Saudi)
    oil_keywords = ["oil", "aramco", "crude", "energy", "production"]
    for s in saudi_stories:
        text = (s.get('title', '') + s.get('summary', '')).lower()
        if any(k in text for k in oil_keywords):
            # Positive oil is mixed for Egypt (petrodollars vs import costs), 
            # but generally higher liquidity in region is good.
            total_score += s.get('gossip_score', 0) * 0.3
            
    return max(-10, min(10, total_score))

async def async_gather_gossip():
    """Async main function to fetch gossip."""
    from core import TimeUtils
    if TimeUtils.is_simulating():
        return [{"source": "System", "title": "News Archives Offline", "summary": "Live news feed is disabled during Simulation Mode (Time Travel).", "link": "#", "tickers": [], "gossip_score": 0}]

    import asyncio
    tasks = [
        async_fetch_enterprise_news(), 
        async_fetch_mubasher_news(),
        async_fetch_arabfinance_news(),
        async_fetch_amwal_alghad_news(),
        async_fetch_us_news()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    stories = []
    for res in results:
        if isinstance(res, list):
            stories.extend(res)
        elif isinstance(res, Exception):
            logger.error(f"SentimentCrawler: Async Scrape failed: {res}")
    
    processed_news = []
    seen_titles = set()
    for story in stories:
        if story['title'] in seen_titles: continue
        seen_titles.add(story['title'])
        full_text = f"{story['title']} {story['summary']}"
        story['tickers'] = extract_tickers(full_text)
        story['gossip_score'] = calculate_gossip_score(full_text)
        processed_news.append(story)
        
    processed_news = filter_market_news_stories(processed_news)

    # Calculate Macro Pressure
    macro_score = get_macro_correlation_score(processed_news)
    
    return {
        "stories": processed_news,
        "macro_correlation": macro_score,
        "timestamp": TimeUtils.now().isoformat()
    }


def gather_gossip():
    """Compatibility wrapper for legacy sync callers.

    Older paths expect SentimentCrawler to return just the processed story list,
    while newer async consumers use the richer payload from async_gather_gossip().
    """
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            payload = asyncio.run(async_gather_gossip())
        else:
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                payload = executor.submit(lambda: asyncio.run(async_gather_gossip())).result()
    except Exception as e:
        logger.warning(f"SentimentCrawler: sync gossip fetch failed: {e}")
        return []

    if isinstance(payload, dict):
        stories = payload.get("stories", [])
        return list(stories) if isinstance(stories, list) else []
    if isinstance(payload, list):
        return list(payload)
    return []

def run_gossip():
    """CLI Interface for the Gossip Engine."""
    print(Fore.MAGENTA + Style.BRIGHT + "\n🐿️  RATATOSKR (THE GOSSIP ENGINE)")
    print(Fore.MAGENTA + "=" * 50)
    news = gather_gossip()
    if not news:
        print(Fore.YELLOW + "  No current whispers in the wind...")
        return
    for item in news:
        score = item.get('gossip_score', 0)
        color = Fore.GREEN if score > 0 else Fore.RED if score < 0 else Fore.WHITE
        ticker_list = item.get('tickers', [])
        ticker_str = ", ".join(ticker_list) if ticker_list else "Market Wide"
        print(f"\n{Fore.CYAN}[{item['source']}] {Style.BRIGHT}{item['title']}")
        print(f"  {Fore.YELLOW}Tickers: {Fore.WHITE}{ticker_str}")
        print(f"  {Fore.YELLOW}Gossip Score: {color}{item['gossip_score']:+d}")
        print(f"  {Fore.WHITE}{item['summary']}...")
        print(f"  {Fore.BLUE}{item['link']}")
        print(Fore.MAGENTA + "-" * 30)

if __name__ == "__main__":
    run_gossip()
