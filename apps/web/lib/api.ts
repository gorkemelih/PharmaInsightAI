/**
 * API client for projects and runs
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Project {
    id: string;
    name: string;
    description: string | null;
    tenant_id: string;
    created_by_user_id: string | null;
    created_at: string;
}

export interface Run {
    id: string;
    project_id: string;
    query_text: string;
    status: "QUEUED" | "RUNNING" | "DONE" | "FAILED";
    error_message: string | null;
    created_at: string;
    max_papers: number;
    year_from: number | null;
    year_to: number | null;
    analysis_mode?: "synthesis" | "per_paper";
}

// Projects API
export async function getProjects(): Promise<Project[]> {
    const response = await fetch(`${API_URL}/projects`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch projects");
    }

    return response.json();
}

export async function getProject(id: string): Promise<Project> {
    const response = await fetch(`${API_URL}/projects/${id}`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch project");
    }

    return response.json();
}

export async function createProject(data: { name: string; description?: string }): Promise<Project> {
    const response = await fetch(`${API_URL}/projects`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create project");
    }

    return response.json();
}

export async function deleteProject(id: string): Promise<void> {
    const response = await fetch(`${API_URL}/projects/${id}`, {
        method: "DELETE",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete project");
    }
}

export async function restoreProject(id: string): Promise<Project> {
    const response = await fetch(`${API_URL}/projects/${id}/restore`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to restore project");
    }

    return response.json();
}

export async function deleteRun(id: string): Promise<void> {
    const response = await fetch(`${API_URL}/runs/${id}`, {
        method: "DELETE",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete run");
    }
}

export async function restoreRun(id: string): Promise<Run> {
    const response = await fetch(`${API_URL}/runs/${id}/restore`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to restore run");
    }

    return response.json();
}

// Runs API
export async function getProjectRuns(projectId: string): Promise<Run[]> {
    const response = await fetch(`${API_URL}/projects/${projectId}/runs`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch runs");
    }

    return response.json();
}

export type AnalysisMode = "synthesis" | "per_paper";

export interface CreateRunParams {
    query_text: string;
    max_papers?: number;
    year_from?: number;
    year_to?: number;
    analysis_mode?: AnalysisMode;
    include_marketing?: boolean;
    language?: "en" | "tr";
}

export async function createRun(projectId: string, params: CreateRunParams | string): Promise<Run> {
    // Support both old (string) and new (object) API
    const body = typeof params === "string" ? { query_text: params } : params;

    const response = await fetch(`${API_URL}/projects/${projectId}/runs`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create run");
    }

    return response.json();
}

export async function getRun(runId: string): Promise<Run> {
    const response = await fetch(`${API_URL}/runs/${runId}`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch run");
    }

    return response.json();
}

// Papers API
export interface Paper {
    id: string;
    title: string;
    abstract: string | null;
    journal: string | null;
    year: number | null;
    authors: string[];
    pmid: string | null;
    doi: string | null;
    url: string | null;
    source: string;
}

export async function getRunPapers(runId: string): Promise<Paper[]> {
    const response = await fetch(`${API_URL}/runs/${runId}/papers`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch papers");
    }

    return response.json();
}

// Summaries API
export interface SummaryStatus {
    paper_id: string;
    title: string;
    status: "QUEUED" | "RUNNING" | "DONE" | "FAILED";
    error_message: string | null;
}

export interface EvidenceSnippet {
    quote: string;
    location: string;
    confidence: number;
}

export interface QualityFlags {
    is_review: boolean;
    has_humans: boolean | null;
    has_animals: boolean | null;
    has_rct_terms: boolean;
    contains_numbers: boolean;
}

export interface PaperSummaryData {
    study_type: string | null;
    population: string | null;
    intervention: string | null;
    comparator: string | null;
    outcomes: string[];
    key_findings: string[];
    limitations: string[];
    evidence_snippets: EvidenceSnippet[];
    quality_flags: QualityFlags;
}

export interface Summary {
    paper_id: string;
    run_id: string;
    status: "QUEUED" | "RUNNING" | "DONE" | "FAILED";
    model: string;
    summary: PaperSummaryData | null;
    error_message: string | null;
}

export async function getRunSummaries(runId: string): Promise<SummaryStatus[]> {
    const response = await fetch(`${API_URL}/runs/${runId}/summaries`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch summaries");
    }

    return response.json();
}

// On-demand paper summary (new endpoints)
export interface OnDemandSummary {
    id: string;
    paper_id: string;
    run_id: string;
    status: string;
    summary_json: Record<string, unknown> | null;
    created_at: string;
    cached: boolean;
}

export async function generatePaperSummary(runId: string, paperId: string): Promise<OnDemandSummary> {
    const response = await fetch(`${API_URL}/runs/${runId}/papers/${paperId}/summary`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate summary");
    }

    return response.json();
}

export async function getPaperSummaryOnDemand(runId: string, paperId: string): Promise<OnDemandSummary | null> {
    const response = await fetch(`${API_URL}/runs/${runId}/papers/${paperId}/summary`, {
        credentials: "include",
    });

    if (response.status === 404) {
        return null; // Summary not yet generated
    }

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch summary");
    }

    return response.json();
}

// Legacy endpoint (kept for compatibility)
export async function getPaperSummary(paperId: string, runId: string): Promise<Summary> {
    const response = await fetch(`${API_URL}/papers/${paperId}/summary?run_id=${runId}`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch summary");
    }

    return response.json();
}

// Evidence Table and Run Summary API
export interface EvidenceRow {
    paper_id: string;
    citation: {
        pmid: string | null;
        doi: string | null;
        year: number | null;
        title: string;
        journal: string | null;
    };
    study_type: string | null;
    population: string | null;
    intervention: string | null;
    comparator: string | null;
    outcomes: string[];
    key_findings: string[];
    limitations: string[];
}

export interface Citation {
    paper_id: string;
    pmid: string | null;
    doi: string | null;
}

export interface KeyPoint {
    text: string;
    citations: Citation[];
}

export interface Claim {
    claim: string;
    allowed: boolean;
    rationale: string;
    citations: Citation[];
}

export interface RunSynthesisSummary {
    tldr: string;
    key_points: KeyPoint[];
    consensus_level: "high" | "medium" | "low";
    contradictions: KeyPoint[];
    gaps: string[];
    safety_notes: string[];
    claims_draft: Claim[];
}

export interface RunSummaryResponse {
    run_id: string;
    status: "PENDING" | "QUEUED" | "RUNNING" | "DONE" | "FAILED";
    model: string;
    summary: RunSynthesisSummary | null;
    error_message: string | null;
}

export async function getEvidenceTable(runId: string): Promise<EvidenceRow[]> {
    const response = await fetch(`${API_URL}/runs/${runId}/evidence-table`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch evidence table");
    }

    return response.json();
}

export async function getRunSummary(runId: string): Promise<RunSummaryResponse> {
    const response = await fetch(`${API_URL}/runs/${runId}/summary`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch run summary");
    }

    return response.json();
}

export async function retryRunSummary(runId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_URL}/runs/${runId}/summary/retry`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to retry synthesis");
    }

    return response.json();
}

// Summary with References API
export interface FormattedReference {
    index: number;
    paper_id: string;
    formatted: string;
    link: string | null;
}

export interface CitationWithIndex {
    index: number;
}

export interface KeyPointWithIndices {
    text: string;
    citations: CitationWithIndex[];
}

export interface ClaimWithIndices {
    claim: string;
    allowed: boolean;
    rationale: string;
    citations: CitationWithIndex[];
}

export interface SummaryWithIndices {
    tldr: string;
    key_points: KeyPointWithIndices[];
    consensus_level: "high" | "medium" | "low";
    contradictions: KeyPointWithIndices[];
    gaps: string[];
    safety_notes: string[];
    claims_draft: ClaimWithIndices[];
}

export interface SummaryWithReferencesResponse {
    run_id: string;
    status: "PENDING" | "QUEUED" | "RUNNING" | "DONE" | "FAILED";
    summary: SummaryWithIndices | null;
    references: FormattedReference[];
    error_message: string | null;
}

export async function getSummaryWithReferences(runId: string): Promise<SummaryWithReferencesResponse> {
    const response = await fetch(`${API_URL}/runs/${runId}/summary-with-references`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch summary with references");
    }

    return response.json();
}

// Evidence Detail API
export interface EvidenceDetail {
    paper_id: string;
    title: string;
    authors: string[];
    year: number | null;
    journal: string | null;
    pmid: string | null;
    doi: string | null;
    url: string | null;
    evidence_snippets: string[];
    key_findings: string[];
    study_type: string | null;
}

export async function getEvidenceDetail(runId: string, paperId: string): Promise<EvidenceDetail> {
    const response = await fetch(`${API_URL}/runs/${runId}/evidence/${paperId}`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch evidence detail");
    }

    return response.json();
}

// Dashboard API
export interface DashboardSummary {
    total_projects: number;
    total_papers: number;
    total_runs: number;
    pending_runs: number;
}

export interface RecentRun {
    id: string;
    query_text: string;
    status: "QUEUED" | "RUNNING" | "DONE" | "FAILED";
    paper_count: number;
    created_at: string;
    project_name: string;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
    const response = await fetch(`${API_URL}/dashboard/summary`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch dashboard summary");
    }

    return response.json();
}

export async function getRecentRuns(limit: number = 10): Promise<RecentRun[]> {
    const response = await fetch(`${API_URL}/runs/recent?limit=${limit}`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch recent runs");
    }

    return response.json();
}

// PDF Report API
export async function downloadRunReport(runId: string): Promise<void> {
    const response = await fetch(`${API_URL}/runs/${runId}/report.pdf`, {
        credentials: "include",
    });

    if (!response.ok) {
        let errorMessage = "Failed to download report";
        try {
            const error = await response.json();
            errorMessage = error.detail || errorMessage;
        } catch {
            // Response wasn't JSON
        }
        throw new Error(errorMessage);
    }

    // Get the blob from response
    const blob = await response.blob();

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pharmainsightai-run-${runId}.pdf`;
    document.body.appendChild(a);
    a.click();

    // Cleanup
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// ============ Documents API ============

export interface DocumentItem {
    id: string;
    project_id: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    status: "uploaded" | "processing" | "processed" | "failed";
    error_message: string | null;
    created_at: string;
    chunk_count: number;
}

export interface DocumentUploadResponse {
    id: string;
    filename: string;
    status: string;
    message: string;
}

export interface AnalysisCitation {
    key: string;
    type: "internal" | "literature";
    doc_id?: string;
    chunk_id?: string;
    filename?: string;
    page_number?: number;
    paper_id?: string;
    pmid?: string;
    doi?: string;
    title?: string;
}

export interface InternalAnalysisResponse {
    markdown_report: string;
    citations: AnalysisCitation[];
    warning?: string;
}

export async function uploadDocument(projectId: string, file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/projects/${projectId}/documents`, {
        method: "POST",
        credentials: "include",
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to upload document");
    }

    return response.json();
}

export async function getDocuments(projectId: string): Promise<DocumentItem[]> {
    const response = await fetch(`${API_URL}/projects/${projectId}/documents`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch documents");
    }

    return response.json();
}

export async function processDocument(docId: string): Promise<DocumentItem> {
    const response = await fetch(`${API_URL}/documents/${docId}/process`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to process document");
    }

    return response.json();
}

export async function deleteDocument(docId: string): Promise<void> {
    const response = await fetch(`${API_URL}/documents/${docId}`, {
        method: "DELETE",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete document");
    }
}

export async function runInternalAnalysis(
    projectId: string,
    question: string,
    scope: "internal_only" | "literature_only" | "hybrid" = "hybrid",
    maxSourcesInternal: number = 10,
    maxSourcesLiterature: number = 10,
): Promise<InternalAnalysisResponse> {
    const response = await fetch(`${API_URL}/projects/${projectId}/internal-analysis`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            question,
            scope,
            max_sources_internal: maxSourcesInternal,
            max_sources_literature: maxSourcesLiterature,
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to run analysis");
    }

    return response.json();
}
