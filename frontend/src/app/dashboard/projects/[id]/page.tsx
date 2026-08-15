"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ExternalLink, Rocket, RotateCcw, Settings } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/badge";
import { api, Deployment, Project } from "@/lib/api";
import { formatDate, formatDuration } from "@/lib/utils";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [deploying, setDeploying] = useState(false);

  const load = () => {
    api.get<{ data: Project }>(`/projects/${projectId}`).then((res) => setProject(res.data));
    api.get<{ data: Deployment[] }>(`/projects/${projectId}/deployments`).then((res) => setDeployments(res.data));
  };

  useEffect(() => { load(); }, [projectId]);

  const handleDeploy = async () => {
    setDeploying(true);
    try {
      await api.post(`/projects/${projectId}/deploy`);
      load();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Deploy failed");
    } finally {
      setDeploying(false);
    }
  };

  const handleRollback = async (deploymentId: string) => {
    if (!confirm("Rollback to this deployment?")) return;
    try {
      await api.post(`/deployments/${deploymentId}/rollback`);
      load();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Rollback failed");
    }
  };

  if (!project) {
    return (
      <DashboardLayout>
        <p className="text-slate-400">Loading project...</p>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{project.name}</h1>
          <p className="text-slate-400">{project.github_repo_full_name}</p>
        </div>
        <div className="flex gap-3">
          <Link href={`/dashboard/projects/${projectId}/settings`}>
            <Button variant="outline" className="gap-2">
              <Settings className="h-4 w-4" />
              Settings
            </Button>
          </Link>
          <Button onClick={handleDeploy} disabled={deploying} className="gap-2">
            <Rocket className="h-4 w-4" />
            {deploying ? "Deploying..." : "Deploy"}
          </Button>
        </div>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Framework</p>
            <p className="font-medium text-white">{project.framework || "—"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Branch</p>
            <p className="font-medium text-white">{project.default_branch}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Type</p>
            <p className="font-medium text-white">{project.deployment_type}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-slate-500">Status</p>
            <StatusBadge status={project.status} />
          </CardContent>
        </Card>
      </div>

      {project.deployment_url && (
        <Card className="mb-8">
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-slate-400">Production URL</p>
              <a
                href={project.deployment_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-violet-400 hover:underline"
              >
                {project.deployment_url}
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Deployment History</CardTitle>
        </CardHeader>
        <CardContent>
          {deployments.length === 0 ? (
            <p className="py-8 text-center text-slate-500">No deployments yet</p>
          ) : (
            <div className="space-y-2">
              {deployments.map((d) => (
                <div
                  key={d.id}
                  className="flex items-center justify-between rounded-lg border border-slate-800 p-4"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <Link href={`/dashboard/deployments/${d.id}`} className="font-medium text-white hover:text-violet-400">
                        v{d.version}
                      </Link>
                      <p className="text-xs text-slate-500">
                        {d.commit_message?.slice(0, 60) || d.branch} · {formatDate(d.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500">{formatDuration(d.total_duration_ms)}</span>
                    <StatusBadge status={d.status} />
                    {d.status === "success" && (
                      <Button variant="ghost" size="sm" onClick={() => handleRollback(d.id)}>
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
