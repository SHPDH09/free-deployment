import { NextRequest, NextResponse } from "next/server";
import { signToken } from "@/lib/auth-server";
import { prisma } from "@/lib/prisma";

export async function POST(req: NextRequest) {
  const code = req.nextUrl.searchParams.get("code");
  if (!code) {
    return NextResponse.json({ detail: "No code" }, { status: 400 });
  }

  const clientId = process.env.GITHUB_CLIENT_ID!;
  const clientSecret = process.env.GITHUB_CLIENT_SECRET!;
  const tokenRes = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: { Accept: "application/json" },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      code,
    }),
  });
  const tokenData = await tokenRes.json();
  const accessToken = tokenData.access_token;
  if (!accessToken) {
    return NextResponse.json({ detail: "OAuth failed" }, { status: 400 });
  }

  const userRes = await fetch("https://api.github.com/user", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: "application/vnd.github+json",
    },
  });
  const ghUser = await userRes.json();
  const email = ghUser.email || `${ghUser.login}@users.noreply.github.com`;

  let user = await prisma.user.findUnique({ where: { email } });
  if (!user) {
    const isAdmin = process.env.ADMIN_EMAIL && email === process.env.ADMIN_EMAIL;
    user = await prisma.user.create({
      data: {
        email,
        name: ghUser.name || ghUser.login,
        avatarUrl: ghUser.avatar_url,
        role: isAdmin ? "admin" : "user",
      },
    });
  }

  await prisma.gitHubAccount.upsert({
    where: { userId: user.id },
    create: {
      userId: user.id,
      githubId: String(ghUser.id),
      githubUsername: ghUser.login,
      accessToken,
    },
    update: {
      githubId: String(ghUser.id),
      githubUsername: ghUser.login,
      accessToken,
    },
  });

  const jwt = await signToken({ sub: user.id });

  return NextResponse.json({
    access_token: jwt,
    token_type: "bearer",
    user: {
      id: user.id,
      email: user.email,
      name: user.name,
      avatar_url: user.avatarUrl,
      role: user.role,
    },
  });
}
