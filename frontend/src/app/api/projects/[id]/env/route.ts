import { NextRequest, NextResponse } from "next/server";
import { getProjectForUser, getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const project = await getProjectForUser(params.id, user.id);
  if (!project) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const environment = req.nextUrl.searchParams.get("environment") || "production";
  const vars = await prisma.environmentVariable.findMany({
    where: { projectId: params.id, environment },
  });

  return NextResponse.json({
    data: vars.map((v) => ({
      id: v.id,
      key: v.key,
      value: v.isSecret ? "*****" : v.value,
      environment: v.environment,
      is_secret: v.isSecret,
      created_at: v.createdAt.toISOString(),
    })),
    message: "success",
  });
}

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const project = await getProjectForUser(params.id, user.id);
  if (!project) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const body = await req.json();
  const v = await prisma.environmentVariable.create({
    data: {
      projectId: params.id,
      key: body.key,
      value: body.value,
      environment: body.environment || "production",
      isSecret: body.is_secret ?? true,
    },
  });

  return NextResponse.json({
    data: {
      id: v.id,
      key: v.key,
      value: v.isSecret ? "*****" : v.value,
      environment: v.environment,
      is_secret: v.isSecret,
      created_at: v.createdAt.toISOString(),
    },
    message: "success",
  });
}
