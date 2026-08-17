import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  if (user.role !== "admin") return NextResponse.json({ detail: "Admin required" }, { status: 403 });

  const [users, projects, deployments, failed] = await Promise.all([
    prisma.user.count(),
    prisma.project.count(),
    prisma.deployment.count(),
    prisma.deployment.count({ where: { status: "failed" } }),
  ]);

  return NextResponse.json({
    data: {
      total_users: users,
      total_projects: projects,
      total_deployments: deployments,
      active_containers: 0,
      build_workers: 0,
      failed_deployments_24h: failed,
      system_cpu: null,
      system_memory: null,
      system_disk: null,
    },
    message: "success",
  });
}
