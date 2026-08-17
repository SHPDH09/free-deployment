import { NextResponse } from "next/server";

export async function GET() {
  const clientId = process.env.GITHUB_CLIENT_ID;
  if (!clientId) {
    return NextResponse.json({ detail: "GitHub OAuth not configured" }, { status: 503 });
  }

  const callback =
    process.env.GITHUB_CALLBACK_URL ||
    `${process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000"}/auth/callback`;

  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: callback,
    scope: "read:user user:email repo",
  });

  return NextResponse.json({
    url: `https://github.com/login/oauth/authorize?${params}`,
  });
}
