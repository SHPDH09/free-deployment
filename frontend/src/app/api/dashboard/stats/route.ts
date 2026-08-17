import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/get-user";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const projects = await prisma.project.findMany({ where: { userId: user.id } });
  const projectIds = projects.map((p) => p.id);

  const [success, failed, active, recent] = await Promise.all([
    prisma.deployment.count({
      where: { projectId: { in: projectIds }, status: "success" },
    }),
    prisma.deployment.count({
      where: { projectId: { in: projectIds }, status: "failed" },
    }),
    prisma.deployment.count({
      where: { projectId: { in: projectIds }, status: { in: ["pending", "building"] } },
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
      recent_deployments: recent.map((d) => ({
        id: d.id,
        project_id: d.projectId,
        version: d.version,
        status: d.status,
        branch: d.branch,
        deployment_url: d.deploymentUrl,
        created_at: d.createdAt.toISOString(),
      })),
      resource_usage: {},
    },
    message: "success",
  });
}
