"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { GitHubIcon } from "@/components/icons/github";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, GitHubRepo } from "@/lib/api";

const FRAMEWORKS = [
  { id: "nextjs", name: "Next.js" },
  { id: "react", name: "React" },
  { id: "vite", name: "Vite" },
  { id: "vue", name: "Vue" },
  { id: "angular", name: "Angular" },
  { id: "nodejs", name: "Node.js" },
  { id: "fastapi", name: "FastAPI" },
  { id: "flask", name: "Flask" },
  { id: "python", name: "Python" },
  { id: "static", name: "Static HTML" },
];

export default function NewProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [branches, setBranches] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    github_repo_full_name: "",
    default_branch: "main",
    framework: "vite",
    root_directory: ".",
    build_command: "",
    install_command: "",
    output_directory: "",
    start_command: "",
    deployment_type: "static",
  });

  useEffect(() => {
    api.get<{ data: GitHubRepo[] }>("/auth/github/repos")
      .then((res) => setRepos(res.data))
      .catch(() => setError("Failed to load repositories. Connect your GitHub account."));
  }, []);

  const selectRepo = async (repo: GitHubRepo) => {
    setForm((f) => ({
      ...f,
      name: repo.name,
      github_repo_full_name: repo.full_name,
      default_branch: repo.default_branch,
    }));

    const [owner, name] = repo.full_name.split("/");
    try {
      const res = await api.get<{ data: { name: string }[] }>(
        `/auth/github/repos/${owner}/${name}/branches`
      );
      setBranches(res.data.map((b) => b.name));
    } catch {
      setBranches([repo.default_branch]);
    }
    setStep(2);
  };

  const selectFramework = (frameworkId: string) => {
    setForm((f) => ({ ...f, framework: frameworkId }));
    setStep(3);
  };

  const handleDeploy = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<{ data: { id: string } }>("/projects", {
        name: form.name,
        github_repo_full_name: form.github_repo_full_name,
        default_branch: form.default_branch,
        framework: form.framework,
        root_directory: form.root_directory,
        build_command: form.build_command || undefined,
        install_command: form.install_command || undefined,
        output_directory: form.output_directory || undefined,
        start_command: form.start_command || undefined,
        deployment_type: form.deployment_type,
      });

      await api.post(`/projects/${res.data.id}/deploy`);
      router.push(`/dashboard/projects/${res.data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">New Project</h1>
        <p className="text-slate-400">Set up a new deployment from GitHub</p>
      </div>

      <div className="mb-8 flex items-center gap-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
                step >= s ? "bg-violet-600 text-white" : "bg-slate-800 text-slate-500"
              }`}
            >
              {s}
            </div>
            {s < 3 && <ChevronRight className="h-4 w-4 text-slate-600" />}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitHubIcon className="h-5 w-5" />
              Select Repository
            </CardTitle>
            <CardDescription>Choose a GitHub repository to deploy</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {repos.map((repo) => (
                <button
                  key={repo.id}
                  onClick={() => selectRepo(repo)}
                  className="flex w-full items-center justify-between rounded-lg border border-slate-800 p-4 text-left hover:border-violet-500/50 hover:bg-slate-800/50"
                >
                  <div>
                    <p className="font-medium text-white">{repo.full_name}</p>
                    <p className="text-sm text-slate-500">{repo.description || "No description"}</p>
                  </div>
                  <span className="text-xs text-slate-500">{repo.language}</span>
                </button>
              ))}
              {repos.length === 0 && (
                <p className="text-center text-slate-500 py-8">No repositories found</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Select Framework</CardTitle>
            <CardDescription>Choose your project framework for automatic configuration</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {FRAMEWORKS.map((fw) => (
                <button
                  key={fw.id}
                  onClick={() => selectFramework(fw.id)}
                  className="rounded-lg border border-slate-800 p-4 text-left hover:border-violet-500/50 hover:bg-slate-800/50"
                >
                  <p className="font-medium text-white">{fw.name}</p>
                </button>
              ))}
            </div>
            <Button variant="ghost" className="mt-4" onClick={() => setStep(1)}>Back</Button>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Configure Project</CardTitle>
            <CardDescription>Fine-tune build settings or deploy with defaults</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1 block text-sm text-slate-400">Project Name</label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Branch</label>
              <select
                value={form.default_branch}
                onChange={(e) => setForm({ ...form, default_branch: e.target.value })}
                className="flex h-10 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
              >
                {branches.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Root Directory</label>
              <Input value={form.root_directory} onChange={(e) => setForm({ ...form, root_directory: e.target.value })} />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Install Command</label>
              <Input value={form.install_command} onChange={(e) => setForm({ ...form, install_command: e.target.value })} placeholder="npm install" />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Build Command</label>
              <Input value={form.build_command} onChange={(e) => setForm({ ...form, build_command: e.target.value })} placeholder="npm run build" />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Output Directory</label>
              <Input value={form.output_directory} onChange={(e) => setForm({ ...form, output_directory: e.target.value })} placeholder="dist" />
            </div>
            <div className="flex gap-3 pt-4">
              <Button variant="ghost" onClick={() => setStep(2)}>Back</Button>
              <Button onClick={handleDeploy} disabled={loading}>
                {loading ? "Creating..." : "Create & Deploy"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </DashboardLayout>
  );
}
