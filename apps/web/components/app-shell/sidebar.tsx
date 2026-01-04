"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    FolderOpen,
    FileText,
    Users,
    Settings,
    FlaskConical,
} from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/components/auth-provider";

export function Sidebar() {
    const pathname = usePathname();
    const { t } = useI18n();
    const { user } = useAuth();

    const navItems = [
        { href: "/dashboard", labelKey: "overview" as const, icon: <LayoutDashboard className="h-5 w-5" /> },
        { href: "/projects", labelKey: "projects" as const, icon: <FolderOpen className="h-5 w-5" /> },
        { href: "/users", labelKey: "users" as const, icon: <Users className="h-5 w-5" /> },
        { href: "/settings", labelKey: "settings" as const, icon: <Settings className="h-5 w-5" /> },
    ];

    return (
        <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-primary dark:bg-sidebar-background">
            <div className="flex h-full flex-col">
                {/* Brand */}
                <div className="flex h-16 items-center gap-3 px-6 border-b border-white/10">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/20">
                        <FlaskConical className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex flex-col">
                        <span className="font-semibold text-white">PharmaInsightAI</span>
                        <span className="text-xs text-white/70">Enterprise Admin</span>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-1 px-3 py-4">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`sidebar-item ${isActive ? "sidebar-item-active" : "sidebar-item-inactive"}`}
                            >
                                {item.icon}
                                <span>{t.nav[item.labelKey]}</span>
                            </Link>
                        );
                    })}
                </nav>

                {/* User section at bottom */}
                <div className="border-t border-white/10 p-4">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center">
                            <span className="text-sm font-medium text-white">
                                {user?.email?.slice(0, 2).toUpperCase() || "AD"}
                            </span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm font-medium text-white">
                                {user?.role || "User"}
                            </span>
                            <span className="text-xs text-white/70 truncate max-w-[140px]">
                                {user?.email || "user@example.com"}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    );
}
