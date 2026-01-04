"use client";

import { Bell, HelpCircle, Search, Languages } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { useI18n } from "@/lib/i18n";

export function Topbar() {
    const { locale, setLocale, t } = useI18n();

    const toggleLocale = () => {
        setLocale(locale === "en" ? "tr" : "en");
    };

    return (
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background px-6">
            {/* Search */}
            <div className="flex-1 max-w-xl">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                        type="search"
                        placeholder={t.topbar.searchPlaceholder}
                        className="pl-10 bg-secondary border-none"
                    />
                </div>
            </div>

            {/* Right side actions */}
            <div className="flex items-center gap-2">
                {/* Language Toggle */}
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleLocale}
                    className="h-9 px-3 gap-1.5"
                >
                    <Languages className="h-4 w-4" />
                    <span className="text-xs font-medium">{locale.toUpperCase()}</span>
                </Button>
                <ThemeToggle />
                <Button variant="ghost" size="icon" className="h-9 w-9">
                    <Bell className="h-4 w-4" />
                    <span className="sr-only">{t.topbar.notifications}</span>
                </Button>
                <Button variant="ghost" size="icon" className="h-9 w-9">
                    <HelpCircle className="h-4 w-4" />
                    <span className="sr-only">{t.topbar.help}</span>
                </Button>
            </div>
        </header>
    );
}
