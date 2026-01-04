"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { dictionaries, Locale, Dictionary } from "./dictionaries";

const STORAGE_KEY = "pharmainsight_locale";

interface I18nContextType {
    locale: Locale;
    setLocale: (locale: Locale) => void;
    t: Dictionary;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
    const [locale, setLocaleState] = useState<Locale>("en");
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const stored = localStorage.getItem(STORAGE_KEY) as Locale | null;
        if (stored && (stored === "en" || stored === "tr")) {
            setLocaleState(stored);
        }
    }, []);

    const setLocale = (newLocale: Locale) => {
        setLocaleState(newLocale);
        localStorage.setItem(STORAGE_KEY, newLocale);
    };

    if (!mounted) {
        return <>{children}</>;
    }

    return (
        <I18nContext.Provider value={{ locale, setLocale, t: dictionaries[locale] }}>
            {children}
        </I18nContext.Provider>
    );
}

export function useI18n() {
    const context = useContext(I18nContext);
    if (!context) {
        return {
            locale: "en" as Locale,
            setLocale: () => {},
            t: dictionaries.en,
        };
    }
    return context;
}

export { dictionaries, type Locale, type Dictionary };
