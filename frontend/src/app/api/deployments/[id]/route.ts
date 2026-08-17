import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest, mapDeployment } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

async function getDeploymentForUser(deploymentId: string, userId: string) {
  return prisma.deployment.findFirst({
    where: { id: deploymentId, project: { userId } },
  });
}

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const deployment = await getDeploymentForUser(params.id, user.id);
  if (!deployment) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  return NextResponse.json({ data: mapDeployment(deployment), message: "success" });
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const deployment = await getDeploymentForUser(params.id, user.id);
  if (!deployment) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  await prisma.deployment.delete({ where: { id: params.id } });
  return NextResponse.json({ data: { deleted: true }, message: "success" });
}
