"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Download, Loader2, Sparkles } from "lucide-react";
import {
    getRun,
    getProject,
    getRunPapers,
    getRunSummaries,
    getPaperSummary,
    getEvidenceTable,
    getSummaryWithReferences,
    getEvidenceDetail,
    downloadRunReport,
    generatePaperSummary,
    Run,
    Project,
    Paper,
    SummaryStatus,
    Summary,
    EvidenceRow,
    SummaryWithReferencesResponse,
    FormattedReference,
    EvidenceDetail,
    OnDemandSummary,
} from "@/lib/api";

type TabType = "papers" | "summary" | "claims";

export default function RunDetailPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const params = useParams();
    const runId = params.id as string;

    const [activeTab, setActiveTab] = useState<TabType>("papers");
    const [run, setRun] = useState<Run | null>(null);
    const [project, setProject] = useState<Project | null>(null);
    const [papers, setPapers] = useState<Paper[]>([]);
    const [summaries, setSummaries] = useState<SummaryStatus[]>([]);
    const [evidenceTable, setEvidenceTable] = useState<EvidenceRow[]>([]);
    const [summaryWithRefs, setSummaryWithRefs] = useState<SummaryWithReferencesResponse | null>(null);
    const [selectedSummary, setSelectedSummary] = useState<Summary | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [loadingData, setLoadingData] = useState(true);
    const [loadingPapers, setLoadingPapers] = useState(false);
    const [loadingSummary, setLoadingSummary] = useState(false);
    const [error, setError] = useState("");

    // Evidence drawer state
    const [showEvidenceDrawer, setShowEvidenceDrawer] = useState(false);
    const [evidenceDetail, setEvidenceDetail] = useState<EvidenceDetail | null>(null);
    const [loadingEvidence, setLoadingEvidence] = useState(false);

    // PDF download state
    const [downloadingPdf, setDownloadingPdf] = useState(false);

    // On-demand summary state
    const [generatingSummary, setGeneratingSummary] = useState<string | null>(null);
    const [onDemandSummary, setOnDemandSummary] = useState<OnDemandSummary | null>(null);
    const [showOnDemandModal, setShowOnDemandModal] = useState(false);

    const handleDownloadPdf = async () => {
        setDownloadingPdf(true);
        try {
            await downloadRunReport(runId);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to download PDF");
        } finally {
            setDownloadingPdf(false);
        }
    };

    const handleGenerateSummary = async (paperId: string) => {
        setGeneratingSummary(paperId);
        setError("");
        try {
            const summary = await generatePaperSummary(runId, paperId);
            setOnDemandSummary(summary);
            setShowOnDemandModal(true);
            // Refresh summaries list to update status
            fetchSummaries();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to generate summary");
        } finally {
            setGeneratingSummary(null);
        }
    };

    useEffect(() => {
        if (!loading && !user) {
            router.push("/login");
        }
    }, [user, loading, router]);

    useEffect(() => {
        if (user && runId) {
            fetchData();
        }
    }, [user, runId]);

    useEffect(() => {
        if (run && (run.status === "QUEUED" || run.status === "RUNNING")) {
            const interval = setInterval(fetchData, 2000);
            return () => clearInterval(interval);
        }
    }, [run?.status]);

    useEffect(() => {
        if (run?.status === "DONE" && papers.length === 0 && !loadingPapers) {
            fetchPapers();
            fetchSummaries();
            fetchEvidenceTable();
            fetchSummaryWithRefs();
        }
    }, [run?.status]);

    useEffect(() => {
        if (run?.status === "DONE" && summaries.length > 0) {
            const processingCount = summaries.filter(
                (s) => s.status === "QUEUED" || s.status === "RUNNING"
            ).length;
            if (processingCount > 0) {
                const interval = setInterval(() => {
                    fetchSummaries();
                    fetchEvidenceTable();
                    fetchSummaryWithRefs();
                }, 3000);
                return () => clearInterval(interval);
            }
        }
    }, [run?.status, summaries]);

    useEffect(() => {
        if (summaryWithRefs && (summaryWithRefs.status === "QUEUED" || summaryWithRefs.status === "RUNNING")) {
            const interval = setInterval(fetchSummaryWithRefs, 3000);
            return () => clearInterval(interval);
        }
    }, [summaryWithRefs?.status]);

    const fetchData = async () => {
        try {
            const runData = await getRun(runId);
            setRun(runData);
            if (!project) {
                const projectData = await getProject(runData.project_id);
                setProject(projectData);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch data");
        } finally {
            setLoadingData(false);
        }
    };

    const fetchPapers = async () => {
        setLoadingPapers(true);
        try {
            const papersData = await getRunPapers(runId);
            setPapers(papersData);
        } catch (err) {
            console.error("Failed to fetch papers:", err);
        } finally {
            setLoadingPapers(false);
        }
    };

    const fetchSummaries = async () => {
        try {
            const summariesData = await getRunSummaries(runId);
            setSummaries(summariesData);
        } catch (err) {
            console.error("Failed to fetch summaries:", err);
        }
    };

    const fetchEvidenceTable = async () => {
        try {
            const data = await getEvidenceTable(runId);
            setEvidenceTable(data);
        } catch (err) {
            console.error("Failed to fetch evidence table:", err);
        }
    };

    const fetchSummaryWithRefs = async () => {
        try {
            const data = await getSummaryWithReferences(runId);
            setSummaryWithRefs(data);
        } catch (err) {
            console.error("Failed to fetch summary with references:", err);
        }
    };

    const handleViewSummary = async (paperId: string) => {
        setLoadingSummary(true);
        setShowModal(true);
        try {
            const summary = await getPaperSummary(paperId, runId);
            setSelectedSummary(summary);
        } catch (err) {
            console.error("Failed to fetch summary:", err);
        } finally {
            setLoadingSummary(false);
        }
    };

    const handleCitationClick = async (ref: FormattedReference) => {
        setLoadingEvidence(true);
        setShowEvidenceDrawer(true);
        setEvidenceDetail(null);
        try {
            const detail = await getEvidenceDetail(runId, ref.paper_id);
            setEvidenceDetail(detail);
        } catch (err) {
            console.error("Failed to fetch evidence:", err);
        } finally {
            setLoadingEvidence(false);
        }
    };

    const getSummaryStatus = (paperId: string) => {
        return summaries.find((s) => s.paper_id === paperId);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case "DONE": return "bg-green-100 text-green-700 border-green-200";
            case "RUNNING": return "bg-blue-100 text-blue-700 border-blue-200";
            case "QUEUED": return "bg-yellow-100 text-yellow-700 border-yellow-200";
            case "FAILED": return "bg-red-100 text-red-700 border-red-200";
            default: return "bg-gray-100 text-gray-700 border-gray-200";
        }
    };

    const getStatusBadge = (status: string) => {
        const colors: Record<string, string> = {
            DONE: "bg-green-100 text-green-700",
            RUNNING: "bg-blue-100 text-blue-700",
            QUEUED: "bg-yellow-100 text-yellow-700",
            FAILED: "bg-red-100 text-red-700",
            PENDING: "bg-gray-100 text-gray-700",
        };
        return colors[status] || "bg-gray-100 text-gray-700";
    };

    // Citation chip component
    const CitationChip = ({ indices, references }: { indices: { index: number }[]; references: FormattedReference[] }) => {
        if (indices.length === 0) return null;
        return (
            <span className="inline-flex gap-1 ml-1">
                {indices.map((cit) => {
                    const ref = references.find(r => r.index === cit.index);
                    return (
                        <button
                            key={cit.index}
                            onClick={() => ref && handleCitationClick(ref)}
                            className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors cursor-pointer"
                            title={ref?.formatted}
                        >
                            [{cit.index}]
                        </button>
                    );
                })}
            </span>
        );
    };

    if (loading || !user || loadingData) {
        return (
            <div className="container py-8">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 w-48 bg-muted rounded" />
                    <div className="h-32 w-full bg-muted rounded" />
                </div>
            </div>
        );
    }

    if (!run) {
        return (
            <div className="container py-8">
                <div className="text-center py-12">
                    <h2 className="text-xl font-semibold mb-2">Run not found</h2>
                    <Link href="/projects">
                        <Button>Back to Projects</Button>
                    </Link>
                </div>
            </div>
        );
    }

    const processingCount = summaries.filter(
        (s) => s.status === "QUEUED" || s.status === "RUNNING"
    ).length;
    const doneCount = summaries.filter((s) => s.status === "DONE").length;

    const tabs: { id: TabType; label: string; count?: number }[] = [
        { id: "papers", label: "Papers", count: papers.length },
        { id: "summary", label: "Run Summary" },
        { id: "claims", label: "Claims Draft" },
    ];

    return (
        <div className="container py-8">
            <div className="flex flex-col gap-6">
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Link href="/projects" className="hover:text-primary">Projects</Link>
                    <span>/</span>
                    {project && (
                        <>
                            <Link href={`/projects/${project.id}`} className="hover:text-primary">{project.name}</Link>
                            <span>/</span>
                        </>
                    )}
                    <span>Run</span>
                </div>

                {/* Status Card */}
                <div className={`rounded-lg border p-6 ${getStatusColor(run.status)}`}>
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold">{run.status}</h2>
                            <p className="text-sm opacity-80">
                                {run.status === "QUEUED" && "Waiting in queue..."}
                                {run.status === "RUNNING" && "Searching literature databases..."}
                                {run.status === "DONE" && `Found ${papers.length} papers`}
                                {run.status === "FAILED" && "Analysis failed"}
                            </p>
                        </div>
                        {run.status === "DONE" && (
                            <Button
                                onClick={handleDownloadPdf}
                                disabled={downloadingPdf}
                                variant="outline"
                                className="bg-white/90 hover:bg-white"
                            >
                                <Download className={`h-4 w-4 mr-2 ${downloadingPdf ? "animate-pulse" : ""}`} />
                                {downloadingPdf ? "Generating..." : "Download PDF"}
                            </Button>
                        )}
                    </div>
                </div>

                {error && (
                    <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">{error}</div>
                )}

                {/* Query */}
                <div className="rounded-lg border bg-card p-6">
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Research Query</h3>
                    <p className="text-lg">{run.query_text}</p>
                </div>

                {/* Progress */}
                {run.status === "DONE" && summaries.length > 0 && (
                    <div className="rounded-lg border bg-card p-6">
                        <h3 className="text-lg font-semibold mb-2">AI Analysis Progress</h3>
                        <div className="flex items-center gap-4">
                            <div className="flex-1 bg-muted rounded-full h-2">
                                <div className="bg-primary h-2 rounded-full transition-all" style={{ width: `${(doneCount / summaries.length) * 100}%` }} />
                            </div>
                            <span className="text-sm text-muted-foreground">{doneCount}/{summaries.length} analyzed</span>
                            {processingCount > 0 && <span className="text-sm text-blue-600 animate-pulse">Processing...</span>}
                        </div>
                        {summaryWithRefs && (
                            <div className="mt-2 text-sm">
                                Run Summary: <span className={`px-2 py-0.5 rounded ${getStatusBadge(summaryWithRefs.status)}`}>{summaryWithRefs.status}</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Tabs */}
                {run.status === "DONE" && (
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
                                    {tab.count !== undefined && <span className="ml-1 text-xs">({tab.count})</span>}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Papers Tab */}
                {run.status === "DONE" && activeTab === "papers" && (
                    <div className="rounded-lg border bg-card">
                        <div className="p-6 border-b">
                            <h3 className="text-lg font-semibold">Papers Found ({papers.length})</h3>
                        </div>
                        {loadingPapers ? (
                            <div className="p-8 text-center text-muted-foreground">Loading...</div>
                        ) : papers.length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">No papers found.</div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="border-b bg-muted/50">
                                        <tr>
                                            <th className="px-4 py-3 text-left font-medium">Title</th>
                                            <th className="px-4 py-3 text-left font-medium w-20">Year</th>
                                            <th className="px-4 py-3 text-left font-medium w-24">AI Status</th>
                                            <th className="px-4 py-3 text-right font-medium w-32">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {papers.map((paper) => {
                                            const summaryStatus = getSummaryStatus(paper.id);
                                            return (
                                                <tr key={paper.id} className="border-b last:border-0 hover:bg-muted/30">
                                                    <td className="px-4 py-3">
                                                        <div className="font-medium line-clamp-2">{paper.title}</div>
                                                    </td>
                                                    <td className="px-4 py-3 text-muted-foreground">{paper.year || "-"}</td>
                                                    <td className="px-4 py-3">
                                                        {summaryStatus && (
                                                            <span className={`px-2 py-0.5 rounded text-xs ${getStatusBadge(summaryStatus.status)}`}>
                                                                {summaryStatus.status}
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className="px-4 py-3 text-right">
                                                        {run.analysis_mode === "per_paper" ? (
                                                            summaryStatus?.status === "DONE" ? (
                                                                <button
                                                                    onClick={() => handleViewSummary(paper.id)}
                                                                    className="text-primary hover:underline text-xs"
                                                                >
                                                                    View Summary
                                                                </button>
                                                            ) : (
                                                                <button
                                                                    onClick={() => handleGenerateSummary(paper.id)}
                                                                    disabled={generatingSummary === paper.id}
                                                                    className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 disabled:opacity-50"
                                                                >
                                                                    {generatingSummary === paper.id ? (
                                                                        <>
                                                                            <Loader2 className="h-3 w-3 animate-spin" />
                                                                            Generating...
                                                                        </>
                                                                    ) : (
                                                                        <>
                                                                            <Sparkles className="h-3 w-3" />
                                                                            Generate Summary
                                                                        </>
                                                                    )}
                                                                </button>
                                                            )
                                                        ) : (
                                                            paper.doi ? (
                                                                <a
                                                                    href={`https://doi.org/${paper.doi}`}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="text-primary hover:underline text-xs"
                                                                >
                                                                    DOI →
                                                                </a>
                                                            ) : paper.pmid ? (
                                                                <a
                                                                    href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}`}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="text-primary hover:underline text-xs"
                                                                >
                                                                    PubMed →
                                                                </a>
                                                            ) : (
                                                                <span className="text-muted-foreground">—</span>
                                                            )
                                                        )}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}

                {/* Evidence Table removed - data shown in Papers tab */}

                {/* Summary Tab with References */}
                {run.status === "DONE" && activeTab === "summary" && (
                    <div className="rounded-lg border bg-card p-6">
                        <h3 className="text-lg font-semibold mb-4">
                            Run Summary
                            {summaryWithRefs && (
                                <span className={`ml-2 px-2 py-0.5 rounded text-xs ${getStatusBadge(summaryWithRefs.status)}`}>
                                    {summaryWithRefs.status}
                                </span>
                            )}
                        </h3>
                        {!summaryWithRefs || summaryWithRefs.status === "PENDING" ? (
                            <div className="text-muted-foreground">Waiting for paper analysis to complete...</div>
                        ) : summaryWithRefs.status === "RUNNING" || summaryWithRefs.status === "QUEUED" ? (
                            <div className="text-muted-foreground animate-pulse">Synthesizing findings...</div>
                        ) : summaryWithRefs.status === "FAILED" ? (
                            <div className="text-red-600">Synthesis failed: {summaryWithRefs.error_message}</div>
                        ) : summaryWithRefs.summary ? (
                            <div className="space-y-6">
                                <div>
                                    <h4 className="font-medium text-muted-foreground mb-2">Executive Summary (TLDR)</h4>
                                    <p className="text-sm">{summaryWithRefs.summary.tldr}</p>
                                </div>
                                <div>
                                    <h4 className="font-medium text-muted-foreground mb-2">
                                        Consensus Level: <span className={`px-2 py-0.5 rounded ${summaryWithRefs.summary.consensus_level === "high" ? "bg-green-100 text-green-700" :
                                            summaryWithRefs.summary.consensus_level === "medium" ? "bg-yellow-100 text-yellow-700" :
                                                "bg-red-100 text-red-700"
                                            }`}>{summaryWithRefs.summary.consensus_level}</span>
                                    </h4>
                                </div>
                                {summaryWithRefs.summary.key_points.length > 0 && (
                                    <div>
                                        <h4 className="font-medium text-muted-foreground mb-2">Key Points</h4>
                                        <ul className="space-y-2">
                                            {summaryWithRefs.summary.key_points.map((kp, i) => (
                                                <li key={i} className="text-sm flex items-start gap-2">
                                                    <span className="text-primary">•</span>
                                                    <div>
                                                        {kp.text}
                                                        <CitationChip indices={kp.citations} references={summaryWithRefs.references} />
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {summaryWithRefs.summary.gaps.length > 0 && (
                                    <div>
                                        <h4 className="font-medium text-muted-foreground mb-2">Research Gaps</h4>
                                        <ul className="text-sm space-y-1">
                                            {summaryWithRefs.summary.gaps.map((gap, i) => (
                                                <li key={i}>• {gap}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* References Section */}
                                {summaryWithRefs.references.length > 0 && (
                                    <div className="mt-8 pt-6 border-t">
                                        <h4 className="font-medium text-muted-foreground mb-3">References</h4>
                                        <ol className="space-y-2 text-sm">
                                            {summaryWithRefs.references.map((ref) => (
                                                <li key={ref.index} className="flex items-start gap-2">
                                                    <span className="text-muted-foreground font-medium">[{ref.index}]</span>
                                                    <div>
                                                        <span>{ref.formatted}</span>
                                                        {ref.link && (
                                                            <a
                                                                href={ref.link}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="ml-2 text-primary hover:underline"
                                                            >
                                                                →
                                                            </a>
                                                        )}
                                                    </div>
                                                </li>
                                            ))}
                                        </ol>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-muted-foreground">No summary available.</div>
                        )}
                    </div>
                )}

                {/* Claims Tab with Clickable Citations */}
                {run.status === "DONE" && activeTab === "claims" && summaryWithRefs?.summary && (
                    <div className="rounded-lg border bg-card p-6">
                        <h3 className="text-lg font-semibold mb-4">Claims Draft</h3>
                        {!summaryWithRefs.summary.claims_draft || summaryWithRefs.summary.claims_draft.length === 0 ? (
                            <div className="text-muted-foreground">No claims generated yet.</div>
                        ) : (
                            <div className="space-y-4">
                                {summaryWithRefs.summary.claims_draft.map((claim, i) => (
                                    <div key={i} className={`p-4 rounded-lg border ${claim.allowed ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"}`}>
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${claim.allowed ? "bg-green-200 text-green-800" : "bg-red-200 text-red-800"}`}>
                                                {claim.allowed ? "✓ Allowed" : "✗ Not Allowed"}
                                            </span>
                                        </div>
                                        <p className="font-medium text-sm mb-2">
                                            &quot;{claim.claim}&quot;
                                            <CitationChip indices={claim.citations} references={summaryWithRefs.references} />
                                        </p>
                                        <p className="text-xs text-muted-foreground">{claim.rationale}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* No claims state fallback */}
                {run.status === "DONE" && activeTab === "claims" && !summaryWithRefs?.summary && (
                    <div className="rounded-lg border bg-card p-6">
                        <h3 className="text-lg font-semibold mb-4">Claims Draft</h3>
                        <div className="text-muted-foreground">No claims generated yet.</div>
                    </div>
                )}

                {/* Metadata */}
                <div className="rounded-lg border bg-card p-6">
                    <h3 className="text-sm font-medium text-muted-foreground mb-4">Details</h3>
                    <dl className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <dt className="text-muted-foreground">Created</dt>
                            <dd className="font-medium">{new Date(run.created_at).toLocaleString()}</dd>
                        </div>
                        <div>
                            <dt className="text-muted-foreground">Run ID</dt>
                            <dd className="font-mono text-xs">{run.id}</dd>
                        </div>
                    </dl>
                </div>

                {project && (
                    <div>
                        <Link href={`/projects/${project.id}`}>
                            <Button variant="outline">← Back to Project</Button>
                        </Link>
                    </div>
                )}
            </div>

            {/* Paper Summary Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-auto">
                        <div className="p-6 border-b flex items-center justify-between">
                            <h2 className="text-lg font-semibold">Paper Summary</h2>
                            <button onClick={() => { setShowModal(false); setSelectedSummary(null); }} className="text-muted-foreground hover:text-foreground">✕</button>
                        </div>
                        <div className="p-6">
                            {loadingSummary ? (
                                <div className="text-center py-8 text-muted-foreground">Loading...</div>
                            ) : selectedSummary?.summary ? (
                                <div className="space-y-4 text-sm">
                                    {selectedSummary.summary.study_type && <div><strong>Study Type:</strong> {selectedSummary.summary.study_type}</div>}
                                    {selectedSummary.summary.population && <div><strong>Population:</strong> {selectedSummary.summary.population}</div>}
                                    {selectedSummary.summary.intervention && <div><strong>Intervention:</strong> {selectedSummary.summary.intervention}</div>}
                                    {selectedSummary.summary.outcomes?.length > 0 && (
                                        <div><strong>Outcomes:</strong> {selectedSummary.summary.outcomes.join(", ")}</div>
                                    )}
                                    {selectedSummary.summary.key_findings?.length > 0 && (
                                        <div><strong>Key Findings:</strong>
                                            <ul className="list-disc ml-5 mt-1">{selectedSummary.summary.key_findings.map((f, i) => <li key={i}>{f}</li>)}</ul>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-muted-foreground">No summary available.</div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Evidence Detail Drawer */}
            {showEvidenceDrawer && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-end z-50">
                    <div className="bg-white h-full w-full max-w-lg shadow-xl overflow-auto">
                        <div className="p-6 border-b flex items-center justify-between sticky top-0 bg-white">
                            <h2 className="text-lg font-semibold">Evidence Detail</h2>
                            <button onClick={() => { setShowEvidenceDrawer(false); setEvidenceDetail(null); }} className="text-muted-foreground hover:text-foreground">✕</button>
                        </div>
                        <div className="p-6">
                            {loadingEvidence ? (
                                <div className="text-center py-8 text-muted-foreground">Loading...</div>
                            ) : evidenceDetail ? (
                                <div className="space-y-4">
                                    <h3 className="font-semibold text-lg">{evidenceDetail.title}</h3>
                                    <div className="text-sm text-muted-foreground">
                                        {evidenceDetail.authors.length > 0 && (
                                            <p>{evidenceDetail.authors.slice(0, 3).join(", ")}{evidenceDetail.authors.length > 3 && " et al."}</p>
                                        )}
                                        <p>
                                            {evidenceDetail.year && <span>{evidenceDetail.year} • </span>}
                                            {evidenceDetail.journal && <span>{evidenceDetail.journal}</span>}
                                        </p>
                                    </div>
                                    <div className="flex gap-2 flex-wrap">
                                        {evidenceDetail.pmid && (
                                            <a href={`https://pubmed.ncbi.nlm.nih.gov/${evidenceDetail.pmid}/`} target="_blank" rel="noopener noreferrer" className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                                                PMID: {evidenceDetail.pmid}
                                            </a>
                                        )}
                                        {evidenceDetail.doi && (
                                            <a href={`https://doi.org/${evidenceDetail.doi}`} target="_blank" rel="noopener noreferrer" className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200">
                                                DOI: {evidenceDetail.doi}
                                            </a>
                                        )}
                                    </div>
                                    {evidenceDetail.study_type && (
                                        <div>
                                            <h4 className="font-medium text-sm text-muted-foreground mb-1">Study Type</h4>
                                            <p className="text-sm">{evidenceDetail.study_type}</p>
                                        </div>
                                    )}
                                    {evidenceDetail.key_findings.length > 0 && (
                                        <div>
                                            <h4 className="font-medium text-sm text-muted-foreground mb-1">Key Findings</h4>
                                            <ul className="text-sm space-y-1">
                                                {evidenceDetail.key_findings.map((f, i) => (
                                                    <li key={i}>• {f}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    {evidenceDetail.evidence_snippets.length > 0 && (
                                        <div>
                                            <h4 className="font-medium text-sm text-muted-foreground mb-1">Evidence Snippets</h4>
                                            <div className="space-y-2">
                                                {evidenceDetail.evidence_snippets.map((snippet, i) => (
                                                    <blockquote key={i} className="text-sm italic border-l-2 border-primary pl-3 py-1 bg-muted/30">
                                                        &quot;{snippet}&quot;
                                                    </blockquote>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {evidenceDetail.url && (
                                        <a href={evidenceDetail.url} target="_blank" rel="noopener noreferrer" className="inline-block mt-4 text-primary hover:underline text-sm">
                                            View Source →
                                        </a>
                                    )}
                                </div>
                            ) : (
                                <div className="text-muted-foreground">No evidence found.</div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* On-Demand Summary Modal */}
            {showOnDemandModal && onDemandSummary && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-background rounded-lg shadow-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto m-4">
                        <div className="p-6 border-b sticky top-0 bg-background flex justify-between items-center">
                            <div>
                                <h2 className="text-xl font-semibold">Paper Summary</h2>
                                <p className="text-sm text-muted-foreground">
                                    {onDemandSummary.cached ? "Cached summary" : "Newly generated"}
                                </p>
                            </div>
                            <button
                                onClick={() => setShowOnDemandModal(false)}
                                className="text-muted-foreground hover:text-foreground text-2xl"
                            >
                                ×
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            {onDemandSummary.summary_json ? (
                                <>
                                    {onDemandSummary.summary_json.study_type && (
                                        <div>
                                            <h3 className="font-medium text-sm text-muted-foreground">Study Type</h3>
                                            <p>{String(onDemandSummary.summary_json.study_type)}</p>
                                        </div>
                                    )}
                                    {onDemandSummary.summary_json.key_findings && (
                                        <div>
                                            <h3 className="font-medium text-sm text-muted-foreground">Key Findings</h3>
                                            <ul className="list-disc list-inside space-y-1">
                                                {(onDemandSummary.summary_json.key_findings as string[]).map((finding, i) => (
                                                    <li key={i} className="text-sm">{finding}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    {onDemandSummary.summary_json.clinical_relevance && (
                                        <div>
                                            <h3 className="font-medium text-sm text-muted-foreground">Clinical Relevance</h3>
                                            <p className="text-sm">{String(onDemandSummary.summary_json.clinical_relevance)}</p>
                                        </div>
                                    )}
                                    {onDemandSummary.summary_json.limitations && (
                                        <div>
                                            <h3 className="font-medium text-sm text-muted-foreground">Limitations</h3>
                                            <ul className="list-disc list-inside space-y-1">
                                                {(onDemandSummary.summary_json.limitations as string[]).map((lim, i) => (
                                                    <li key={i} className="text-sm text-muted-foreground">{lim}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    {onDemandSummary.summary_json.pico && (
                                        <div>
                                            <h3 className="font-medium text-sm text-muted-foreground">PICO</h3>
                                            <div className="grid grid-cols-2 gap-2 text-sm">
                                                <div><span className="font-medium">P:</span> {String((onDemandSummary.summary_json.pico as Record<string, unknown>).population || '-')}</div>
                                                <div><span className="font-medium">I:</span> {String((onDemandSummary.summary_json.pico as Record<string, unknown>).intervention || '-')}</div>
                                                <div><span className="font-medium">C:</span> {String((onDemandSummary.summary_json.pico as Record<string, unknown>).comparison || '-')}</div>
                                                <div><span className="font-medium">O:</span> {String((onDemandSummary.summary_json.pico as Record<string, unknown>).outcome || '-')}</div>
                                            </div>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <p className="text-muted-foreground">No summary data available.</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
