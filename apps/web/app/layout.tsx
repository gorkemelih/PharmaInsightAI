import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { I18nProvider } from "@/lib/i18n/index";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "PharmaInsightAI",
    description: "B2B pharmaceutical insights platform powered by AI",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={inter.className}>
                <ThemeProvider>
                    <I18nProvider>
                        <AuthProvider>
                            {children}
                        </AuthProvider>
                    </I18nProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}
