"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent } from "@/components/ui/card";

export default function LogsPage() {
  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Build Logs</h1>
        <p className="text-slate-400">View real-time build and deployment logs</p>
      </div>
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-slate-400">Select a deployment from the Deployments page to view its logs.</p>
          <a href="/dashboard/deployments" className="mt-4 text-sm text-violet-400 hover:underline">
            Go to Deployments →
          </a>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
