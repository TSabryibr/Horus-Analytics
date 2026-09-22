from core.analyzers import SentimentCrawler
import asyncio


def test_analyze_mortal_whispers_greed_regime():
    texts = [
        "Rocket breakout buy signal, green up move",
        "Profit moon buy setup",
        "Buy buy breakout up",
    ]
    result = SentimentCrawler.analyze_mortal_whispers(texts)
    assert result["score"] > 70
    assert result["regime"] == "BULLISH EXUBERANCE"
    assert result["bull_count"] > result["bear_count"]


def test_analyze_mortal_whispers_neutral_when_no_hits():
    texts = ["Nothing actionable here", "Sideways talk with no trigger words"]
    result = SentimentCrawler.analyze_mortal_whispers(texts)
    assert result["score"] == 50.0
    assert result["regime"] == "NEUTRAL"
    assert result["total_hits"] == 0


def test_analyze_mortal_whispers_blood_paralysis_regime():
    texts = [
        "Crash dump red blood halas",
        "Sell sell down loss",
    ]
    result = SentimentCrawler.analyze_mortal_whispers(texts)
    assert result["score"] < 30
    assert result["regime"] == "BEARISH PANIC"
    assert result["bear_count"] > result["bull_count"]


def test_analyze_mortal_whispers_word_boundary_avoids_false_up_match():
    texts = ["startup remains stable", "upside remains theoretical", "profitability was unchanged"]
    result = SentimentCrawler.analyze_mortal_whispers(texts)
    assert result["score"] == 50.0
    assert result["total_hits"] == 0


def test_get_bifrost_sentiment_uses_headline_fallback():
    news_items = [
        {"Headline": "Rocket breakout buy", "summary": "Green close"},
        {"title": "Crash sell pressure", "summary": "red day"},
    ]
    result = SentimentCrawler.get_bifrost_sentiment(news_items)
    assert "score" in result
    assert "regime" in result
    assert result["sample_size"] == 2


def test_extract_tickers_does_not_map_saudi_article_to_acap():
    text = "AlJazira Capital reviews ADES Holding Q1 results, sets rating, TP Saudi Market Intelligence"

    assert "ACAP" not in SentimentCrawler.extract_tickers(text)


def test_extract_tickers_keeps_explicit_egx_symbols():
    text = "Elsewedy Electric (SWDY.CA) and Housing and Development Bank (HDBK.CA) lead EGX trading."

    tickers = SentimentCrawler.extract_tickers(text)

    assert "SWDY" in tickers
    assert "HDBK" in tickers


def test_extract_tickers_maps_alexandria_container_without_irax_false_positive():
    text = "Alexandria Container's net profits jump to EGP 1.9bn in Q1-26"

    tickers = SentimentCrawler.extract_tickers(text)

    assert "ALCN" in tickers
    assert "IRAX" not in tickers


def test_extract_tickers_avoids_title_case_symbol_false_positive():
    text = "Certificates Of Odin Egyptian Equity Investment Fund-KASAB (KASABF.CA) - Decisions"

    tickers = SentimentCrawler.extract_tickers(text)

    assert "KASABF" in tickers
    assert "ODIN" not in tickers


def test_extract_arabfinance_stories_from_news_links():
    assert hasattr(SentimentCrawler, "_extract_arabfinance_stories")
    html = """
        <a href="/en/news/newdetails/egx-banks-lead-market-gains">
            EGX banks lead market gains in active trading session
        </a>
    """

    stories = SentimentCrawler._extract_arabfinance_stories(html)

    assert stories == [
        {
            "source": "Arab Finance",
            "title": "EGX banks lead market gains in active trading session",
            "link": "https://www.arabfinance.com/en/news/newdetails/egx-banks-lead-market-gains",
            "summary": "",
        }
    ]


def test_extract_amwal_alghad_stories_from_egx_category():
    assert hasattr(SentimentCrawler, "_extract_amwal_alghad_stories")
    html = """
        <a href="https://en.amwalalghad.com/egypt-denies-plans-for-10000-pound-banknote/">
            Egypt denies plans for 10,000 pound banknote
        </a>
        <span>Browsing Category</span>
        <a href="https://en.amwalalghad.com/egx-closes-higher-as-banks-lead-session/">
            EGX closes higher as banks lead session
        </a>
        <a href="/category/stocks/c1-egx/">EGX archive</a>
    """

    stories = SentimentCrawler._extract_amwal_alghad_stories(html)

    assert stories == [
        {
            "source": "Amwal Al Ghad",
            "title": "EGX closes higher as banks lead session",
            "link": "https://en.amwalalghad.com/egx-closes-higher-as-banks-lead-session/",
            "summary": "",
        }
    ]


def test_async_gather_gossip_excludes_saudi_source(monkeypatch):
    async def _enterprise():
        return [
            {
                "source": "Enterprise",
                "title": "EGX closes higher as banks lead the session",
                "summary": "Egyptian equities improved.",
                "link": "https://enterpriseam.com/egypt/example",
            }
        ]

    async def _mubasher():
        return []

    async def _saudi():
        return [
            {
                "source": "Argaam",
                "title": "AlJazira Capital reviews ADES Holding Q1 results, sets rating, TP",
                "summary": "Saudi Market Intelligence",
                "link": "https://www.argaam.com/en/article/example",
            }
        ]

    async def _us():
        return []

    async def _arabfinance():
        return []

    async def _amwal_alghad():
        return []

    monkeypatch.setattr(SentimentCrawler, "async_fetch_enterprise_news", _enterprise)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_mubasher_news", _mubasher)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_arabfinance_news", _arabfinance, raising=False)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_amwal_alghad_news", _amwal_alghad, raising=False)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_saudi_news", _saudi)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_us_news", _us)

    payload = asyncio.run(SentimentCrawler.async_gather_gossip())

    assert all(story["source"] != "Argaam" for story in payload["stories"])
    assert all("argaam.com" not in story.get("link", "").lower() for story in payload["stories"])


def test_async_gather_gossip_includes_new_egx_sources(monkeypatch):
    async def _empty():
        return []

    async def _arabfinance():
        return [
            {
                "source": "Arab Finance",
                "title": "EGX-listed banks lead market gains in active trading session",
                "summary": "Egyptian equities advanced.",
                "link": "https://www.arabfinance.com/en/news/newdetails/egx-banks-lead-market-gains",
            }
        ]

    async def _amwal_alghad():
        return [
            {
                "source": "Amwal Al Ghad",
                "title": "EGX closes higher as banks lead session",
                "summary": "Egypt stock market closes in green area.",
                "link": "https://en.amwalalghad.com/egx-closes-higher-as-banks-lead-session/",
            }
        ]

    monkeypatch.setattr(SentimentCrawler, "async_fetch_enterprise_news", _empty)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_mubasher_news", _empty)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_arabfinance_news", _arabfinance, raising=False)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_amwal_alghad_news", _amwal_alghad, raising=False)
    monkeypatch.setattr(SentimentCrawler, "async_fetch_us_news", _empty)

    payload = asyncio.run(SentimentCrawler.async_gather_gossip())

    sources = {story["source"] for story in payload["stories"]}
    assert {"Arab Finance", "Amwal Al Ghad"} <= sources
