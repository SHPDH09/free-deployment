import { NextRequest } from "next/server";
import { verifyToken } from "./auth-server";
import { prisma } from "./prisma";

export async function getUserFromRequest(req: NextRequest) {
  const header = req.headers.get("authorization");
  const token = header?.startsWith("Bearer ")
    ? header.slice(7)
    : req.cookies.get("access_token")?.value;

  if (!token) return null;

  const payload = await verifyToken(token);
  if (!payload?.sub) return null;

  return prisma.user.findUnique({ where: { id: payload.sub } });
}
