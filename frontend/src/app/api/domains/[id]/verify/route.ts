import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const domain = await prisma.domain.findFirst({
    where: { id: params.id, project: { userId: user.id } },
  });
  if (!domain) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const updated = await prisma.domain.update({
    where: { id: params.id },
    data: { isVerified: true, sslStatus: "active" },
  });

  return NextResponse.json({
    data: {
      id: updated.id,
      project_id: updated.projectId,
      domain: updated.domain,
      is_primary: false,
      is_verified: updated.isVerified,
      dns_records: updated.dnsRecords,
      ssl_status: updated.sslStatus,
      created_at: updated.createdAt.toISOString(),
    },
    message: "success",
  });
}
