"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { getProject, getProjectRuns, createRun, getDocuments, Project, Run, DocumentItem, AnalysisMode } from "@/lib/api";
import { DocumentsTab } from "@/components/documents-tab";
import { QueryBuilder } from "@/components/query-builder";

type TabType = "runs" | "documents";

export default function ProjectDetailPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const params = useParams();
    const projectId = params.id as string;

    const [activeTab, setActiveTab] = useState<TabType>("runs");
    const [project, setProject] = useState<Project | null>(null);
    const [runs, setRuns] = useState<Run[]>([]);
    const [documents, setDocuments] = useState<DocumentItem[]>([]);
    const [loadingData, setLoadingData] = useState(true);
    const [error, setError] = useState("");

    // New run state
    const [queryText, setQueryText] = useState("");
    const [isQueryValid, setIsQueryValid] = useState(false);
    const [maxPapers, setMaxPapers] = useState(10);
    const [yearFrom, setYearFrom] = useState("");
    const [yearTo, setYearTo] = useState("");
    const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("synthesis");
    const [language, setLanguage] = useState<"en" | "tr">("en");
    const [creatingRun, setCreatingRun] = useState(false);

    useEffect(() => {
        if (!loading && !user) {
            router.push("/login");
        }
    }, [user, loading, router]);

    useEffect(() => {
        if (user && projectId) {
            fetchData();
        }
    }, [user, projectId]);

    const fetchData = async () => {
        try {
            const [projectData, runsData, docsData] = await Promise.all([
                getProject(projectId),
                getProjectRuns(projectId),
                getDocuments(projectId),
            ]);
            setProject(projectData);
            setRuns(runsData);
            setDocuments(docsData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch data");
        } finally {
            setLoadingData(false);
        }
    };

    const handleCreateRun = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!queryText.trim() || !isQueryValid) return;

        // Validate year range
        const yearFromNum = yearFrom ? parseInt(yearFrom) : undefined;
        const yearToNum = yearTo ? parseInt(yearTo) : undefined;
        if (yearFromNum && yearToNum && yearFromNum > yearToNum) {
            setError("Year From must be less than or equal to Year To");
            return;
        }

        setCreatingRun(true);
        try {
            const run = await createRun(projectId, {
                query_text: queryText,
                max_papers: maxPapers,
                year_from: yearFromNum,
                year_to: yearToNum,
                analysis_mode: analysisMode,
                language: language,
            });
            setQueryText("");
            setMaxPapers(10);
            setYearFrom("");
            setYearTo("");
            setAnalysisMode("synthesis");
            setLanguage("en");
            router.push(`/runs/${run.id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create run");
        } finally {
            setCreatingRun(false);
        }
    };

    const canCreateRun = user?.role === "ADMIN" || user?.role === "ANALYST";

    const getStatusColor = (status: string) => {
        switch (status) {
            case "DONE":
                return "bg-green-100 text-green-700";
            case "RUNNING":
                return "bg-blue-100 text-blue-700";
            case "QUEUED":
                return "bg-yellow-100 text-yellow-700";
            case "FAILED":
                return "bg-red-100 text-red-700";
            default:
                return "bg-gray-100 text-gray-700";
        }
    };

    const tabs: { id: TabType; label: string; count?: number }[] = [
        { id: "runs", label: "Analysis Runs", count: runs.length },
        { id: "documents", label: "Documents", count: documents.length },
    ];

    if (loading || !user) {
        return (
            <div className="container py-8">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 w-48 bg-muted rounded" />
                </div>
            </div>
        );
    }

    if (loadingData) {
        return (
            <div className="container py-8">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 w-48 bg-muted rounded" />
                    <div className="h-4 w-96 bg-muted rounded" />
                </div>
            </div>
        );
    }

    if (!project) {
        return (
            <div className="container py-8">
                <div className="text-center py-12">
                    <h2 className="text-xl font-semibold mb-2">Project not found</h2>
                    <Link href="/projects">
                        <Button>Back to Projects</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="container py-8">
            <div className="flex flex-col gap-6">
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Link href="/projects" className="hover:text-primary">
                        Projects
                    </Link>
                    <span>/</span>
                    <span>{project.name}</span>
                </div>

                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
                    {project.description && (
                        <p className="text-muted-foreground mt-2">{project.description}</p>
                    )}
                </div>

                {error && (
                    <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">
                        {error}
                    </div>
                )}

                {/* Tabs */}
                <div className="border-b">
                    <div className="flex gap-4">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`px-4 py-2 border-b-2 transition-colors ${activeTab === tab.id
                                    ? "border-primary text-primary font-medium"
                                    : "border-transparent text-muted-foreground hover:text-foreground"
                                    }`}
                            >
                                {tab.label}
                                {tab.count !== undefined && (
                                    <span className="ml-2 text-xs bg-muted px-2 py-0.5 rounded-full">
                                        {tab.count}
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Runs Tab */}
                {activeTab === "runs" && (
                    <>
                        {/* New Analysis Form */}
                        {canCreateRun && (
                            <div className="rounded-lg border bg-card p-6">
                                <h2 className="text-xl font-semibold mb-4">New Analysis</h2>
                                <form onSubmit={handleCreateRun} className="space-y-6">
                                    {/* Query Builder Component */}
                                    <QueryBuilder
                                        onQueryChange={(query, isValid) => {
                                            setQueryText(query);
                                            setIsQueryValid(isValid);
                                        }}
                                        disabled={creatingRun}
                                    />

                                    {/* Additional Settings */}
                                    <div className="border-t pt-4">
                                        <h3 className="text-sm font-medium mb-3 text-muted-foreground">Analysis Settings</h3>
                                        <div className="grid grid-cols-4 gap-4">
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium">Max Papers</label>
                                                <input
                                                    type="number"
                                                    value={maxPapers}
                                                    onChange={(e) => setMaxPapers(parseInt(e.target.value) || 10)}
                                                    min={1}
                                                    max={50}
                                                    disabled={creatingRun}
                                                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium">Year From</label>
                                                <input
                                                    type="number"
                                                    value={yearFrom}
                                                    onChange={(e) => setYearFrom(e.target.value)}
                                                    placeholder="e.g., 2020"
                                                    min={1900}
                                                    max={2026}
                                                    disabled={creatingRun}
                                                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium">Year To</label>
                                                <input
                                                    type="number"
                                                    value={yearTo}
                                                    onChange={(e) => setYearTo(e.target.value)}
                                                    placeholder="e.g., 2026"
                                                    min={1900}
                                                    max={2026}
                                                    disabled={creatingRun}
                                                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium">Language</label>
                                                <select
                                                    value={language}
                                                    onChange={(e) => setLanguage(e.target.value as "en" | "tr")}
                                                    disabled={creatingRun}
                                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                                >
                                                    <option value="en">English</option>
                                                    <option value="tr">Türkçe</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <Button
                                        type="submit"
                                        disabled={creatingRun || !isQueryValid}
                                        className="w-full"
                                    >
                                        {creatingRun ? "Starting Analysis..." : "Start Analysis"}
                                    </Button>
                                </form>
                            </div>
                        )}

                        {/* Runs List */}
                        <div className="rounded-lg border bg-card">
                            <div className="p-6 border-b">
                                <h2 className="text-xl font-semibold">Analysis Runs</h2>
                            </div>
                            {runs.length === 0 ? (
                                <div className="p-8 text-center text-muted-foreground">
                                    No analyses yet. Start your first analysis above.
                                </div>
                            ) : (
                                <div className="divide-y">
                                    {runs.map((run) => (
                                        <Link
                                            key={run.id}
                                            href={`/runs/${run.id}`}
                                            className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
                                        >
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium truncate">{run.query_text}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    {new Date(run.created_at).toLocaleString()}
                                                </p>
                                            </div>
                                            <span
                                                className={`ml-4 px-2 py-1 rounded text-xs font-medium ${getStatusColor(run.status)}`}
                                            >
                                                {run.status}
                                            </span>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* Documents Tab */}
                {activeTab === "documents" && (
                    <DocumentsTab
                        projectId={projectId}
                        documents={documents}
                        onRefresh={fetchData}
                    />
                )}
            </div>
        </div>
    );
}
