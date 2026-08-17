import { NextRequest, NextResponse } from "next/server";
import { getProjectForUser, getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";
import { randomBytes } from "crypto";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const project = await getProjectForUser(params.id, user.id);
  if (!project) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const domains = await prisma.domain.findMany({ where: { projectId: params.id } });
  return NextResponse.json({
    data: domains.map((d) => ({
      id: d.id,
      project_id: d.projectId,
      domain: d.domain,
      is_primary: false,
      is_verified: d.isVerified,
      dns_records: d.dnsRecords,
      ssl_status: d.sslStatus,
      created_at: d.createdAt.toISOString(),
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
  const token = randomBytes(16).toString("hex");
  const platform = process.env.PLATFORM_DOMAIN || process.env.VERCEL_URL || "vercel.app";

  const domain = await prisma.domain.create({
    data: {
      projectId: params.id,
      domain: body.domain,
      verificationToken: token,
      dnsRecords: [
        { type: "CNAME", name: body.domain, value: `cname.${platform}`, purpose: "Point to platform" },
        { type: "TXT", name: `_deploystack.${body.domain}`, value: token, purpose: "Verify ownership" },
      ],
    },
  });

  return NextResponse.json({
    data: {
      id: domain.id,
      project_id: domain.projectId,
      domain: domain.domain,
      is_primary: false,
      is_verified: domain.isVerified,
      dns_records: domain.dnsRecords,
      ssl_status: domain.sslStatus,
      created_at: domain.createdAt.toISOString(),
    },
    message: "success",
  });
}
