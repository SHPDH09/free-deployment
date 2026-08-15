"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/badge";
import { api, Deployment, Project } from "@/lib/api";
import { formatDate, formatDuration } from "@/lib/utils";

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [projects, setProjects] = useState<Record<string, Project>>({});

  useEffect(() => {
    api.get<{ data: Project[] }>("/projects").then(async (res) => {
      const projectMap: Record<string, Project> = {};
      res.data.forEach((p) => { projectMap[p.id] = p; });
      setProjects(projectMap);

      const allDeployments: Deployment[] = [];
      for (const project of res.data) {
        try {
          const depRes = await api.get<{ data: Deployment[] }>(`/projects/${project.id}/deployments`);
          allDeployments.push(...depRes.data);
        } catch {
          // skip
        }
      }
      allDeployments.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setDeployments(allDeployments);
    });
  }, []);

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Deployments</h1>
        <p className="text-slate-400">All deployment activity across projects</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
                <th className="p-4">Project</th>
                <th className="p-4">Version</th>
                <th className="p-4">Branch</th>
                <th className="p-4">Status</th>
                <th className="p-4">Duration</th>
                <th className="p-4">Date</th>
              </tr>
            </thead>
            <tbody>
              {deployments.map((d) => (
                <tr key={d.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="p-4">
                    <Link href={`/dashboard/projects/${d.project_id}`} className="text-sm text-white hover:text-violet-400">
                      {projects[d.project_id]?.name || "—"}
                    </Link>
                  </td>
                  <td className="p-4">
                    <Link href={`/dashboard/deployments/${d.id}`} className="text-sm text-violet-400 hover:underline">
                      v{d.version}
                    </Link>
                  </td>
                  <td className="p-4 text-sm text-slate-400">{d.branch}</td>
                  <td className="p-4"><StatusBadge status={d.status} /></td>
                  <td className="p-4 text-sm text-slate-400">{formatDuration(d.total_duration_ms)}</td>
                  <td className="p-4 text-sm text-slate-400">{formatDate(d.created_at)}</td>
                </tr>
              ))}
              {deployments.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500">No deployments yet</td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
