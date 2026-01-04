"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { getProjects, createProject, deleteProject, Project } from "@/lib/api";
import { Trash2, Loader2 } from "lucide-react";

export default function ProjectsPage() {
    const { user, loading } = useAuth();
    const { t } = useI18n();
    const router = useRouter();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loadingProjects, setLoadingProjects] = useState(true);
    const [error, setError] = useState("");
    const [archiving, setArchiving] = useState<string | null>(null);

    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [newName, setNewName] = useState("");
    const [newDescription, setNewDescription] = useState("");
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        if (!loading && !user) {
            router.push("/login");
        }
    }, [user, loading, router]);

    useEffect(() => {
        if (user) {
            fetchProjects();
        }
    }, [user]);

    const fetchProjects = async () => {
        try {
            const data = await getProjects();
            setProjects(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch projects");
        } finally {
            setLoadingProjects(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        try {
            const project = await createProject({
                name: newName,
                description: newDescription || undefined,
            });
            setShowModal(false);
            setNewName("");
            setNewDescription("");
            router.push(`/projects/${project.id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create project");
        } finally {
            setCreating(false);
        }
    };

    const handleArchive = async (e: React.MouseEvent, projectId: string, projectName: string) => {
        e.preventDefault();
        e.stopPropagation();

        if (!confirm(t.projects.deleteConfirmation.replace("{name}", projectName))) {
            return;
        }

        setArchiving(projectId);
        try {
            await deleteProject(projectId);
            setProjects(projects.filter(p => p.id !== projectId));
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to archive project");
        } finally {
            setArchiving(null);
        }
    };

    const canCreate = user?.role === "ADMIN" || user?.role === "ANALYST";
    const canArchive = user?.role === "ADMIN";

    if (loading || !user) {
        return (
            <div className="container py-8">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 w-32 bg-muted rounded" />
                </div>
            </div>
        );
    }

    return (
        <div className="container py-8">
            <div className="flex flex-col gap-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">{t.projects.title}</h1>
                        <p className="text-muted-foreground">
                            {t.projects.subtitle}
                        </p>
                    </div>
                    {canCreate && (
                        <Button onClick={() => setShowModal(true)}>{t.projects.newProject}</Button>
                    )}
                </div>

                {error && (
                    <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">
                        {error}
                    </div>
                )}

                {loadingProjects ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="rounded-lg border bg-card p-6 animate-pulse">
                                <div className="h-6 w-32 bg-muted rounded mb-2" />
                                <div className="h-4 w-48 bg-muted rounded" />
                            </div>
                        ))}
                    </div>
                ) : projects.length === 0 ? (
                    <div className="text-center py-12 rounded-lg border bg-card">
                        <h3 className="text-lg font-medium mb-2">{t.projects.noProjects}</h3>
                        <p className="text-muted-foreground mb-4">
                            {t.projects.createFirst}
                        </p>
                        {canCreate && (
                            <Button onClick={() => setShowModal(true)}>{t.projects.newProject}</Button>
                        )}
                    </div>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {projects.map((project) => (
                            <div
                                key={project.id}
                                className="rounded-lg border bg-card p-6 hover:border-primary transition-colors relative group"
                            >
                                <Link href={`/projects/${project.id}`} className="block">
                                    <h3 className="text-lg font-semibold mb-2">{project.name}</h3>
                                    <p className="text-sm text-muted-foreground line-clamp-2">
                                        {project.description || "No description"}
                                    </p>
                                    <p className="text-xs text-muted-foreground mt-4">
                                        {t.dashboard.created} {new Date(project.created_at).toLocaleDateString()}
                                    </p>
                                </Link>
                                {canArchive && (
                                    <button
                                        onClick={(e) => handleArchive(e, project.id, project.name)}
                                        disabled={archiving === project.id}
                                        className="absolute top-4 right-4 p-2 rounded-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                                        title={t.projects.deleteTooltip}
                                    >
                                        {archiving === project.id ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Trash2 className="h-4 w-4" />
                                        )}
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Project Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="bg-background rounded-lg p-6 w-full max-w-md shadow-lg">
                        <h2 className="text-xl font-semibold mb-4">{t.projects.createModalTitle}</h2>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">{t.projects.name}</label>
                                <input
                                    type="text"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    required
                                    placeholder={t.projects.placeholderName}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">{t.projects.description}</label>
                                <textarea
                                    value={newDescription}
                                    onChange={(e) => setNewDescription(e.target.value)}
                                    placeholder={t.projects.placeholderDesc}
                                    rows={3}
                                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                />
                            </div>
                            <div className="flex justify-end gap-2 pt-4">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => setShowModal(false)}
                                >
                                    {t.common.cancel}
                                </Button>
                                <Button type="submit" disabled={creating}>
                                    {creating ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            {t.common.loading}
                                        </>
                                    ) : (
                                        t.common.create
                                    )}
                                </Button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
