"use client";

import { useMemo, useState } from "react";
import { Check, FileText, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ParameterRow } from "@/lib/types";

function EvidencePopover({ row, doc }: { row: ParameterRow; doc: string }) {
  const source = row.sources.find((s) => s.document_name === doc);
  if (!source) return <span className="text-muted-foreground/50">-</span>;

  const hasTrace = Boolean(source.location || source.raw_snippet);
  const highlight = row.status === "mismatch" && row.sources.length > 1;

  return (
    <span className="group relative inline-flex cursor-default items-center gap-1">
      <span
        className={cn(
          "font-mono",
          highlight && "font-semibold text-[#a32e2e] dark:text-[#f19a9a]",
          hasTrace && "underline decoration-dotted decoration-muted-foreground/50 underline-offset-2"
        )}
      >
        {source.value}
        {source.unit ? ` ${source.unit}` : ""}
      </span>
      {hasTrace && (
        <span className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1.5 hidden w-64 -translate-x-1/2 rounded-lg border border-border bg-popover p-2.5 text-left shadow-lg group-hover:block">
          <span className="flex items-center gap-1 text-[11px] font-semibold text-foreground">
            <FileText className="size-3" />
            {source.document_name}
          </span>
          {source.location && (
            <span className="mt-0.5 block font-mono text-[11px] text-muted-foreground">
              위치: {source.location}
            </span>
          )}
          {source.raw_snippet && (
            <span className="mt-1.5 block whitespace-pre-wrap rounded bg-muted/70 p-1.5 font-sans text-[11px] leading-relaxed text-foreground/90">
              {source.raw_snippet}
            </span>
          )}
          <span className="mt-1.5 block text-[10px] text-muted-foreground">
            AI 추출 값 — 원문과 대조해 확인하세요
          </span>
        </span>
      )}
    </span>
  );
}

export function CrossCheckTable({ parameters }: { parameters: ParameterRow[] }) {
  const [onlyMismatch, setOnlyMismatch] = useState(false);

  const documents = useMemo(() => {
    const set = new Set<string>();
    parameters.forEach((p) => p.sources.forEach((s) => set.add(s.document_name)));
    return Array.from(set).sort();
  }, [parameters]);

  const rows = onlyMismatch ? parameters.filter((p) => p.status === "mismatch") : parameters;

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-4">
        <p className="text-xs text-muted-foreground">
          <span className="font-medium text-[#a32e2e] dark:text-[#f19a9a]">빨간 값</span>은 문서 간에 서로 다른 값입니다. 점선이 표시된 값에 마우스를 올리면 원문 위치를 확인할 수 있습니다.
        </p>
        <label className="flex shrink-0 items-center gap-1.5 text-xs">
          <input type="checkbox" checked={onlyMismatch} onChange={(e) => setOnlyMismatch(e.target.checked)} />
          불일치만 보기
        </label>
      </div>
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="bg-muted/60 text-xs text-muted-foreground">
            <tr>
              <th className="px-3 py-2 text-left font-medium">항목</th>
              {documents.map((doc) => (
                <th key={doc} className="px-3 py-2 text-right font-medium">
                  {doc}
                </th>
              ))}
              <th className="px-3 py-2 text-center font-medium">일치 여부</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} className={cn("border-t", row.status === "mismatch" && "bg-[#d03b3b]/5")}>
                <td className="px-3 py-2 font-medium">{row.name}</td>
                {documents.map((doc) => (
                  <td key={doc} className="px-3 py-2 text-right">
                    <EvidencePopover row={row} doc={doc} />
                  </td>
                ))}
                <td className="px-3 py-2 text-center">
                  {row.status === "match" ? (
                    <Check className="mx-auto size-4 text-[#0ca30c]" strokeWidth={3} />
                  ) : (
                    <TriangleAlert className="mx-auto size-4 text-[#d03b3b]" strokeWidth={2.5} />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
