import { cn } from "@/lib/utils";
import { DISPOSITION_META } from "@/lib/disposition";
import type { IssueDisposition } from "@/lib/types";

export function DispositionBadge({
  disposition,
  className,
  hideOpen = false,
}: {
  disposition: IssueDisposition;
  className?: string;
  hideOpen?: boolean;
}) {
  if (hideOpen && disposition === "open") return null;
  const meta = DISPOSITION_META[disposition];
  const Icon = meta.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        meta.bgClass,
        meta.textClass,
        meta.borderClass,
        className
      )}
    >
      <Icon className="size-3.5" strokeWidth={2.5} />
      {meta.short}
    </span>
  );
}
