import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest, mapDeployment } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const projects = await prisma.project.findMany({ where: { userId: user.id } });
  const projectIds = projects.map((p) => p.id);

  if (!projectIds.length) {
    return NextResponse.json({
      data: {
        total_projects: 0,
        successful_deployments: 0,
        failed_deployments: 0,
        active_deployments: 0,
        recent_deployments: [],
        resource_usage: {},
      },
      message: "success",
    });
  }

  const [success, failed, active, recent] = await Promise.all([
    prisma.deployment.count({ where: { projectId: { in: projectIds }, status: "success" } }),
    prisma.deployment.count({ where: { projectId: { in: projectIds }, status: "failed" } }),
    prisma.deployment.count({
      where: { projectId: { in: projectIds }, status: { in: ["pending", "building", "deploying"] } },
    }),
    prisma.deployment.findMany({
      where: { projectId: { in: projectIds } },
      orderBy: { createdAt: "desc" },
      take: 10,
    }),
  ]);

  return NextResponse.json({
    data: {
      total_projects: projects.length,
      successful_deployments: success,
      failed_deployments: failed,
      active_deployments: active,
      recent_deployments: recent.map(mapDeployment),
      resource_usage: { cpu_percent: 0, memory_mb: 0, disk_mb: 0 },
    },
    message: "success",
  });
}
