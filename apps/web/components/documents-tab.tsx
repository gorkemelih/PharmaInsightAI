"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    DocumentItem,
    getDocuments,
    uploadDocument,
    processDocument,
    deleteDocument,
} from "@/lib/api";
import { Upload, FileText, Trash2, Play, Loader2, AlertCircle, CheckCircle } from "lucide-react";

interface DocumentsTabProps {
    projectId: string;
    documents: DocumentItem[];
    onRefresh: () => void;
}

export function DocumentsTab({ projectId, documents, onRefresh }: DocumentsTabProps) {
    const [uploading, setUploading] = useState(false);
    const [processing, setProcessing] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [dragActive, setDragActive] = useState(false);

    const handleUpload = async (files: FileList | null) => {
        if (!files || files.length === 0) return;

        setUploading(true);
        setError(null);

        try {
            for (const file of Array.from(files)) {
                await uploadDocument(projectId, file);
            }
            onRefresh();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Upload failed");
        } finally {
            setUploading(false);
        }
    };

    const handleProcess = async (docId: string) => {
        setProcessing(docId);
        setError(null);

        try {
            await processDocument(docId);
            onRefresh();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Processing failed");
        } finally {
            setProcessing(null);
        }
    };

    const handleDelete = async (docId: string) => {
        if (!confirm("Are you sure you want to delete this document?")) return;

        setError(null);
        try {
            await deleteDocument(docId);
            onRefresh();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Delete failed");
        }
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
        handleUpload(e.dataTransfer.files);
    }, [projectId]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(true);
    }, []);

    const handleDragLeave = useCallback(() => {
        setDragActive(false);
    }, []);

    const formatBytes = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const getStatusBadge = (doc: DocumentItem) => {
        const statusColors = {
            uploaded: "bg-yellow-100 text-yellow-700",
            processing: "bg-blue-100 text-blue-700",
            processed: "bg-green-100 text-green-700",
            failed: "bg-red-100 text-red-700",
        };

        const statusIcons = {
            uploaded: <AlertCircle className="h-3 w-3" />,
            processing: <Loader2 className="h-3 w-3 animate-spin" />,
            processed: <CheckCircle className="h-3 w-3" />,
            failed: <AlertCircle className="h-3 w-3" />,
        };

        return (
            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusColors[doc.status]}`}>
                {statusIcons[doc.status]}
                {doc.status}
            </span>
        );
    };

    return (
        <div className="space-y-6">
            {/* Upload Area */}
            <Card
                className={`border-2 border-dashed transition-colors ${dragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25"
                    }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
            >
                <CardContent className="flex flex-col items-center justify-center py-10">
                    <Upload className={`h-10 w-10 mb-4 ${dragActive ? "text-primary" : "text-muted-foreground"}`} />
                    <p className="text-sm text-muted-foreground mb-4">
                        Drag & drop files here, or click to browse
                    </p>
                    <input
                        type="file"
                        id="file-upload"
                        className="hidden"
                        multiple
                        accept=".pdf,.txt,.md,.csv"
                        onChange={(e) => handleUpload(e.target.files)}
                    />
                    <Button
                        variant="outline"
                        onClick={() => document.getElementById("file-upload")?.click()}
                        disabled={uploading}
                    >
                        {uploading ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Uploading...
                            </>
                        ) : (
                            <>
                                <Upload className="h-4 w-4 mr-2" />
                                Choose Files
                            </>
                        )}
                    </Button>
                    <p className="text-xs text-muted-foreground mt-2">
                        Supported: PDF, TXT, MD, CSV (max 50MB)
                    </p>
                </CardContent>
            </Card>

            {error && (
                <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">
                    {error}
                </div>
            )}

            {/* Documents List */}
            {documents.length === 0 ? (
                <Card>
                    <CardContent className="py-10 text-center text-muted-foreground">
                        <FileText className="h-10 w-10 mx-auto mb-4 opacity-50" />
                        <p>No documents uploaded yet</p>
                    </CardContent>
                </Card>
            ) : (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Documents ({documents.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="divide-y">
                            {documents.map((doc) => (
                                <div key={doc.id} className="flex items-center justify-between py-4">
                                    <div className="flex items-center gap-4">
                                        <FileText className="h-8 w-8 text-muted-foreground" />
                                        <div>
                                            <p className="font-medium">{doc.filename}</p>
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                <span>{formatBytes(doc.size_bytes)}</span>
                                                <span>•</span>
                                                <span>{doc.chunk_count} chunks</span>
                                                <span>•</span>
                                                <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                                            </div>
                                            {doc.error_message && (
                                                <p className="text-xs text-red-500 mt-1">{doc.error_message}</p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {getStatusBadge(doc)}
                                        {doc.status === "uploaded" && (
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleProcess(doc.id)}
                                                disabled={processing === doc.id}
                                            >
                                                {processing === doc.id ? (
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                ) : (
                                                    <>
                                                        <Play className="h-4 w-4 mr-1" />
                                                        Process
                                                    </>
                                                )}
                                            </Button>
                                        )}
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                            onClick={() => handleDelete(doc.id)}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
