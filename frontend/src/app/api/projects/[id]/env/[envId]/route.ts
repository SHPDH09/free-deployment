import { NextRequest, NextResponse } from "next/server";
import { getProjectForUser, getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string; envId: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const project = await getProjectForUser(params.id, user.id);
  if (!project) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  await prisma.environmentVariable.deleteMany({
    where: { id: params.envId, projectId: params.id },
  });

  return NextResponse.json({ data: { deleted: true }, message: "success" });
}
