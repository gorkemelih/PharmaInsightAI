"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import {
    getRun,
    getProject,
    getRunPapers,
    getRunSummaries,
    getEvidenceTable,
    getSummaryWithReferences,
    getPaperSummary,
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

export type TabType = "papers" | "summary" | "claims";

export interface UseRunDetailsReturn {
    // Auth & navigation
    user: ReturnType<typeof useAuth>["user"];
    loading: boolean;
    runId: string;

    // Core data
    run: Run | null;
    project: Project | null;
    papers: Paper[];
    summaries: SummaryStatus[];
    evidenceTable: EvidenceRow[];
    summaryWithRefs: SummaryWithReferencesResponse | null;

    // Selected/modal data
    selectedSummary: Summary | null;
    evidenceDetail: EvidenceDetail | null;
    onDemandSummary: OnDemandSummary | null;

    // UI state
    activeTab: TabType;
    setActiveTab: (tab: TabType) => void;
    showModal: boolean;
    setShowModal: (show: boolean) => void;
    showEvidenceDrawer: boolean;
    setShowEvidenceDrawer: (show: boolean) => void;
    showOnDemandModal: boolean;
    setShowOnDemandModal: (show: boolean) => void;

    // Loading states
    loadingData: boolean;
    loadingPapers: boolean;
    loadingSummary: boolean;
    loadingEvidence: boolean;
    downloadingPdf: boolean;
    generatingSummary: string | null;

    // Error state
    error: string;
    setError: (error: string) => void;

    // Actions
    handleDownloadPdf: () => Promise<void>;
    handleGenerateSummary: (paperId: string) => Promise<void>;
    handleViewSummary: (paperId: string) => Promise<void>;
    handleCitationClick: (ref: FormattedReference) => Promise<void>;

    // Helpers
    getSummaryStatus: (paperId: string) => SummaryStatus | undefined;
    getStatusColor: (status: string) => string;
    getStatusBadge: (status: string) => string;

    // Refetch functions
    fetchSummaries: () => Promise<void>;
    fetchSummaryWithRefs: () => Promise<void>;
}

export function useRunDetails(): UseRunDetailsReturn {
    const { user, loading } = useAuth();
    const router = useRouter();
    const params = useParams();
    const runId = params.id as string;

    // Tab state
    const [activeTab, setActiveTab] = useState<TabType>("papers");

    // Core data
    const [run, setRun] = useState<Run | null>(null);
    const [project, setProject] = useState<Project | null>(null);
    const [papers, setPapers] = useState<Paper[]>([]);
    const [summaries, setSummaries] = useState<SummaryStatus[]>([]);
    const [evidenceTable, setEvidenceTable] = useState<EvidenceRow[]>([]);
    const [summaryWithRefs, setSummaryWithRefs] = useState<SummaryWithReferencesResponse | null>(null);

    // Selected/modal data
    const [selectedSummary, setSelectedSummary] = useState<Summary | null>(null);
    const [evidenceDetail, setEvidenceDetail] = useState<EvidenceDetail | null>(null);
    const [onDemandSummary, setOnDemandSummary] = useState<OnDemandSummary | null>(null);

    // UI state
    const [showModal, setShowModal] = useState(false);
    const [showEvidenceDrawer, setShowEvidenceDrawer] = useState(false);
    const [showOnDemandModal, setShowOnDemandModal] = useState(false);

    // Loading states
    const [loadingData, setLoadingData] = useState(true);
    const [loadingPapers, setLoadingPapers] = useState(false);
    const [loadingSummary, setLoadingSummary] = useState(false);
    const [loadingEvidence, setLoadingEvidence] = useState(false);
    const [downloadingPdf, setDownloadingPdf] = useState(false);
    const [generatingSummary, setGeneratingSummary] = useState<string | null>(null);

    // Error state
    const [error, setError] = useState("");

    // Fetch functions
    const fetchData = useCallback(async () => {
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
    }, [runId, project]);

    const fetchPapers = useCallback(async () => {
        setLoadingPapers(true);
        try {
            const papersData = await getRunPapers(runId);
            setPapers(papersData);
        } catch (err) {
            console.error("Failed to fetch papers:", err);
        } finally {
            setLoadingPapers(false);
        }
    }, [runId]);

    const fetchSummaries = useCallback(async () => {
        try {
            const summariesData = await getRunSummaries(runId);
            setSummaries(summariesData);
        } catch (err) {
            console.error("Failed to fetch summaries:", err);
        }
    }, [runId]);

    const fetchEvidenceTable = useCallback(async () => {
        try {
            const data = await getEvidenceTable(runId);
            setEvidenceTable(data);
        } catch (err) {
            console.error("Failed to fetch evidence table:", err);
        }
    }, [runId]);

    const fetchSummaryWithRefs = useCallback(async () => {
        try {
            const data = await getSummaryWithReferences(runId);
            setSummaryWithRefs(data);
        } catch (err) {
            console.error("Failed to fetch summary with references:", err);
        }
    }, [runId]);

    // Action handlers
    const handleDownloadPdf = useCallback(async () => {
        setDownloadingPdf(true);
        try {
            await downloadRunReport(runId);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to download PDF");
        } finally {
            setDownloadingPdf(false);
        }
    }, [runId]);

    const handleGenerateSummary = useCallback(async (paperId: string) => {
        setGeneratingSummary(paperId);
        setError("");
        try {
            const summary = await generatePaperSummary(runId, paperId);
            setOnDemandSummary(summary);
            setShowOnDemandModal(true);
            fetchSummaries();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to generate summary");
        } finally {
            setGeneratingSummary(null);
        }
    }, [runId, fetchSummaries]);

    const handleViewSummary = useCallback(async (paperId: string) => {
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
    }, [runId]);

    const handleCitationClick = useCallback(async (ref: FormattedReference) => {
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
    }, [runId]);

    // Helper functions
    const getSummaryStatus = useCallback((paperId: string) => {
        return summaries.find((s) => s.paper_id === paperId);
    }, [summaries]);

    const getStatusColor = useCallback((status: string) => {
        switch (status) {
            case "DONE": return "bg-green-100 text-green-700 border-green-200";
            case "RUNNING": return "bg-blue-100 text-blue-700 border-blue-200";
            case "QUEUED": return "bg-yellow-100 text-yellow-700 border-yellow-200";
            case "FAILED": return "bg-red-100 text-red-700 border-red-200";
            default: return "bg-gray-100 text-gray-700 border-gray-200";
        }
    }, []);

    const getStatusBadge = useCallback((status: string) => {
        const colors: Record<string, string> = {
            DONE: "bg-green-100 text-green-700",
            RUNNING: "bg-blue-100 text-blue-700",
            QUEUED: "bg-yellow-100 text-yellow-700",
            FAILED: "bg-red-100 text-red-700",
            PENDING: "bg-gray-100 text-gray-700",
        };
        return colors[status] || "bg-gray-100 text-gray-700";
    }, []);

    // Effects
    useEffect(() => {
        if (!loading && !user) {
            router.push("/login");
        }
    }, [user, loading, router]);

    useEffect(() => {
        if (user && runId) {
            fetchData();
        }
    }, [user, runId, fetchData]);

    useEffect(() => {
        if (run && (run.status === "QUEUED" || run.status === "RUNNING")) {
            const interval = setInterval(fetchData, 2000);
            return () => clearInterval(interval);
        }
    }, [run?.status, fetchData]);

    useEffect(() => {
        if (run?.status === "DONE" && papers.length === 0 && !loadingPapers) {
            fetchPapers();
            fetchSummaries();
            fetchEvidenceTable();
            fetchSummaryWithRefs();
        }
    }, [run?.status, papers.length, loadingPapers, fetchPapers, fetchSummaries, fetchEvidenceTable, fetchSummaryWithRefs]);

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
    }, [run?.status, summaries, fetchSummaries, fetchEvidenceTable, fetchSummaryWithRefs]);

    useEffect(() => {
        if (summaryWithRefs && (summaryWithRefs.status === "QUEUED" || summaryWithRefs.status === "RUNNING")) {
            const interval = setInterval(fetchSummaryWithRefs, 3000);
            return () => clearInterval(interval);
        }
    }, [summaryWithRefs?.status, fetchSummaryWithRefs]);

    return {
        // Auth & navigation
        user,
        loading,
        runId,

        // Core data
        run,
        project,
        papers,
        summaries,
        evidenceTable,
        summaryWithRefs,

        // Selected/modal data
        selectedSummary,
        evidenceDetail,
        onDemandSummary,

        // UI state
        activeTab,
        setActiveTab,
        showModal,
        setShowModal,
        showEvidenceDrawer,
        setShowEvidenceDrawer,
        showOnDemandModal,
        setShowOnDemandModal,

        // Loading states
        loadingData,
        loadingPapers,
        loadingSummary,
        loadingEvidence,
        downloadingPdf,
        generatingSummary,

        // Error state
        error,
        setError,

        // Actions
        handleDownloadPdf,
        handleGenerateSummary,
        handleViewSummary,
        handleCitationClick,

        // Helpers
        getSummaryStatus,
        getStatusColor,
        getStatusBadge,

        // Refetch functions
        fetchSummaries,
        fetchSummaryWithRefs,
    };
}
