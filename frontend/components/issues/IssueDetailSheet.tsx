"use client";

import { useEffect, useState } from "react";
import { ArrowDown, ChevronRight, FileText, Loader2, Scale, TriangleAlert } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SeverityBadge } from "@/components/severity-badge";
import { DispositionBadge } from "@/components/issues/DispositionBadge";
import { cn } from "@/lib/utils";
import { getDocumentContent, updateIssueReview } from "@/lib/api";
import { DISPOSITION_META, DISPOSITION_ORDER } from "@/lib/disposition";
import { impactChain, mismatchSummary } from "@/lib/issue-format";
import { toast } from "sonner";
import type { ExtractedChunk, Issue, IssueDisposition } from "@/lib/types";

const ISSUE_TYPE_LABEL: Record<string, string> = {
  value_mismatch: "값 불일치",
  unit_mismatch: "단위/자릿수 불일치",
  missing: "필수 항목 누락",
  spec_mismatch: "사양 불일치",
  abnormal_value: "이상값",
  calc_mismatch: "계산값 불일치",
};

function fmtValue(value: string, unit: string | null) {
  return unit ? `${value} ${unit}` : value;
}

/** 문서별 값 비교 — 어느 문서가 어떤 값을 적었는지 한눈에, 클릭하면 원문 확인. */
function ValueComparison({
  issue,
  isDemo,
}: {
  issue: Issue;
  isDemo: boolean;
}) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const diff = mismatchSummary(issue);
  const isMissing = issue.issue_type === "missing";

  // 서로 다른 값에 색을 주기 위해 값 → 등장 순서 인덱스
  const distinct = Array.from(
    new Set(issue.evidence.map((e) => fmtValue(e.value, e.unit)))
  );

  return (
    <section>
      <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        <Scale className="size-3.5" />
        문서별 값 비교
      </h4>

      {isMissing ? (
        <p className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
          누락 — 업로드된 문서에서 값을 찾지 못했습니다.
        </p>
      ) : diff ? (
        <p className="mt-2 rounded-lg border border-[#d03b3b]/30 bg-[#d03b3b]/5 px-3 py-2 text-sm font-medium text-[#a32e2e] dark:text-[#f19a9a]">
          불일치 &nbsp;
          <span className="font-mono">{diff}</span>
        </p>
      ) : null}

      <div className="mt-2 overflow-hidden rounded-lg border">
        <table className="w-full text-sm">
          <thead className="bg-muted/60 text-xs text-muted-foreground">
            <tr>
              <th className="px-3 py-2 text-left font-medium">문서</th>
              <th className="px-3 py-2 text-right font-medium">기재된 값</th>
            </tr>
          </thead>
          <tbody>
            {issue.evidence.map((e, i) => {
              const traceable = e.document_id != null || Boolean(e.raw_snippet);
              const label = fmtValue(e.value, e.unit);
              const colorIdx = distinct.indexOf(label);
              const differ = !isMissing && distinct.length > 1;
              return (
                <FragmentRow
                  key={i}
                  document={e.document}
                  location={e.location}
                  valueLabel={label}
                  differ={differ}
                  emphasize={differ && colorIdx === distinct.length - 1}
                  traceable={traceable}
                  expanded={expandedIndex === i}
                  onToggle={() =>
                    traceable && setExpandedIndex((p) => (p === i ? null : i))
                  }
                  projectId={issue.project_id}
                  documentId={e.document_id}
                  rawSnippet={e.raw_snippet}
                  parameterLabel={issue.parameter_label}
                />
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-1.5 text-xs text-muted-foreground">
        값을 클릭하면 어느 문서의 어디에서 추출됐는지 원문을 확인할 수 있습니다.
        {isDemo && " (데모 데이터 기반 예시 위치입니다.)"}
      </p>
    </section>
  );
}

function FragmentRow({
  document,
  location,
  valueLabel,
  differ,
  emphasize,
  traceable,
  expanded,
  onToggle,
  projectId,
  documentId,
  rawSnippet,
  parameterLabel,
}: {
  document: string;
  location: string | null;
  valueLabel: string;
  differ: boolean;
  emphasize: boolean;
  traceable: boolean;
  expanded: boolean;
  onToggle: () => void;
  projectId: number;
  documentId: number | null;
  rawSnippet: string | null;
  parameterLabel: string | null;
}) {
  return (
    <>
      <tr
        className={cn("border-t", traceable && "cursor-pointer hover:bg-muted/40")}
        onClick={onToggle}
      >
        <td className="px-3 py-2 font-medium">
          <span className="flex items-center gap-1">
            {traceable && (
              <ChevronRight
                className={cn("size-3.5 shrink-0 transition-transform", expanded && "rotate-90")}
              />
            )}
            {document}
          </span>
        </td>
        <td
          className={cn(
            "px-3 py-2 text-right font-mono",
            differ && (emphasize ? "font-semibold text-[#a32e2e] dark:text-[#f19a9a]" : "text-foreground")
          )}
        >
          {valueLabel}
        </td>
      </tr>
      {expanded && (
        <tr className="border-t bg-muted/30">
          <td colSpan={2} className="px-3 py-3">
            <div className="space-y-2">
              <div className="rounded-md border bg-card p-2.5 text-xs">
                <p className="font-semibold">{document}</p>
                <p className="mt-0.5 text-muted-foreground">
                  위치: <span className="font-mono">{location ?? "-"}</span>
                  {parameterLabel ? ` · 항목: ${parameterLabel}` : ""}
                  {` · 값: `}
                  <span className="font-mono">{valueLabel}</span>
                </p>
              </div>
              {rawSnippet && (
                <div className="rounded-md border border-blue-200 bg-blue-50/60 p-2.5 dark:border-blue-900 dark:bg-blue-950/40">
                  <p className="mb-1 text-[11px] font-semibold text-blue-900 dark:text-blue-300">AI가 이 값을 읽어낸 문장</p>
                  <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-blue-950/90 dark:text-blue-100/90">
                    {rawSnippet}
                  </pre>
                </div>
              )}
              {documentId != null && (
                <EvidenceOriginalText projectId={projectId} documentId={documentId} location={location} />
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function EvidenceOriginalText({
  projectId,
  documentId,
  location,
}: {
  projectId: number;
  documentId: number;
  location: string | null;
}) {
  const [chunks, setChunks] = useState<ExtractedChunk[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getDocumentContent(projectId, documentId)
      .then((data) => !cancelled && setChunks(data))
      .catch(() => !cancelled && setError(true))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [projectId, documentId]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="size-3.5 animate-spin" />
        원문을 불러오는 중…
      </div>
    );
  }
  if (error || !chunks) {
    return <p className="text-xs text-muted-foreground">원문을 불러오지 못했습니다.</p>;
  }

  const matched = chunks.find((c) => c.location === location) ?? null;
  const shown = matched ? [matched] : chunks;

  if (shown.length === 0) {
    return <p className="text-xs text-muted-foreground">이 문서에서 추출된 원문이 없습니다.</p>;
  }

  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold text-muted-foreground">
        {matched ? "문서 원문 (해당 위치)" : "문서 전체 추출 원문"}
      </p>
      {!matched && (
        <p className="text-xs text-amber-700 dark:text-amber-300">
          정확히 일치하는 위치({location ?? "-"})를 찾지 못해 문서의 전체 추출 원문을 표시합니다.
        </p>
      )}
      {shown.map((c) => (
        <div key={c.id} className="rounded-md border bg-card p-2.5">
          <p className="mb-1 font-mono text-[11px] font-semibold text-muted-foreground">{c.location}</p>
          <pre className="max-h-40 overflow-y-auto whitespace-pre-wrap font-sans text-xs leading-relaxed text-foreground/90">
            {c.text}
          </pre>
        </div>
      ))}
    </div>
  );
}

/** 영향 가능 항목 — 파라미터에서 시작해 후속 설계 항목으로 이어지는 흐름. */
function ImpactFlow({ issue }: { issue: Issue }) {
  const chain = impactChain(issue);
  return (
    <section>
      <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        <TriangleAlert className="size-3.5" />
        영향 가능 항목
      </h4>
      <p className="mt-1 text-xs text-muted-foreground">
        이 값이 바뀌면 다시 확인해야 할 수 있는 후속 설계 항목입니다.
      </p>

      <div className="mt-3 flex flex-col items-stretch gap-1">
        {chain.map((node, i) => (
          <div key={`${node}-${i}`} className="flex flex-col items-center gap-1">
            <div
              className={cn(
                "w-full rounded-lg border px-3 py-2 text-center text-sm",
                i === 0
                  ? "border-[#d03b3b]/30 bg-[#d03b3b]/5 font-semibold text-[#a32e2e] dark:text-[#f19a9a]"
                  : "border-blue-200 bg-blue-50/70 text-blue-900 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-200"
              )}
            >
              {node}
            </div>
            {i < chain.length - 1 && <ArrowDown className="size-3.5 text-muted-foreground" />}
          </div>
        ))}
      </div>

      <p className="mt-3 rounded-lg bg-muted/60 p-2.5 text-xs leading-relaxed text-muted-foreground">
        영향 가능 항목은 검토 우선순위를 제시하기 위한 참고 정보이며, 최종 설계 판단은 담당 엔지니어의 확인이 필요합니다.
      </p>
    </section>
  );
}

/** 검증 방식 — 어디까지 AI가, 어디부터 검증 엔진이 하는지. */
function HowVerified() {
  return (
    <section>
      <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">검증 방식</h4>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        <div className="rounded-lg border border-blue-200 bg-blue-50/60 p-2.5 text-xs dark:border-blue-900 dark:bg-blue-950/40">
          <p className="font-semibold text-blue-800 dark:text-blue-300">AI</p>
          <p className="mt-1 text-foreground/80">문서 내용 이해 · 설비 TAG 식별 · 값 추출</p>
        </div>
        <div className="rounded-lg border border-emerald-200 bg-emerald-50/60 p-2.5 text-xs dark:border-emerald-900 dark:bg-emerald-950/40">
          <p className="font-semibold text-emerald-800 dark:text-emerald-300">검증 엔진</p>
          <p className="mt-1 text-foreground/80">수치 비교 · 단위 환산 · 불일치 판정</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        AI가 문서에서 값을 읽어오고, 값이 서로 같은지 다른지는 별도의 검증 로직이 계산합니다.
      </p>
    </section>
  );
}

function ReviewSection({
  issue,
  onUpdated,
}: {
  issue: Issue;
  onUpdated?: (issue: Issue) => void;
}) {
  // Mounted with key={issue.id}, so these initialisers re-run for each issue.
  const [disposition, setDisposition] = useState<IssueDisposition>(issue.disposition);
  const [comment, setComment] = useState(issue.review_comment ?? "");
  const [reviewedBy, setReviewedBy] = useState(issue.reviewed_by ?? "");
  const [saving, setSaving] = useState(false);

  const dirty =
    disposition !== issue.disposition ||
    comment.trim() !== (issue.review_comment ?? "") ||
    reviewedBy.trim() !== (issue.reviewed_by ?? "");

  async function save() {
    setSaving(true);
    try {
      const updated = await updateIssueReview(issue.id, {
        disposition,
        review_comment: comment.trim(),
        reviewed_by: reviewedBy.trim(),
      });
      onUpdated?.(updated);
      toast.success("검토 내용을 저장했습니다.");
    } catch {
      toast.error("검토 내용 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        <FileText className="size-3.5" />
        엔지니어 검토 — 상태 및 의견
      </h4>
      <p className="mt-1 text-xs text-muted-foreground">
        이 불일치가 설계상 의도된 것인지, 조치가 필요한지 판단하고 근거를 기록하세요. 저장한 내용은 PDF 리포트에 함께 반영됩니다.
      </p>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {DISPOSITION_ORDER.map((key) => {
          const meta = DISPOSITION_META[key];
          const Icon = meta.icon;
          const active = disposition === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => setDisposition(key)}
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                active
                  ? cn(meta.bgClass, meta.textClass, meta.borderClass, "ring-1 ring-inset ring-current")
                  : "border-border bg-background text-muted-foreground hover:bg-muted"
              )}
              aria-pressed={active}
            >
              <Icon className="size-3.5" strokeWidth={2.5} />
              {meta.short}
            </button>
          );
        })}
      </div>

      <div className="mt-3 space-y-2">
        <Input
          placeholder="검토자 (예: 홍길동 / 전기팀)"
          value={reviewedBy}
          onChange={(e) => setReviewedBy(e.target.value)}
        />
        <textarea
          placeholder="검토 의견 · 예외 사유를 입력하세요 (예: 도면 값이 최신이며 설비 목록 갱신 요청함 / 제어전압과 전원전압 표기 차이로 의도된 것임)"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          className="w-full resize-y rounded-lg border border-input bg-transparent px-2.5 py-1.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        />
      </div>

      <div className="mt-2.5 flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          {issue.reviewed_at
            ? `최근 검토: ${new Date(issue.reviewed_at).toLocaleString("ko-KR")}`
            : "아직 검토되지 않았습니다."}
        </p>
        <Button size="sm" onClick={save} disabled={!dirty || saving}>
          {saving && <Loader2 className="size-3.5 animate-spin" />}
          검토 내용 저장
        </Button>
      </div>
    </section>
  );
}

export function IssueDetailSheet({
  issue,
  open,
  onOpenChange,
  onUpdated,
  isDemo = false,
}: {
  issue: Issue | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdated?: (issue: Issue) => void;
  isDemo?: boolean;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full gap-0 overflow-y-auto sm:max-w-xl">
        {issue && (
          <>
            <SheetHeader className="gap-3 border-b pb-4">
              <div className="flex flex-wrap items-center gap-2">
                <SeverityBadge severity={issue.severity} />
                {issue.equipment_tag && (
                  <span className="rounded bg-muted px-2 py-0.5 font-mono text-xs font-semibold">
                    {issue.equipment_tag}
                  </span>
                )}
                <span className="text-xs text-muted-foreground">
                  {ISSUE_TYPE_LABEL[issue.issue_type] ?? issue.issue_type}
                </span>
                {issue.parameter_label && (
                  <span className="rounded bg-muted px-2 py-0.5 text-xs font-medium">
                    {issue.parameter_label}
                  </span>
                )}
                <DispositionBadge disposition={issue.disposition} hideOpen />
              </div>
              <SheetTitle className="text-left text-base leading-snug">{issue.title}</SheetTitle>
              <SheetDescription className="text-left leading-relaxed">{issue.description}</SheetDescription>
            </SheetHeader>

            <div className="space-y-6 px-4 py-5">
              <ValueComparison key={issue.id} issue={issue} isDemo={isDemo} />

              <Separator />

              <section>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">왜 중요한가?</h4>
                <p className="mt-2 rounded-lg bg-muted/60 p-3 text-sm leading-relaxed text-foreground/90">
                  {issue.reasoning}
                </p>
              </section>

              <Separator />

              <ImpactFlow issue={issue} />

              <Separator />

              <HowVerified />

              <Separator />

              <ReviewSection key={issue.id} issue={issue} onUpdated={onUpdated} />

              <p className="text-xs text-muted-foreground">
                이 화면의 분석은 검토를 돕기 위한 참고 자료입니다. AI는 설계를 확정하거나 승인하지 않으며, 최종 판단은 담당 엔지니어가 합니다.
              </p>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
