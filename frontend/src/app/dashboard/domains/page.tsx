"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/badge";
import { api, Domain, Project } from "@/lib/api";

export default function DomainsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [newDomain, setNewDomain] = useState("");
  const [selectedProject, setSelectedProject] = useState("");

  useEffect(() => {
    api.get<{ data: Project[] }>("/projects").then(async (res) => {
      setProjects(res.data);
      if (res.data.length > 0) setSelectedProject(res.data[0].id);
      const all: Domain[] = [];
      for (const p of res.data) {
        try {
          const d = await api.get<{ data: Domain[] }>(`/projects/${p.id}/domains`);
          all.push(...d.data);
        } catch { /* skip */ }
      }
      setDomains(all);
    });
  }, []);

  const addDomain = async () => {
    if (!selectedProject || !newDomain) return;
    try {
      await api.post(`/projects/${selectedProject}/domains`, { domain: newDomain });
      setNewDomain("");
      const d = await api.get<{ data: Domain[] }>(`/projects/${selectedProject}/domains`);
      setDomains((prev) => [...prev.filter((x) => x.project_id !== selectedProject), ...d.data]);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to add domain");
    }
  };

  const verifyDomain = async (domainId: string) => {
    try {
      const res = await api.post<{ data: Domain }>(`/domains/${domainId}/verify`);
      setDomains((prev) => prev.map((d) => d.id === domainId ? res.data : d));
    } catch (err) {
      alert(err instanceof Error ? err.message : "Verification failed");
    }
  };

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Domains</h1>
        <p className="text-slate-400">Manage custom domains for your projects</p>
      </div>

      <Card className="mb-8">
        <CardHeader><CardTitle>Add Custom Domain</CardTitle></CardHeader>
        <CardContent className="flex gap-3">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="h-10 rounded-lg border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <Input placeholder="www.example.com" value={newDomain} onChange={(e) => setNewDomain(e.target.value)} />
          <Button onClick={addDomain}>Add Domain</Button>
        </CardContent>
      </Card>

      <div className="space-y-4">
        {domains.map((domain) => (
          <Card key={domain.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-white">{domain.domain}</p>
                  <div className="mt-1 flex gap-2">
                    <StatusBadge status={domain.is_verified ? "success" : "pending"} />
                    <StatusBadge status={domain.ssl_status === "active" ? "success" : "pending"} />
                  </div>
                </div>
                {!domain.is_verified && (
                  <Button size="sm" onClick={() => verifyDomain(domain.id)}>Verify DNS</Button>
                )}
              </div>
              {domain.dns_records && !domain.is_verified && (
                <div className="mt-4 rounded-lg bg-slate-950 p-4">
                  <p className="mb-2 text-xs text-slate-500">DNS Configuration</p>
                  {(domain.dns_records as Array<{ type: string; name: string; value: string }>).map((r) => (
                    <div key={r.name} className="text-sm">
                      <span className="text-violet-400">{r.type}</span>
                      <span className="text-slate-500"> {r.name} → </span>
                      <span className="text-slate-300">{r.value}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
        {domains.length === 0 && (
          <p className="text-center text-slate-500 py-8">No custom domains configured</p>
        )}
      </div>
    </DashboardLayout>
  );
}
