"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Box, CheckCircle2, Clock, Rocket, XCircle } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, DashboardStats, Deployment } from "@/lib/api";
import { formatDate, formatDuration } from "@/lib/utils";

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: number;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-6">
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${color}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ data: DashboardStats }>("/dashboard/stats")
      .then((res) => setStats(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="text-slate-400">Loading dashboard...</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Overview</h1>
        <p className="text-slate-400">Monitor your deployments and platform activity</p>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Projects" value={stats?.total_projects || 0} icon={Box} color="bg-violet-500/15 text-violet-400" />
        <StatCard title="Successful Deployments" value={stats?.successful_deployments || 0} icon={CheckCircle2} color="bg-emerald-500/15 text-emerald-400" />
        <StatCard title="Failed Deployments" value={stats?.failed_deployments || 0} icon={XCircle} color="bg-red-500/15 text-red-400" />
        <StatCard title="Active Deployments" value={stats?.active_deployments || 0} icon={Clock} color="bg-amber-500/15 text-amber-400" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Deployments</CardTitle>
            <Link href="/dashboard/deployments">
              <Button variant="ghost" size="sm">View all</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {stats?.recent_deployments?.length === 0 ? (
              <div className="py-8 text-center">
                <Rocket className="mx-auto mb-3 h-8 w-8 text-slate-600" />
                <p className="text-sm text-slate-400">No deployments yet</p>
                <Link href="/dashboard/projects/new">
                  <Button className="mt-4" size="sm">Create a project</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {stats?.recent_deployments?.map((d: Deployment) => (
                  <Link
                    key={d.id}
                    href={`/dashboard/deployments/${d.id}`}
                    className="flex items-center justify-between rounded-lg border border-slate-800 p-3 hover:bg-slate-800/50"
                  >
                    <div>
                      <p className="text-sm font-medium text-white">v{d.version}</p>
                      <p className="text-xs text-slate-500">{formatDate(d.created_at)}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500">{formatDuration(d.total_duration_ms)}</span>
                      <StatusBadge status={d.status} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resource Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { label: "CPU", value: stats?.resource_usage?.cpu_percent || 0, max: 100, unit: "%" },
                { label: "Memory", value: stats?.resource_usage?.memory_mb || 0, max: 2048, unit: "MB" },
                { label: "Disk", value: stats?.resource_usage?.disk_mb || 0, max: 10000, unit: "MB" },
              ].map((item) => (
                <div key={item.label}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-slate-400">{item.label}</span>
                    <span className="text-slate-300">{item.value}{item.unit}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-800">
                    <div
                      className="h-2 rounded-full bg-violet-600"
                      style={{ width: `${Math.min((item.value / item.max) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
