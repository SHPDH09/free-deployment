import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/get-user";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  return NextResponse.json({
    data: {
      id: user.id,
      email: user.email,
      name: user.name,
      avatar_url: user.avatarUrl,
      role: user.role,
      is_active: user.isActive,
      created_at: user.createdAt.toISOString(),
    },
    message: "success",
  });
}
