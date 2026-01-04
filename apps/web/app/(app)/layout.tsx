"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { AppShell } from "@/components/app-shell";

export default function AuthenticatedLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && !user) {
            router.push("/login");
        }
    }, [user, loading, router]);

    // Show loading state while checking auth
    if (loading) {
        return (
            <AppShell>
                <div className="flex items-center justify-center min-h-[50vh]">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                </div>
            </AppShell>
        );
    }

    // Redirect handled in useEffect, but prevent flash
    if (!user) {
        return null;
    }

    return <AppShell>{children}</AppShell>;
}
