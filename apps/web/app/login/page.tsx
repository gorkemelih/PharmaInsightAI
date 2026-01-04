"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            await login(email, password);
            router.push("/dashboard");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center">
            <div className="w-full max-w-md p-8 space-y-8">
                <div className="text-center">
                    <h1 className="text-3xl font-bold">Sign In</h1>
                    <p className="text-muted-foreground mt-2">
                        Enter your credentials to access the platform
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {error && (
                        <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">
                            {error}
                        </div>
                    )}

                    <div className="space-y-2">
                        <label
                            htmlFor="email"
                            className="text-sm font-medium leading-none"
                        >
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="admin@pharmainsight.io"
                            required
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                        />
                    </div>

                    <div className="space-y-2">
                        <label
                            htmlFor="password"
                            className="text-sm font-medium leading-none"
                        >
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                        />
                    </div>

                    <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? "Signing in..." : "Sign In"}
                    </Button>
                </form>

                <div className="text-center text-sm text-muted-foreground">
                    <p>Default credentials:</p>
                    <p className="font-mono text-xs mt-1">
                        admin@pharmainsight.io / changeme123
                    </p>
                </div>
            </div>
        </div>
    );
}
