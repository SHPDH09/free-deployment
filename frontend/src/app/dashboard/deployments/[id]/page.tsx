"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/badge";
import { api, Deployment, DeploymentLog } from "@/lib/api";
import { formatDate, formatDuration } from "@/lib/utils";

export default function DeploymentDetailPage() {
  const params = useParams();
  const deploymentId = params.id as string;
  const [deployment, setDeployment] = useState<Deployment | null>(null);
  const [logs, setLogs] = useState<DeploymentLog[]>([]);

  useEffect(() => {
    api.get<{ data: Deployment }>(`/deployments/${deploymentId}`).then((res) => setDeployment(res.data));
    api.get<{ data: DeploymentLog[] }>(`/deployments/${deploymentId}/logs`).then((res) => setLogs(res.data));

    const token = localStorage.getItem("access_token");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const ws = new WebSocket(`${apiUrl.replace("http", "ws")}/api/deployments/${deploymentId}/logs/stream?token=${token}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLogs((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          level: data.level,
          message: data.message,
          step: data.step,
          created_at: data.timestamp,
        },
      ]);
    };

    return () => ws.close();
  }, [deploymentId]);

  if (!deployment) {
    return (
      <DashboardLayout>
        <p className="text-slate-400">Loading deployment...</p>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="mb-8">
        <Link href={`/dashboard/projects/${deployment.project_id}`} className="text-sm text-violet-400 hover:underline">
          ← Back to project
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-white">Deployment v{deployment.version}</h1>
        <div className="mt-2 flex items-center gap-3">
          <StatusBadge status={deployment.status} />
          <span className="text-sm text-slate-500">{formatDate(deployment.created_at)}</span>
          <span className="text-sm text-slate-500">{formatDuration(deployment.total_duration_ms)}</span>
        </div>
      </div>

      {deployment.error_message && (
        <Card className="mb-6 border-red-500/30">
          <CardContent className="p-4">
            <p className="text-sm font-medium text-red-400">Deployment Failed</p>
            <pre className="mt-2 text-sm text-slate-300 whitespace-pre-wrap">{deployment.error_message}</pre>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <div className="bg-slate-950 p-4 font-mono text-sm max-h-[600px] overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-slate-500">Waiting for logs...</p>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="flex gap-3 py-0.5">
                  <span className="text-slate-600 shrink-0">
                    [{new Date(log.created_at).toLocaleTimeString()}]
                  </span>
                  <span className={
                    log.level === "error" ? "text-red-400" :
                    log.level === "warning" ? "text-amber-400" : "text-slate-300"
                  }>
                    {log.message}
                  </span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
