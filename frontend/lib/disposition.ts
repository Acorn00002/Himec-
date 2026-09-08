import { CheckCircle2, CircleDashed, CircleDot, ShieldCheck, type LucideIcon } from "lucide-react";
import type { IssueDisposition } from "./types";

// Human-in-the-Loop dispositions — the reviewing engineer's call on each issue.
// These sit alongside AI severity, never replace it.
export const DISPOSITION_META: Record<
  IssueDisposition,
  { label: string; short: string; icon: LucideIcon; textClass: string; bgClass: string; borderClass: string }
> = {
  open: {
    label: "미검토",
    short: "미검토",
    icon: CircleDashed,
    textClass: "text-muted-foreground",
    bgClass: "bg-muted",
    borderClass: "border-border",
  },
  intentional: {
    label: "의도된 차이 (Design Margin)",
    short: "의도된 차이",
    icon: ShieldCheck,
    textClass: "text-blue-800 dark:text-blue-300",
    bgClass: "bg-blue-50 dark:bg-blue-950/40",
    borderClass: "border-blue-200 dark:border-blue-900",
  },
  action_required: {
    label: "조치 필요",
    short: "조치 필요",
    icon: CircleDot,
    textClass: "text-[#a32e2e] dark:text-[#f19a9a]",
    bgClass: "bg-[#d03b3b]/10",
    borderClass: "border-[#d03b3b]/30",
  },
  resolved: {
    label: "조치 완료",
    short: "조치 완료",
    icon: CheckCircle2,
    textClass: "text-[#0a7a0a] dark:text-[#7fce7f]",
    bgClass: "bg-[#0ca30c]/10",
    borderClass: "border-[#0ca30c]/30",
  },
};

export const DISPOSITION_ORDER: IssueDisposition[] = [
  "open",
  "intentional",
  "action_required",
  "resolved",
];
