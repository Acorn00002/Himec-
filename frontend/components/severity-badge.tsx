import { AlertCircle, AlertOctagon, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { SEVERITY_META } from "@/lib/severity";
import type { Severity } from "@/lib/types";

const ICONS: Record<Severity, typeof AlertOctagon> = {
  HIGH: AlertOctagon,
  MEDIUM: AlertTriangle,
  LOW: AlertCircle,
  INFO: Info,
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  const meta = SEVERITY_META[severity];
  const Icon = ICONS[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold",
        meta.bgClass,
        meta.textClass,
        meta.borderClass,
        className
      )}
    >
      <Icon className="size-3.5" strokeWidth={2.5} />
      {meta.label}
    </span>
  );
}
