import { NextRequest, NextResponse } from "next/server";
import {
  getProjectForUser,
  getUserFromRequest,
  mapProject,
} from "@/lib/server-utils";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const project = await getProjectForUser(params.id, user.id);
  if (!project) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  return NextResponse.json({ data: mapProject(project), message: "success" });
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const project = await getProjectForUser(params.id, user.id);
  if (!project) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const { prisma } = await import("@/lib/prisma");
  await prisma.project.delete({ where: { id: params.id } });

  return NextResponse.json({ data: { deleted: true }, message: "success" });
}
