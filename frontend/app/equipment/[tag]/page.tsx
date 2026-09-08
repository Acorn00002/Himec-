"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, FileStack } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { CrossCheckTable } from "@/components/equipment/CrossCheckTable";
import { SeverityBadge } from "@/components/severity-badge";
import { DispositionBadge } from "@/components/issues/DispositionBadge";
import { IssueDetailSheet } from "@/components/issues/IssueDetailSheet";
import { useCurrentProject } from "@/hooks/useCurrentProject";
import { getEquipmentDetail } from "@/lib/api";
import { mismatchSummary } from "@/lib/issue-format";
import type { EquipmentDetail, Issue } from "@/lib/types";

export default function EquipmentDetailPage() {
  const params = useParams<{ tag: string }>();
  const tag = decodeURIComponent(params.tag);
  const { projectId, project } = useCurrentProject();
  const [detail, setDetail] = useState<EquipmentDetail | null>(null);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    getEquipmentDetail(projectId, tag).then(setDetail);
  }, [projectId, tag]);

  function handleIssueUpdated(updated: Issue) {
    setDetail((prev) =>
      prev
        ? { ...prev, issues: prev.issues.map((i) => (i.id === updated.id ? updated : i)) }
        : prev
    );
    setSelectedIssue((prev) => (prev && prev.id === updated.id ? updated : prev));
  }

  const connectedDocs = useMemo(() => {
    if (!detail) return [];
    const set = new Set<string>();
    detail.parameters.forEach((p) => p.sources.forEach((s) => set.add(s.document_name)));
    return Array.from(set).sort();
  }, [detail]);

  const mismatchCount = detail?.parameters.filter((p) => p.status === "mismatch").length ?? 0;

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-6">
        <Link
          href="/equipment"
          className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="size-3.5" />
          설비 탐색
        </Link>

        {!detail ? (
          <div className="h-64 animate-pulse rounded-xl border bg-card" />
        ) : (
          <>
            <div>
              <h1 className="font-mono text-2xl font-bold">{detail.tag}</h1>
              <p className="text-sm text-muted-foreground">{detail.equipment_type}</p>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <FileStack className="size-3.5" />
                  연결된 문서 {connectedDocs.length}건
                </span>
                <span>비교 항목 {detail.parameters.length}개</span>
                <span className={mismatchCount > 0 ? "font-medium text-[#a32e2e] dark:text-[#f19a9a]" : ""}>
                  불일치 {mismatchCount}건
                </span>
                <span>이슈 {detail.issues.length}건</span>
              </div>
              {connectedDocs.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {connectedDocs.map((d) => (
                    <span key={d} className="rounded-md border bg-muted/40 px-2 py-0.5 text-xs">
                      {d}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-sm">
              <h2 className="text-sm font-semibold">문서별 값 비교</h2>
              <p className="mb-3 text-xs text-muted-foreground">
                이 설비의 각 항목을 문서별로 나란히 놓고, 값이 서로 같은지 검증 엔진이 판정한 결과입니다.
              </p>
              <CrossCheckTable parameters={detail.parameters} />
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-sm">
              <h2 className="text-sm font-semibold">발견된 이슈</h2>
              <p className="mb-3 text-xs text-muted-foreground">행을 클릭하면 상세 검토 화면이 열립니다.</p>
              {detail.issues.length === 0 ? (
                <p className="py-6 text-center text-sm text-muted-foreground">발견된 이슈가 없습니다.</p>
              ) : (
                <div className="divide-y">
                  {detail.issues.map((issue) => {
                    const diff = mismatchSummary(issue);
                    return (
                      <button
                        key={issue.id}
                        onClick={() => {
                          setSelectedIssue(issue);
                          setSheetOpen(true);
                        }}
                        className="flex w-full items-center justify-between gap-4 py-3 text-left hover:bg-muted/40"
                      >
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <SeverityBadge severity={issue.severity} />
                            {issue.parameter_label && (
                              <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-medium">
                                {issue.parameter_label}
                              </span>
                            )}
                            <DispositionBadge disposition={issue.disposition} hideOpen />
                          </div>
                          <p className="mt-1 truncate text-sm font-medium">{issue.title}</p>
                          {diff && <p className="mt-0.5 font-mono text-xs text-[#a32e2e] dark:text-[#f19a9a]">{diff}</p>}
                        </div>
                        <span className="shrink-0 text-xs text-muted-foreground">
                          영향 가능 항목 {issue.impact_items.length}개
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <IssueDetailSheet
        issue={selectedIssue}
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        onUpdated={handleIssueUpdated}
        isDemo={project?.mode === "demo"}
      />
    </AppShell>
  );
}
