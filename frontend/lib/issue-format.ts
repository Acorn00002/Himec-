import type { Issue } from "./types";

// Values that mean "no value found", not a real reading — excluded from the diff summary.
const PLACEHOLDER_VALUES = new Set(["(기재 없음)", "(not found)", "-", ""]);

function formatValue(value: string, unit: string | null): string {
  return unit ? `${value} ${unit}` : value;
}

/**
 * A one-line "15 kW ↔ 18.5 kW" summary of the conflicting values in an issue,
 * for showing the disagreement at a glance in list rows. Returns null when there
 * aren't at least two distinct real values (e.g. a pure "missing" issue).
 */
export function mismatchSummary(issue: Issue): string | null {
  const seen: string[] = [];
  for (const e of issue.evidence) {
    if (PLACEHOLDER_VALUES.has(e.value.trim())) continue;
    const label = formatValue(e.value, e.unit);
    if (!seen.includes(label)) seen.push(label);
  }
  return seen.length >= 2 ? seen.join("  ↔  ") : null;
}

/**
 * The causal chain to visualise under "영향 가능 항목": the parameter that
 * disagrees, followed by the downstream design tasks it feeds into.
 */
export function impactChain(issue: Issue): string[] {
  const root = issue.parameter_label ?? issue.parameter_name;
  const head = root ? [`${issue.equipment_tag ?? ""} ${root}`.trim()] : [];
  return [...head, ...issue.impact_items];
}
