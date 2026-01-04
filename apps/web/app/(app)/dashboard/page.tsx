"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    TrendingUp,
    FileText,
    FlaskConical,
    AlertTriangle,
    Plus,
    Download,
    RefreshCw,
} from "lucide-react";
import {
    getDashboardSummary,
    getRecentRuns,
    DashboardSummary,
    RecentRun,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function DashboardPage() {
    const { t } = useI18n();
    const [summary, setSummary] = useState<DashboardSummary | null>(null);
    const [recentRuns, setRecentRuns] = useState<RecentRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const fetchData = async () => {
        try {
            setLoading(true);
            setError("");
            const [summaryData, runsData] = await Promise.all([
                getDashboardSummary(),
                getRecentRuns(10),
            ]);
            setSummary(summaryData);
            setRecentRuns(runsData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const getStatusBadge = (status: string) => {
        switch (status) {
            case "DONE":
                return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">● {t.status.completed}</Badge>;
            case "RUNNING":
                return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">● {t.status.running}</Badge>;
            case "QUEUED":
                return <Badge className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100">● {t.status.pending}</Badge>;
            case "FAILED":
                return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">● {t.status.failed}</Badge>;
            default:
                return <Badge variant="outline">{status}</Badge>;
        }
    };

    const formatTimeAgo = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffHours < 24) return `${diffHours} hrs ago`;
        if (diffDays < 7) return `${diffDays} days ago`;
        return date.toLocaleDateString();
    };

    const statCards = [
        {
            title: t.dashboard.totalProjects,
            value: summary?.total_projects?.toString() || "0",
            change: "",
            icon: <FileText className="h-5 w-5" />,
            iconColor: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
        },
        {
            title: t.dashboard.papersAnalyzed,
            value: summary?.total_papers?.toLocaleString() || "0",
            change: "",
            icon: <FlaskConical className="h-5 w-5" />,
            iconColor: "bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400",
        },
        {
            title: t.dashboard.totalRuns,
            value: summary?.total_runs?.toString() || "0",
            change: "",
            icon: <TrendingUp className="h-5 w-5" />,
            iconColor: "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400",
        },
        {
            title: t.dashboard.pendingRuns,
            value: summary?.pending_runs?.toString() || "0",
            change: summary?.pending_runs && summary.pending_runs > 0 ? t.dashboard.inProgress : "",
            icon: <AlertTriangle className="h-5 w-5" />,
            iconColor: "bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400",
        },
    ];

    if (loading && !summary) {
        return (
            <div className="space-y-6">
                <div className="h-8 w-48 bg-muted rounded animate-pulse" />
                <div className="grid grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-32 bg-muted rounded-xl animate-pulse" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Breadcrumb */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>{t.common.home}</span>
                    <span>›</span>
                    <span className="text-foreground font-medium">{t.dashboard.title}</span>
                </div>
                <Button variant="ghost" size="sm" onClick={fetchData} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                    {t.dashboard.refresh}
                </Button>
            </div>

            {error && (
                <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">
                    {error}
                </div>
            )}

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {statCards.map((stat, i) => (
                    <Card key={i} className="stat-card">
                        <CardContent className="p-5">
                            <div className="flex items-start justify-between">
                                <div className={`p-2.5 rounded-lg ${stat.iconColor}`}>
                                    {stat.icon}
                                </div>
                                {stat.change && (
                                    <span className="text-xs font-medium text-orange-600">
                                        {stat.change}
                                    </span>
                                )}
                            </div>
                            <div className="mt-4">
                                <p className="text-sm text-muted-foreground">{stat.title}</p>
                                <p className="text-2xl font-bold">{stat.value}</p>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Recent Runs Section */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-4">
                    <div>
                        <CardTitle>{t.dashboard.researchDirectory}</CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">
                            {t.dashboard.manageAnalyses}
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 mr-2" />
                            {t.dashboard.export}
                        </Button>
                        <Button size="sm" asChild>
                            <Link href="/projects">
                                <Plus className="h-4 w-4 mr-2" />
                                {t.dashboard.newRun}
                            </Link>
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    {/* Table */}
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">{t.dashboard.query}</th>
                                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">{t.dashboard.project}</th>
                                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">{t.dashboard.papers}</th>
                                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">{t.dashboard.status}</th>
                                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">{t.dashboard.created}</th>
                                    <th className="text-right py-3 px-4 font-medium text-muted-foreground">{t.dashboard.actions}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recentRuns.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="py-8 text-center text-muted-foreground">
                                            {t.dashboard.noRuns}
                                        </td>
                                    </tr>
                                ) : (
                                    recentRuns.map((run) => (
                                        <tr key={run.id} className="border-b hover:bg-muted/50">
                                            <td className="py-3 px-4">
                                                <span className="font-medium line-clamp-1">{run.query_text}</span>
                                            </td>
                                            <td className="py-3 px-4 text-muted-foreground">
                                                {run.project_name}
                                            </td>
                                            <td className="py-3 px-4">{run.paper_count}</td>
                                            <td className="py-3 px-4">{getStatusBadge(run.status)}</td>
                                            <td className="py-3 px-4 text-muted-foreground">
                                                {formatTimeAgo(run.created_at)}
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <Link href={`/runs/${run.id}`}>
                                                    <Button variant="ghost" size="sm">
                                                        {t.common.view} →
                                                    </Button>
                                                </Link>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
