"use client";

import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

interface AppShellProps {
    children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
    return (
        <div className="min-h-screen bg-background">
            <Sidebar />
            <div className="ml-64">
                <Topbar />
                <main className="p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}
