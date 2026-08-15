"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, EnvVar, Project } from "@/lib/api";

export default function EnvPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [envVars, setEnvVars] = useState<EnvVar[]>([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");

  useEffect(() => {
    api.get<{ data: Project[] }>("/projects").then((res) => {
      setProjects(res.data);
      if (res.data.length > 0) {
        setSelectedProject(res.data[0].id);
        loadEnv(res.data[0].id);
      }
    });
  }, []);

  const loadEnv = (projectId: string) => {
    api.get<{ data: EnvVar[] }>(`/projects/${projectId}/env`).then((res) => setEnvVars(res.data));
  };

  const addVar = async () => {
    if (!selectedProject || !key) return;
    try {
      await api.post(`/projects/${selectedProject}/env`, { key, value, environment: "production", is_secret: true });
      setKey("");
      setValue("");
      loadEnv(selectedProject);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to add variable");
    }
  };

  const deleteVar = async (envId: string) => {
    await api.delete(`/projects/${selectedProject}/env/${envId}`);
    loadEnv(selectedProject);
  };

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Environment Variables</h1>
        <p className="text-slate-400">Configure secrets and config for your projects</p>
      </div>

      <Card className="mb-6">
        <CardContent className="p-4">
          <select
            value={selectedProject}
            onChange={(e) => { setSelectedProject(e.target.value); loadEnv(e.target.value); }}
            className="h-10 rounded-lg border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader><CardTitle>Add Variable</CardTitle></CardHeader>
        <CardContent className="flex gap-3">
          <Input placeholder="KEY" value={key} onChange={(e) => setKey(e.target.value)} />
          <Input placeholder="Value" type="password" value={value} onChange={(e) => setValue(e.target.value)} />
          <Button onClick={addVar}>Add</Button>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
                <th className="p-4">Key</th>
                <th className="p-4">Value</th>
                <th className="p-4">Environment</th>
                <th className="p-4"></th>
              </tr>
            </thead>
            <tbody>
              {envVars.map((v) => (
                <tr key={v.id} className="border-b border-slate-800/50">
                  <td className="p-4 font-mono text-sm text-white">{v.key}</td>
                  <td className="p-4 font-mono text-sm text-slate-500">{v.value || "*****"}</td>
                  <td className="p-4 text-sm text-slate-400">{v.environment}</td>
                  <td className="p-4">
                    <Button variant="ghost" size="sm" onClick={() => deleteVar(v.id)}>Delete</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
