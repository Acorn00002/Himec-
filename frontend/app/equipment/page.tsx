"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { FileStack, Search } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { SeverityBadge } from "@/components/severity-badge";
import { Input } from "@/components/ui/input";
import { useCurrentProject } from "@/hooks/useCurrentProject";
import { listEquipment } from "@/lib/api";
import type { EquipmentSummary } from "@/lib/types";

export default function EquipmentExplorerPage() {
  const { projectId } = useCurrentProject();
  const [equipment, setEquipment] = useState<EquipmentSummary[] | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!projectId) return;
    listEquipment(projectId).then(setEquipment);
  }, [projectId]);

  const filtered = useMemo(() => {
    if (!equipment) return [];
    const q = query.trim().toLowerCase();
    if (!q) return equipment;
    return equipment.filter(
      (e) => e.tag.toLowerCase().includes(q) || e.equipment_type.toLowerCase().includes(q)
    );
  }, [equipment, query]);

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">설비 탐색</h1>
            <p className="text-sm text-muted-foreground">TAG 단위로 통합된 설비 목록입니다. 클릭하면 교차검증 결과를 볼 수 있습니다.</p>
          </div>
        </div>

        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="TAG 또는 설비 유형 검색 (예: M-101, Motor)"
            className="pl-9"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        {!equipment ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-32 animate-pulse rounded-xl border bg-card" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <p className="py-12 text-center text-sm text-muted-foreground">설비가 없습니다.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((eq) => (
              <Link
                key={eq.id}
                href={`/equipment/${encodeURIComponent(eq.tag)}`}
                className="rounded-xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-mono text-lg font-bold">{eq.tag}</p>
                    <p className="text-xs text-muted-foreground">{eq.equipment_type}</p>
                  </div>
                  {eq.max_severity && <SeverityBadge severity={eq.max_severity} />}
                </div>
                <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <FileStack className="size-3.5" />
                    문서 {eq.document_count}건
                  </span>
                  <span>이슈 {eq.issue_count}건</span>
                </div>
                {eq.top_issue_label ? (
                  <p className="mt-2 truncate text-xs font-medium text-[#a32e2e] dark:text-[#f19a9a]">{eq.top_issue_label}</p>
                ) : (
                  <p className="mt-2 text-xs text-muted-foreground">발견된 이슈 없음</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
