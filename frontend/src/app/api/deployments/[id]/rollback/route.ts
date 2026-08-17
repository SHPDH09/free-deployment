import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest, mapDeployment } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const deployment = await prisma.deployment.findFirst({
    where: { id: params.id, project: { userId: user.id }, status: "success" },
  });
  if (!deployment) {
    return NextResponse.json({ detail: "Can only rollback to successful deployment" }, { status: 400 });
  }

  await prisma.project.update({
    where: { id: deployment.projectId },
    data: { activeDeploymentId: deployment.id },
  });

  return NextResponse.json({ data: mapDeployment(deployment), message: "success" });
}
