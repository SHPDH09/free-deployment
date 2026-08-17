import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/get-user";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const account = await prisma.gitHubAccount.findUnique({ where: { userId: user.id } });
  if (!account) {
    return NextResponse.json({ detail: "GitHub not connected" }, { status: 400 });
  }

  const res = await fetch(
    "https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner,collaborator",
    {
      headers: {
        Authorization: `Bearer ${account.accessToken}`,
        Accept: "application/vnd.github+json",
      },
    }
  );
  const repos = await res.json();

  return NextResponse.json({
    data: (repos as Array<Record<string, unknown>>).map((r) => ({
      id: r.id,
      name: r.name,
      full_name: r.full_name,
      private: r.private,
      default_branch: r.default_branch || "main",
      html_url: r.html_url,
      description: r.description,
      language: r.language,
    })),
    message: "success",
  });
}
