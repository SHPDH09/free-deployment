"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

export default function AuthCallbackPage() {
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setError("No authorization code received");
      return;
    }

    fetch(`/api/auth/github/callback?code=${encodeURIComponent(code)}`, {
      method: "POST",
    })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Authentication failed");
        }
        return res.json();
      })
      .then((data) => {
        api.setToken(data.access_token);
        window.location.href = "/dashboard";
      })
      .catch((err) => setError(err.message));
  }, [searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950">
      <div className="text-center">
        {error ? (
          <>
            <p className="text-red-400">{error}</p>
            <a href="/login" className="mt-4 text-sm text-violet-400 hover:underline">
              Back to login
            </a>
          </>
        ) : (
          <p className="text-slate-400">Completing sign in...</p>
        )}
      </div>
    </div>
  );
}
