import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const account = await prisma.gitHubAccount.findUnique({ where: { userId: user.id } });
  if (!account) return NextResponse.json({ data: null, message: "No GitHub account" });

  return NextResponse.json({
    data: {
      github_username: account.githubUsername,
      scopes: account.scopes,
      created_at: account.createdAt.toISOString(),
    },
    message: "success",
  });
}
