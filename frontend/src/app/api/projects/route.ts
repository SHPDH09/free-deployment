import { NextRequest, NextResponse } from "next/server";
import { slugify } from "@/lib/auth-server";
import { getUserFromRequest, mapProject } from "@/lib/server-utils";
import { prisma } from "@/lib/prisma";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const projects = await prisma.project.findMany({
    where: { userId: user.id },
    orderBy: { updatedAt: "desc" },
  });

  return NextResponse.json({
    data: projects.map(mapProject),
    message: "success",
  });
}

export async function POST(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });

  const body = await req.json();
  const slug = `${slugify(body.name)}-${Date.now().toString(36).slice(-4)}`;

  const project = await prisma.project.create({
    data: {
      userId: user.id,
      name: body.name,
      slug,
      githubRepoFullName: body.github_repo_full_name,
      defaultBranch: body.default_branch || "main",
      framework: body.framework,
      rootDirectory: body.root_directory || ".",
      buildCommand: body.build_command,
      installCommand: body.install_command,
      outputDirectory: body.output_directory,
      deploymentType: body.deployment_type || "static",
    },
  });

  return NextResponse.json({ data: mapProject(project), message: "success" }, { status: 201 });
}
