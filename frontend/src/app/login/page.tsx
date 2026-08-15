"use client";

import { useEffect } from "react";
import { GitHubIcon } from "@/components/icons/github";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function LoginPage() {
  useEffect(() => {
    if (api.getToken()) {
      window.location.href = "/dashboard";
    }
  }, []);

  const handleGitHubLogin = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/github`
      );
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch {
      alert("Failed to initiate GitHub login. Ensure the API is running and GitHub OAuth is configured.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
            <GitHubIcon className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Welcome to DeployStack</h1>
          <p className="mt-2 text-sm text-slate-400">
            Sign in with GitHub to deploy your projects
          </p>
        </div>

        <Button onClick={handleGitHubLogin} className="w-full gap-2" size="lg">
          <GitHubIcon className="h-5 w-5" />
          Continue with GitHub
        </Button>

        <p className="mt-6 text-center text-xs text-slate-500">
          By signing in, you authorize DeployStack to access your repositories for deployment.
        </p>
      </div>
    </div>
  );
}
