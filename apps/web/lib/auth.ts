/**
 * Authentication API client
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
    id: string;
    email: string;
    role: "ADMIN" | "ANALYST" | "VIEWER";
    tenant_id: string;
    is_active: boolean;
    created_at?: string;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface LoginResponse {
    message: string;
    user_id: string;
    email: string;
    role: string;
}

export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
        credentials: "include", // Important: include cookies
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Login failed");
    }

    return response.json();
}

export async function logout(): Promise<void> {
    const response = await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Logout failed");
    }
}

export async function getMe(): Promise<User | null> {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            credentials: "include",
        });

        if (!response.ok) {
            return null;
        }

        return response.json();
    } catch {
        return null;
    }
}

// Users API (Admin only)
export interface CreateUserRequest {
    email: string;
    password: string;
    role: "ADMIN" | "ANALYST" | "VIEWER";
}

export async function getUsers(): Promise<User[]> {
    const response = await fetch(`${API_URL}/users`, {
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to fetch users");
    }

    return response.json();
}

export async function createUser(data: CreateUserRequest): Promise<User> {
    const response = await fetch(`${API_URL}/users`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create user");
    }

    return response.json();
}

export async function deleteUser(userId: string): Promise<void> {
    const response = await fetch(`${API_URL}/users/${userId}`, {
        method: "DELETE",
        credentials: "include",
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete user");
    }
}
