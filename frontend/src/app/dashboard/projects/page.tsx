"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Rocket, ExternalLink } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/badge";
import { api, Project } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ data: Project[] }>("/projects")
      .then((res) => setProjects(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-slate-400">Manage your deployed applications</p>
        </div>
        <Link href="/dashboard/projects/new">
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            New Project
          </Button>
        </Link>
      </div>

      {loading ? (
        <p className="text-slate-400">Loading projects...</p>
      ) : projects.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Rocket className="mx-auto mb-4 h-12 w-12 text-slate-600" />
            <h3 className="text-lg font-semibold text-white">No projects yet</h3>
            <p className="mt-2 text-sm text-slate-400">
              Connect a GitHub repository to start deploying
            </p>
            <Link href="/dashboard/projects/new">
              <Button className="mt-6 gap-2">
                <Plus className="h-4 w-4" />
                Create your first project
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link key={project.id} href={`/dashboard/projects/${project.id}`}>
              <Card className="transition-colors hover:border-violet-500/50">
                <CardContent className="p-6">
                  <div className="mb-4 flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-white">{project.name}</h3>
                      <p className="text-xs text-slate-500">{project.github_repo_full_name}</p>
                    </div>
                    <StatusBadge status={project.status} />
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Framework</span>
                      <span className="text-slate-300">{project.framework || "—"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Branch</span>
                      <span className="text-slate-300">{project.default_branch}</span>
                    </div>
                    {project.deployment_url && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">URL</span>
                        <a
                          href={project.deployment_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-violet-400 hover:underline"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <span className="truncate max-w-[150px]">{project.slug}</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    )}
                  </div>
                  <p className="mt-4 text-xs text-slate-600">
                    Updated {formatDate(project.updated_at)}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
