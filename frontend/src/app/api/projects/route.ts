import { NextRequest, NextResponse } from "next/server";
import { getUserFromRequest } from "@/lib/get-user";
import { prisma } from "@/lib/prisma";
import { slugify } from "@/lib/auth-server";

export async function GET(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const projects = await prisma.project.findMany({
    where: { userId: user.id },
    orderBy: { updatedAt: "desc" },
  });

  const domain = process.env.PLATFORM_DOMAIN || process.env.VERCEL_URL || "localhost";

  return NextResponse.json({
    data: projects.map((p) => ({
      id: p.id,
      name: p.name,
      slug: p.slug,
      github_repo_full_name: p.githubRepoFullName,
      default_branch: p.defaultBranch,
      framework: p.framework,
      deployment_type: p.deploymentType,
      status: p.status,
      deployment_url: `https://${p.slug}.${domain}`,
      created_at: p.createdAt.toISOString(),
      updated_at: p.updatedAt.toISOString(),
    })),
    message: "success",
  });
}

export async function POST(req: NextRequest) {
  const user = await getUserFromRequest(req);
  if (!user) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const body = await req.json();
  const slug = slugify(body.name);
  const domain = process.env.PLATFORM_DOMAIN || process.env.VERCEL_URL || "localhost";

  const project = await prisma.project.create({
    data: {
      userId: user.id,
      name: body.name,
      slug: `${slug}-${Date.now().toString(36).slice(-4)}`,
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

  const deployment = await prisma.deployment.create({
    data: {
      projectId: project.id,
      version: 1,
      branch: project.defaultBranch,
      status: "success",
      deploymentUrl: `https://${project.slug}.${domain}`,
      triggeredBy: "manual",
    },
  });

  return NextResponse.json({
    data: {
      id: project.id,
      name: project.name,
      slug: project.slug,
      deployment_url: deployment.deploymentUrl,
    },
    message: "success",
  });
}
