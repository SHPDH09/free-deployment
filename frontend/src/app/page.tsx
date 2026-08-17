import Link from "next/link";
import { ArrowRight, Rocket, Shield, Zap } from "lucide-react";
import { GitHubIcon } from "@/components/icons/github";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-slate-950">
      <nav className="border-b border-slate-800 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600">
              <Rocket className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-white">DeployStack</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-slate-400 hover:text-white">
              Sign in
            </Link>
            <Link href="/login">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      <section className="mx-auto max-w-6xl px-6 py-24 text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-sm text-violet-400">
          <Zap className="h-4 w-4" />
          Self-hosted deployment platform
        </div>
        <h1 className="mb-6 text-5xl font-bold tracking-tight text-white md:text-6xl">
          Deploy on your own
          <br />
          <span className="gradient-text">infrastructure</span>
        </h1>
        <p className="mx-auto mb-10 max-w-2xl text-lg text-slate-400">
          Connect GitHub, push code, and get live URLs with automatic builds, Docker isolation,
          custom domains, and HTTPS — all on infrastructure you control.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link href="/login">
            <Button size="lg" className="gap-2">
              <GitHubIcon className="h-5 w-5" />
              Connect GitHub
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="grid gap-6 md:grid-cols-3">
          {[
            {
              icon: GitHubIcon,
              title: "GitHub Integration",
              desc: "OAuth, webhooks, and automatic deployments on every push.",
            },
            {
              icon: Shield,
              title: "Docker Isolation",
              desc: "Every build runs in an isolated container with resource limits.",
            },
            {
              icon: Rocket,
              title: "Instant Deploys",
              desc: "Build queue, health checks, rollbacks, and preview URLs.",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-slate-800 bg-slate-900/50 p-6"
            >
              <feature.icon className="mb-4 h-8 w-8 text-violet-400" />
              <h3 className="mb-2 text-lg font-semibold text-white">{feature.title}</h3>
              <p className="text-sm text-slate-400">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
