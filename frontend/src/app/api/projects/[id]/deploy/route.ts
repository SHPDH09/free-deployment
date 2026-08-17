import { NextRequest, NextResponse } from "next/server";
import {
  getProjectForUser,
  getUserFromRequest,
  mapDeployment,
  runDeployment,
} from "@/lib/server-utils";

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const project = await getProjectForUser(params.id, user.id);
  if (!project) return NextResponse.json({ detail: "Not found" }, { status: 404 });

  const deployment = await runDeployment(params.id, "manual");
  return NextResponse.json({ data: mapDeployment(deployment), message: "success" });
}
