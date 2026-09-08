"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertOctagon, FileDown, FileStack, ListChecks, Wrench } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { StatCard } from "@/components/dashboard/StatCard";
import { SeverityChart } from "@/components/dashboard/SeverityChart";
import { SeverityBadge } from "@/components/severity-badge";
import { DispositionBadge } from "@/components/issues/DispositionBadge";
import { IssueDetailSheet } from "@/components/issues/IssueDetailSheet";
import { HowItWorks } from "@/components/HowItWorks";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useCurrentProject } from "@/hooks/useCurrentProject";
import { getDashboard, listIssues } from "@/lib/api";
import { mismatchSummary } from "@/lib/issue-format";
import type { Dashboard, Issue } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function DashboardPage() {
  const { projectId, project } = useCurrentProject();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    getDashboard(projectId).then(setDashboard);
    listIssues(projectId).then(setIssues);
  }, [projectId]);

  function handleIssueUpdated(updated: Issue) {
    setIssues((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
    setSelectedIssue((prev) => (prev && prev.id === updated.id ? updated : prev));
    if (projectId) getDashboard(projectId).then(setDashboard);
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">대시보드</h1>
            <p className="max-w-2xl text-sm text-muted-foreground">
              여러 설계 문서에 흩어진 <span className="font-medium text-foreground">같은 설비의 정보</span>를 AI가 교차 검증하여,
              문서 간 불일치와 그 영향이 미칠 수 있는 후속 설계 항목을 찾아냅니다.
            </p>
          </div>
          {projectId && (
            <Button
              variant="outline"
              nativeButton={false}
              className="shrink-0 gap-1.5"
              render={<a href={`${API_URL}/api/projects/${projectId}/report.pdf`} download />}
            >
              <FileDown className="size-4" />
              리포트 내보내기 (PDF)
            </Button>
          )}
        </div>

        {!dashboard ? (
          <div className="grid gap-4 sm:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl border bg-card" />
            ))}
          </div>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-4">
              <StatCard label="문서 수" value={dashboard.document_count} icon={FileStack} />
              <StatCard label="설비 수" value={dashboard.equipment_count} icon={Wrench} />
              <StatCard label="전체 이슈" value={dashboard.issue_count} icon={ListChecks} />
              <StatCard
                label="높음 위험도"
                value={dashboard.high_risk_count}
                icon={AlertOctagon}
                accentClass="text-[#d03b3b]"
              />
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-sm">
              <HowItWorks />
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              <div className="rounded-xl border bg-card p-5 shadow-sm lg:col-span-2">
                <h2 className="text-sm font-semibold">위험도 분포</h2>
                <p className="text-xs text-muted-foreground">위험도별 발견된 이슈 수 (높음 · 중간 · 낮음 · 참고)</p>
                <SeverityChart data={dashboard.severity_breakdown} />
              </div>

              <div className="rounded-xl border bg-card p-5 shadow-sm">
                <h2 className="text-sm font-semibold">검토 진행</h2>
                <p className="text-xs text-muted-foreground">담당 엔지니어가 확인·조치한 이슈</p>
                <p className="mt-6 text-2xl font-bold tabular-nums">
                  {dashboard.issue_count}개 발견 이슈 중{" "}
                  <span className="text-[#0a7a0a] dark:text-[#7fce7f]">{dashboard.reviewed_count}개 검토 완료</span>
                </p>
                <Progress value={dashboard.review_progress_percent} className="mt-3" />
                <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
                  <span>검토 전 <span className="font-semibold text-foreground">{dashboard.open_count}</span></span>
                  <span>검토 완료 <span className="font-semibold text-foreground">{dashboard.reviewed_count}</span></span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border bg-card p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold">AI 발견 사항 ({issues.length}건)</h2>
                  <p className="text-xs text-muted-foreground">문서 간 불일치·누락 항목 (위험도 순). 행을 클릭하면 상세 검토 화면이 열립니다.</p>
                </div>
                <Link href="/equipment" className="shrink-0 text-xs font-medium text-blue-600 hover:underline dark:text-blue-400">
                  설비별로 보기 →
                </Link>
              </div>

              <div className="mt-4 divide-y">
                {issues.length === 0 && (
                  <p className="py-6 text-center text-sm text-muted-foreground">발견된 이슈가 없습니다.</p>
                )}
                {issues.map((issue) => {
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
                          {issue.equipment_tag && (
                            <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs font-semibold">
                              {issue.equipment_tag}
                            </span>
                          )}
                          <DispositionBadge disposition={issue.disposition} hideOpen />
                        </div>
                        <p className="mt-1 truncate text-sm font-medium">{issue.title}</p>
                        {diff && (
                          <p className="mt-0.5 font-mono text-xs text-[#a32e2e] dark:text-[#f19a9a]">{diff}</p>
                        )}
                      </div>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        영향 가능 항목 {issue.impact_items.length}개
                      </span>
                    </button>
                  );
                })}
              </div>
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
