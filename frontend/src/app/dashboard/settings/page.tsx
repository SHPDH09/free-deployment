"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, User } from "@/lib/api";

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [githubConnected, setGithubConnected] = useState(false);

  useEffect(() => {
    api.get<{ data: User }>("/auth/me").then((res) => setUser(res.data));
    api.get<{ data: unknown }>("/auth/github/account")
      .then((res) => setGithubConnected(res.data !== null))
      .catch(() => setGithubConnected(false));
  }, []);

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400">Manage your account and integrations</p>
      </div>

      <div className="space-y-6 max-w-2xl">
        <Card>
          <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-400">Email</span>
              <span className="text-white">{user?.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Name</span>
              <span className="text-white">{user?.name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Role</span>
              <span className="text-white">{user?.role}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>GitHub Integration</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">
                {githubConnected ? "GitHub account connected" : "Not connected"}
              </span>
              <span className={githubConnected ? "text-emerald-400" : "text-amber-400"}>
                {githubConnected ? "Connected" : "Disconnected"}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
