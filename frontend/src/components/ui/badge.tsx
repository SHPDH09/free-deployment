import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "info";
  className?: string;
}

const variants = {
  default: "bg-slate-800 text-slate-300",
  success: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
  warning: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
  error: "bg-red-500/15 text-red-400 border border-red-500/30",
  info: "bg-violet-500/15 text-violet-400 border border-violet-500/30",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeProps["variant"]> = {
    success: "success",
    failed: "error",
    building: "info",
    deploying: "info",
    pending: "warning",
    queued: "warning",
    cancelled: "default",
  };
  return <Badge variant={map[status] || "default"}>{status}</Badge>;
}
