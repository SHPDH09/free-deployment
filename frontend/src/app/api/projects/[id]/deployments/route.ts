import { NextRequest, NextResponse } from "next/server";
import { getProjectForUser, getUserFromRequest, mapDeployment } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const project = await getProjectForUser(params.id, user.id);
  if (!project) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const deployments = await prisma.deployment.findMany({
    where: { projectId: params.id },
    orderBy: { createdAt: "desc" },
    take: 50,
  });

  return NextResponse.json({
    data: deployments.map(mapDeployment),
    message: "success",
  });
}
