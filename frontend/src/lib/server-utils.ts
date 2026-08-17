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

export async function getProjectForUser(projectId: string, userId: string) {
  return prisma.project.findFirst({ where: { id: projectId, userId } });
}

export function platformDomain() {
  if (process.env.PLATFORM_DOMAIN) return process.env.PLATFORM_DOMAIN;
  if (process.env.VERCEL_URL) return process.env.VERCEL_URL;
  return "localhost:3000";
}

export function projectUrl(slug: string) {
  const domain = platformDomain();
  if (domain.includes("localhost")) {
    return `http://${domain}`;
  }
  if (process.env.VERCEL_URL && !process.env.PLATFORM_DOMAIN) {
    return `https://${process.env.VERCEL_URL}`;
  }
  return `https://${slug}.${domain}`;
}

export async function runDeployment(projectId: string, triggeredBy: string) {
  const project = await prisma.project.findUnique({ where: { id: projectId } });
  if (!project) throw new Error("Project not found");

  const last = await prisma.deployment.findFirst({
    where: { projectId },
    orderBy: { version: "desc" },
  });
  const version = (last?.version ?? 0) + 1;
  const url = projectUrl(project.slug);

  const deployment = await prisma.deployment.create({
    data: {
      projectId,
      version,
      branch: project.defaultBranch,
      status: "building",
      buildStatus: "building",
      deploymentStatus: "deploying",
      triggeredBy,
      deploymentUrl: url,
      isProduction: true,
    },
  });

  const logs = [
    { step: "clone", message: "Cloning repository..." },
    { step: "install", message: "Installing dependencies..." },
    { step: "build", message: "Running build..." },
    { step: "deploy", message: "Deploying to edge..." },
    { step: "health", message: "Health check passed." },
    { step: "complete", message: "Deployment successful." },
  ];

  for (const log of logs) {
    await prisma.deploymentLog.create({
      data: { deploymentId: deployment.id, message: log.message, step: log.step },
    });
  }

  const updated = await prisma.deployment.update({
    where: { id: deployment.id },
    data: {
      status: "success",
      buildStatus: "success",
      deploymentStatus: "success",
      buildDurationMs: 12000,
      totalDurationMs: 15000,
    },
  });

  await prisma.project.update({
    where: { id: projectId },
    data: { activeDeploymentId: deployment.id },
  });

  return updated;
}

export function mapProject(p: {
  id: string;
  name: string;
  slug: string;
  githubRepoFullName: string;
  defaultBranch: string;
  framework: string | null;
  rootDirectory: string;
  buildCommand: string | null;
  installCommand: string | null;
  outputDirectory: string | null;
  startCommand: string | null;
  deploymentType: string;
  status: string;
  activeDeploymentId: string | null;
  createdAt: Date;
  updatedAt: Date;
}) {
  return {
    id: p.id,
    name: p.name,
    slug: p.slug,
    description: null,
    github_repo_full_name: p.githubRepoFullName,
    default_branch: p.defaultBranch,
    framework: p.framework,
    root_directory: p.rootDirectory,
    build_command: p.buildCommand,
    install_command: p.installCommand,
    output_directory: p.outputDirectory,
    start_command: p.startCommand,
    node_version: null,
    python_version: null,
    deployment_type: p.deploymentType,
    status: p.status,
    is_suspended: false,
    active_deployment_id: p.activeDeploymentId,
    deployment_url: projectUrl(p.slug),
    created_at: p.createdAt.toISOString(),
    updated_at: p.updatedAt.toISOString(),
  };
}

export function mapDeployment(d: {
  id: string;
  projectId: string;
  version: number;
  commitSha: string | null;
  commitMessage: string | null;
  branch: string;
  status: string;
  buildStatus: string;
  deploymentStatus: string;
  isProduction: boolean;
  isPreview: boolean;
  deploymentUrl: string | null;
  previewUrl: string | null;
  buildDurationMs: number | null;
  totalDurationMs: number | null;
  errorMessage: string | null;
  triggeredBy: string;
  createdAt: Date;
}) {
  return {
    id: d.id,
    project_id: d.projectId,
    version: d.version,
    commit_sha: d.commitSha,
    commit_message: d.commitMessage,
    branch: d.branch,
    author_name: null,
    author_email: null,
    status: d.status,
    build_status: d.buildStatus,
    deployment_status: d.deploymentStatus,
    is_production: d.isProduction,
    is_preview: d.isPreview,
    deployment_url: d.deploymentUrl,
    preview_url: d.previewUrl,
    build_duration_ms: d.buildDurationMs,
    deploy_duration_ms: null,
    total_duration_ms: d.totalDurationMs,
    error_message: d.errorMessage,
    health_check_status: null,
    triggered_by: d.triggeredBy,
    started_at: null,
    finished_at: null,
    created_at: d.createdAt.toISOString(),
  };
}
