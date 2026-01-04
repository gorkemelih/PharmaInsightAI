import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-3.5rem)]">
            <div className="container flex flex-col items-center justify-center gap-8 px-4 py-16">
                <div className="text-center space-y-4">
                    <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
                        <span className="bg-gradient-to-r from-primary via-blue-600 to-purple-600 bg-clip-text text-transparent">
                            PharmaInsightAI
                        </span>
                    </h1>
                    <p className="mx-auto max-w-[700px] text-lg text-muted-foreground md:text-xl">
                        B2B pharmaceutical insights platform powered by AI. Analyze
                        literature, extract insights, and accelerate your research.
                    </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-4">
                    <Link href="/dashboard">
                        <Button size="lg" className="text-lg px-8">
                            Go to Dashboard
                        </Button>
                    </Link>
                    <Button size="lg" variant="outline" className="text-lg px-8">
                        Learn More
                    </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16 max-w-5xl">
                    <div className="flex flex-col items-center text-center p-6 rounded-lg border bg-card">
                        <div className="p-3 rounded-full bg-primary/10 mb-4">
                            <svg
                                className="w-6 h-6 text-primary"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold mb-2">Literature Analysis</h3>
                        <p className="text-sm text-muted-foreground">
                            Access PubMed, Europe PMC, Crossref, OpenAlex, and arXiv for
                            comprehensive research.
                        </p>
                    </div>

                    <div className="flex flex-col items-center text-center p-6 rounded-lg border bg-card">
                        <div className="p-3 rounded-full bg-primary/10 mb-4">
                            <svg
                                className="w-6 h-6 text-primary"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M13 10V3L4 14h7v7l9-11h-7z"
                                />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold mb-2">AI-Powered Insights</h3>
                        <p className="text-sm text-muted-foreground">
                            Leverage Gemini AI to extract meaningful insights from
                            pharmaceutical literature.
                        </p>
                    </div>

                    <div className="flex flex-col items-center text-center p-6 rounded-lg border bg-card">
                        <div className="p-3 rounded-full bg-primary/10 mb-4">
                            <svg
                                className="w-6 h-6 text-primary"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                                />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold mb-2">Executive Reports</h3>
                        <p className="text-sm text-muted-foreground">
                            Generate professional reports and summaries for stakeholders.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
