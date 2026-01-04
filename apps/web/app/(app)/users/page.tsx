"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { getUsers, createUser, deleteUser, User } from "@/lib/auth";

export default function UsersPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [users, setUsers] = useState<User[]>([]);
    const [loadingUsers, setLoadingUsers] = useState(true);
    const [error, setError] = useState("");

    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [newEmail, setNewEmail] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [newRole, setNewRole] = useState<"ADMIN" | "ANALYST" | "VIEWER">("VIEWER");
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        if (!loading && !user) {
            router.push("/login");
            return;
        }
        if (!loading && user && user.role !== "ADMIN") {
            router.push("/dashboard");
            return;
        }
    }, [user, loading, router]);

    useEffect(() => {
        if (user?.role === "ADMIN") {
            fetchUsers();
        }
    }, [user]);

    const fetchUsers = async () => {
        try {
            const data = await getUsers();
            setUsers(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch users");
        } finally {
            setLoadingUsers(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        try {
            await createUser({ email: newEmail, password: newPassword, role: newRole });
            setShowModal(false);
            setNewEmail("");
            setNewPassword("");
            setNewRole("VIEWER");
            fetchUsers();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create user");
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (userId: string) => {
        if (!confirm("Are you sure you want to delete this user?")) return;
        try {
            await deleteUser(userId);
            fetchUsers();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete user");
        }
    };

    if (loading || !user || user.role !== "ADMIN") {
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
                        <h1 className="text-3xl font-bold tracking-tight">Users</h1>
                        <p className="text-muted-foreground">Manage user accounts</p>
                    </div>
                    <Button onClick={() => setShowModal(true)}>Create User</Button>
                </div>

                {error && (
                    <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">
                        {error}
                    </div>
                )}

                <div className="rounded-lg border bg-card">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b bg-muted/50">
                                <tr>
                                    <th className="px-4 py-3 text-left font-medium">Email</th>
                                    <th className="px-4 py-3 text-left font-medium">Role</th>
                                    <th className="px-4 py-3 text-left font-medium">Status</th>
                                    <th className="px-4 py-3 text-left font-medium">Created</th>
                                    <th className="px-4 py-3 text-right font-medium">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loadingUsers ? (
                                    <tr>
                                        <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                                            Loading...
                                        </td>
                                    </tr>
                                ) : users.length === 0 ? (
                                    <tr>
                                        <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                                            No users found
                                        </td>
                                    </tr>
                                ) : (
                                    users.map((u) => (
                                        <tr key={u.id} className="border-b last:border-0">
                                            <td className="px-4 py-3">{u.email}</td>
                                            <td className="px-4 py-3">
                                                <span className="px-2 py-0.5 bg-primary/10 text-primary rounded text-xs">
                                                    {u.role}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span
                                                    className={`px-2 py-0.5 rounded text-xs ${u.is_active
                                                            ? "bg-green-100 text-green-700"
                                                            : "bg-red-100 text-red-700"
                                                        }`}
                                                >
                                                    {u.is_active ? "Active" : "Inactive"}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-muted-foreground">
                                                {new Date(u.created_at || "").toLocaleDateString()}
                                            </td>
                                            <td className="px-4 py-3 text-right">
                                                {u.id !== user.id && (
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleDelete(u.id)}
                                                    >
                                                        Delete
                                                    </Button>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Create User Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="bg-background rounded-lg p-6 w-full max-w-md shadow-lg">
                        <h2 className="text-xl font-semibold mb-4">Create User</h2>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Email</label>
                                <input
                                    type="email"
                                    value={newEmail}
                                    onChange={(e) => setNewEmail(e.target.value)}
                                    required
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Password</label>
                                <input
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    required
                                    minLength={8}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Role</label>
                                <select
                                    value={newRole}
                                    onChange={(e) => setNewRole(e.target.value as typeof newRole)}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                >
                                    <option value="VIEWER">Viewer</option>
                                    <option value="ANALYST">Analyst</option>
                                    <option value="ADMIN">Admin</option>
                                </select>
                            </div>
                            <div className="flex justify-end gap-2 pt-4">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => setShowModal(false)}
                                >
                                    Cancel
                                </Button>
                                <Button type="submit" disabled={creating}>
                                    {creating ? "Creating..." : "Create"}
                                </Button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
