import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  if (user.role !== "admin") return NextResponse.json({ detail: "Admin required" }, { status: 403 });

  const users = await prisma.user.findMany({
    orderBy: { createdAt: "desc" },
    take: 100,
  });

  return NextResponse.json({
    data: users.map((u) => ({
      id: u.id,
      email: u.email,
      name: u.name,
      avatar_url: u.avatarUrl,
      role: u.role,
      is_active: u.isActive,
      created_at: u.createdAt.toISOString(),
    })),
    message: "success",
  });
}
