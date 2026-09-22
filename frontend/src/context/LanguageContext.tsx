"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';

type Language = 'en' | 'ar';

interface LanguageContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: (key: string) => string;
    isRtl: boolean;
}

const translations = {
    en: {
        "nav.dashboard": "Terminal Dashboard",
        "nav.telegram": "Telegram Rail",
        "nav.scanner": "Market Scanner",
        "nav.analytics": "Market Analytics",
        "nav.analysis_report": "Analysis Report",
        "nav.live": "Live Monitor",
        "nav.signals": "Live Signals",
        "nav.strategy": "Strategy Core",
        "nav.optimization": "Strategy Lab",
        "nav.news": "Alpha News",
        "nav.executionQuality": "Execution Quality",
        "nav.audit_trail": "Performance Audit",
        "nav.oracle": "AI Oracle",
        "nav.whales": "Whale Tracker",
        "nav.traps": "Trap Detector",
        "nav.arbitrage": "Arbitrage Hub",
        "nav.seasonality": "Seasonality",
        "nav.sectors": "Sector Analysis",
        "nav.simulation": "Simulation Room",
        "nav.status": "System Status",
        "nav.portfolio": "Portfolio",
        "nav.subscribers": "Subscribers",
        "nav.settings": "Settings",
        "status.ready": "System Ready",
        "status.syncing": "Syncing Data",
        "status.error": "System Error",
        "audit.title": "System Audit Hub",
        "audit.event_type": "Event Type",
        "audit.severity": "Severity",
        "audit.message": "Message",
        "audit.timestamp": "Timestamp",
        "settings.webhooks": "Webhook Configuration",
        "settings.language": "Preferred Language",
        "common.save": "Save Changes",
        "common.test": "Test Connection"
    },
    ar: {
        "nav.telegram": "قناة تيليجرام",
        "nav.subscribers": "المشتركين",
        "nav.dashboard": "لوحة التحكم الرئيسية",
        "nav.scanner": "الماسح الضوئي",
        "nav.analytics": "تحليلات السوق",
        "nav.analysis_report": "تقرير التحليل",
        "nav.live": "المراقبة الحية",
        "nav.signals": "الإشارات الحالية",
        "nav.strategy": "نواة الاستراتيجية",
        "nav.optimization": "مختبر الاستراتيجيات",
        "nav.news": "أخبار ألفا",
        "nav.executionQuality": "جودة التنفيذ",
        "nav.audit_trail": "تدقيق الأداء",
        "nav.oracle": "أوراكل الذكاء الاصطناعي",
        "nav.whales": "تعقب الحيتان",
        "nav.traps": "كاشف المصائد",
        "nav.arbitrage": "مركز التحكيم",
        "nav.seasonality": "الموسمية",
        "nav.sectors": "تحليل القطاعات",
        "nav.simulation": "غرفة المحاكاة",
        "nav.status": "حالة النظام",
        "nav.portfolio": "المحفظة الاستثمارية",
        "nav.settings": "الإعدادات",
        "status.ready": "النظام جاهز",
        "status.syncing": "جارٍ المزامنة",
        "status.error": "خطأ في النظام",
        "audit.title": "مركز تدقيق النظام",
        "audit.event_type": "نوع الحدث",
        "audit.severity": "الخطورة",
        "audit.message": "الرسالة",
        "audit.timestamp": "الوقت",
        "settings.webhooks": "إعدادات الربط (Webhook)",
        "settings.language": "اللغة المفضلة",
        "common.save": "حفظ التغييرات",
        "common.test": "اختبار الاتصال"
    }
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [language, setLanguageState] = useState<Language>('en');

    useEffect(() => {
        const saved = localStorage.getItem('horus_lang') as Language;
        if (saved && (saved === 'en' || saved === 'ar')) {
            setLanguageState(saved);
        }
    }, []);

    const setLanguage = (lang: Language) => {
        setLanguageState(lang);
        localStorage.setItem('horus_lang', lang);
        document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
        document.documentElement.lang = lang;
    };

    const t = (key: string) => {
        return translations[language][key as keyof typeof translations['en']] || key;
    };

    const isRtl = language === 'ar';

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t, isRtl }}>
            <div dir={isRtl ? 'rtl' : 'ltr'} className={isRtl ? 'font-arabic' : ''}>
                {children}
            </div>
        </LanguageContext.Provider>
    );
};

export const useLanguage = () => {
    const context = useContext(LanguageContext);
    if (context === undefined) {
        throw new Error('useLanguage must be used within a LanguageProvider');
    }
    return context;
};
