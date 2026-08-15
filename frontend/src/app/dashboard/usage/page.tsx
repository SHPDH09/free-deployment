"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, DashboardStats } from "@/lib/api";

export default function UsagePage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    api.get<{ data: DashboardStats }>("/dashboard/stats").then((res) => setStats(res.data));
  }, []);

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Usage</h1>
        <p className="text-slate-400">Resource usage and deployment metrics</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Deployment Metrics</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-slate-400">Total Projects</span>
              <span className="text-white">{stats?.total_projects || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Successful Deployments</span>
              <span className="text-emerald-400">{stats?.successful_deployments || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Failed Deployments</span>
              <span className="text-red-400">{stats?.failed_deployments || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Active Deployments</span>
              <span className="text-amber-400">{stats?.active_deployments || 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Resource Limits</CardTitle></CardHeader>
          <CardContent className="space-y-4 text-sm text-slate-400">
            <p>Build timeout: 600 seconds</p>
            <p>Max build memory: 2048 MB</p>
            <p>Max deployment size: 500 MB</p>
            <p>Max projects per user: 20</p>
            <p>Max concurrent builds: 3</p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
