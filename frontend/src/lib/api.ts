const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T> {
  data: T;
  message: string;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem("access_token", token);
    } else {
      localStorage.removeItem("access_token");
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
    return this.token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(`${API_URL}/api${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.setToken(null);
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
      throw new Error("Unauthorized");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || error.message || "Request failed");
    }

    return response.json();
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path);
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "DELETE" });
  }
}

export const api = new ApiClient();

export interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  github_repo_full_name: string;
  default_branch: string;
  framework: string | null;
  root_directory: string;
  build_command: string | null;
  install_command: string | null;
  output_directory: string | null;
  start_command: string | null;
  node_version: string | null;
  python_version: string | null;
  deployment_type: string;
  status: string;
  is_suspended: boolean;
  active_deployment_id: string | null;
  deployment_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Deployment {
  id: string;
  project_id: string;
  version: number;
  commit_sha: string | null;
  commit_message: string | null;
  branch: string;
  author_name: string | null;
  status: string;
  build_status: string;
  deployment_status: string;
  is_production: boolean;
  is_preview: boolean;
  deployment_url: string | null;
  preview_url: string | null;
  build_duration_ms: number | null;
  deploy_duration_ms: number | null;
  total_duration_ms: number | null;
  error_message: string | null;
  health_check_status: string | null;
  triggered_by: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_projects: number;
  successful_deployments: number;
  failed_deployments: number;
  active_deployments: number;
  recent_deployments: Deployment[];
  resource_usage: Record<string, number>;
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  default_branch: string;
  html_url: string;
  description: string | null;
  language: string | null;
}

export interface Domain {
  id: string;
  project_id: string;
  domain: string;
  is_primary: boolean;
  is_verified: boolean;
  dns_records: Array<{ type: string; name: string; value: string; purpose: string }> | null;
  ssl_status: string;
  created_at: string;
}

export interface EnvVar {
  id: string;
  key: string;
  value: string | null;
  environment: string;
  is_secret: boolean;
  created_at: string;
}

export interface DeploymentLog {
  id: string;
  level: string;
  message: string;
  step: string | null;
  created_at: string;
}
