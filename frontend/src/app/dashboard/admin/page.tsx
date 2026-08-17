"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface AdminStats {
  total_users: number;
  total_projects: number;
  total_deployments: number;
  active_containers: number;
  build_workers: number;
  failed_deployments_24h: number;
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<Array<{ id: string; email: string; role: string }>>([]);

  useEffect(() => {
    api.get<{ data: AdminStats }>("/admin/stats").then((res) => setStats(res.data)).catch(console.error);
    api.get<{ data: Array<{ id: string; email: string; role: string }> }>("/admin/users")
      .then((res) => setUsers(res.data))
      .catch(console.error);
  }, []);

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
        <p className="text-slate-400">Platform administration and monitoring</p>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-3 lg:grid-cols-6">
        {[
          { label: "Users", value: stats?.total_users },
          { label: "Projects", value: stats?.total_projects },
          { label: "Deployments", value: stats?.total_deployments },
          { label: "Workers", value: stats?.build_workers },
          { label: "Containers", value: stats?.active_containers },
          { label: "Failed (24h)", value: stats?.failed_deployments_24h },
        ].map((item) => (
          <Card key={item.label}>
            <CardContent className="p-4">
              <p className="text-xs text-slate-500">{item.label}</p>
              <p className="text-2xl font-bold text-white">{item.value ?? "—"}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle>Users</CardTitle></CardHeader>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
                <th className="p-4">Email</th>
                <th className="p-4">Role</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-slate-800/50">
                  <td className="p-4 text-sm text-white">{u.email}</td>
                  <td className="p-4"><StatusBadge status={u.role === "admin" ? "success" : "default"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
