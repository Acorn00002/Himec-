import type { Severity } from "./types";

// Status palette (fixed, never themed) — maps INFO/LOW/MEDIUM/HIGH onto the
// good/warning/serious/critical roles. Light-surface contrast for warning/serious
// is intentionally sub-3:1, so these colors are always paired with an icon + label
// in the UI, never used as color alone.
export const SEVERITY_META: Record<
  Severity,
  { label: string; hex: string; textClass: string; bgClass: string; borderClass: string; rank: number }
> = {
  HIGH: {
    label: "높음",
    hex: "#d03b3b",
    textClass: "text-[#a32e2e] dark:text-[#f19a9a]",
    bgClass: "bg-[#d03b3b]/10",
    borderClass: "border-[#d03b3b]/30",
    rank: 3,
  },
  MEDIUM: {
    label: "중간",
    hex: "#ec835a",
    textClass: "text-[#b35a37] dark:text-[#f0a884]",
    bgClass: "bg-[#ec835a]/10",
    borderClass: "border-[#ec835a]/30",
    rank: 2,
  },
  LOW: {
    label: "낮음",
    hex: "#c98500",
    textClass: "text-[#8f6000] dark:text-[#e0b352]",
    bgClass: "bg-[#fab219]/15",
    borderClass: "border-[#fab219]/40",
    rank: 1,
  },
  INFO: {
    label: "참고",
    hex: "#0ca30c",
    textClass: "text-[#0a7a0a] dark:text-[#7fce7f]",
    bgClass: "bg-[#0ca30c]/10",
    borderClass: "border-[#0ca30c]/30",
    rank: 0,
  },
};

export const SEVERITY_ORDER: Severity[] = ["HIGH", "MEDIUM", "LOW", "INFO"];
