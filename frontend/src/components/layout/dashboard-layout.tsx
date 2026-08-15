"use client";

import { useEffect, useState } from "react";
import { api, User } from "@/lib/api";
import { Sidebar } from "@/components/layout/sidebar";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.get<{ data: User }>("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => {
        window.location.href = "/login";
      });
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-950">
      <Sidebar userRole={user?.role} />
      <main className="flex-1 overflow-auto">
        <div className="border-b border-slate-800 bg-slate-950/80 px-8 py-4">
          <div className="flex items-center justify-between">
            <div />
            {user && (
              <div className="flex items-center gap-3">
                {user.avatar_url && (
                  <img src={user.avatar_url} alt="" className="h-8 w-8 rounded-full" />
                )}
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-200">{user.name || user.email}</p>
                  <p className="text-xs text-slate-500">{user.role}</p>
                </div>
              </div>
            )}
          </div>
        </div>
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
