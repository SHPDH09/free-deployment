import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(
  req: NextRequest,
  { params }: { params: { owner: string; repo: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const account = await prisma.gitHubAccount.findUnique({ where: { userId: user.id } });
  if (!account) return NextResponse.json({ detail: "GitHub not connected" }, { status: 400 });

  const res = await fetch(
    `https://api.github.com/repos/${params.owner}/${params.repo}/branches`,
    {
      headers: {
        Authorization: `Bearer ${account.accessToken}`,
        Accept: "application/vnd.github+json",
      },
    }
  );
  const branches = await res.json();

  return NextResponse.json({
    data: (branches as Array<{ name: string }>).map((b) => ({ name: b.name })),
    message: "success",
  });
}
