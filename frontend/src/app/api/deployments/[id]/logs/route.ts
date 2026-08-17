import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const deployment = await prisma.deployment.findFirst({
    where: { id: params.id, project: { userId: user.id } },
  });
  if (!deployment) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const logs = await prisma.deploymentLog.findMany({
    where: { deploymentId: params.id },
    orderBy: { createdAt: "asc" },
    take: 500,
  });

  return NextResponse.json({
    data: logs.map((l) => ({
      id: l.id,
      level: l.level,
      message: l.message,
      step: l.step,
      created_at: l.createdAt.toISOString(),
    })),
    message: "success",
  });
}
