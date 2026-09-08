"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  CheckCircle2,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Loader2,
  PlayCircle,
  UploadCloud,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCurrentProject } from "@/hooks/useCurrentProject";
import { listDocuments, runCrossCheck, uploadDocument } from "@/lib/api";
import type { DocCategory, DocStatus, Document } from "@/lib/types";

const CATEGORY_OPTIONS: { value: DocCategory; label: string }[] = [
  { value: "spec", label: "사양서 (Spec)" },
  { value: "drawing", label: "도면 (전기/기계)" },
  { value: "calculation", label: "계산서 (부하/설계)" },
  { value: "equipment_list", label: "설비 리스트 (Equipment List)" },
  { value: "pid", label: "P&ID" },
  { value: "other", label: "기타" },
];

const TYPE_ICON: Record<string, typeof FileText> = {
  pdf: FileText,
  image: ImageIcon,
  xlsx: FileSpreadsheet,
  csv: FileSpreadsheet,
  txt: FileText,
};

const STATUS_META: Record<DocStatus, { label: string; className: string }> = {
  uploaded: { label: "업로드됨 (파싱 대기)", className: "bg-muted text-muted-foreground" },
  parsed: {
    label: "파싱 완료 (AI 추출 대기)",
    className:
      "bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-900",
  },
  analyzed: {
    label: "AI 분석 완료",
    className:
      "bg-[#0ca30c]/10 text-[#0a7a0a] border border-[#0ca30c]/30 dark:text-[#7fce7f]",
  },
};

export default function UploadPage() {
  const router = useRouter();
  const { projectId, project } = useCurrentProject();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [category, setCategory] = useState<DocCategory>("spec");
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [runningCrossCheck, setRunningCrossCheck] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(() => {
    if (!projectId) return;
    listDocuments(projectId).then(setDocuments);
  }, [projectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleFiles(files: FileList | null) {
    if (!files || !projectId) return;
    setUploading(true);
    try {
      let analyzedCount = 0;
      for (const file of Array.from(files)) {
        try {
          const doc = await uploadDocument(projectId, file, category);
          if (doc.status === "analyzed") analyzedCount += 1;
        } catch {
          toast.error(`${file.name} 업로드에 실패했습니다. (지원 형식: PDF, PNG/JPG, XLSX, CSV, TXT)`);
        }
      }
      toast.success(
        analyzedCount > 0
          ? `문서 업로드가 완료되었습니다. ${analyzedCount}개 문서에서 설비 데이터를 추출했습니다.`
          : "문서 업로드가 완료되었습니다."
      );
      refresh();
    } finally {
      setUploading(false);
    }
  }

  async function handleRunCrossCheck() {
    if (!projectId) return;
    setRunningCrossCheck(true);
    try {
      const result = await runCrossCheck(projectId);
      toast.success(
        `교차검증 완료. ${result.equipment_count}개 설비에서 ${result.issue_count}개 이슈를 발견했습니다 (높음 ${result.high_risk_count}건).`
      );
      router.push("/dashboard");
    } catch {
      toast.error("교차검증 실행에 실패했습니다.");
    } finally {
      setRunningCrossCheck(false);
    }
  }

  const isDemo = project?.is_demo ?? false;

  return (
    <AppShell>
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">설계 문서 업로드</h1>
          <p className="text-sm text-muted-foreground">
            PDF·Excel 등 프로젝트 설계 문서를 업로드하면, 설비 TAG를 기준으로 정보를 연결하고 문서 간 불일치를 검토합니다.
          </p>
        </div>

        <div className="rounded-xl border bg-card p-5 shadow-sm">
          <h2 className="text-sm font-semibold">처리 과정</h2>
          <div className="mt-3 flex flex-wrap items-center gap-x-1.5 gap-y-2">
            {["문서 읽기", "설비 TAG 추출", "데이터 구조화", "문서 간 교차검증", "이슈 생성"].map((step, i, arr) => (
              <div key={step} className="flex items-center gap-1.5">
                <span className="rounded-md border bg-muted/50 px-2 py-1 text-xs font-medium">
                  {i + 1}. {step}
                </span>
                {i < arr.length - 1 && <span className="text-muted-foreground">→</span>}
              </div>
            ))}
          </div>
          <div className="mt-4">
            <p className="text-xs font-medium text-muted-foreground">지원 문서 예시</p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {["사양서 (Equipment Specification)", "부하 목록 (Load List)", "단선 결선도 (Single Line Diagram)", "설비 스케줄 (Equipment Schedule)", "계산서 (Calculation Sheet)"].map((d) => (
                <span key={d} className="rounded-md border bg-background px-2 py-0.5 text-xs">
                  {d}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">문서 종류</span>
          <Select value={category} onValueChange={(v) => setCategory(v as DocCategory)}>
            <SelectTrigger className="w-64">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORY_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            handleFiles(e.dataTransfer.files);
          }}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
            dragActive ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40" : "border-muted-foreground/25 bg-card hover:bg-muted/30"
          }`}
        >
          {uploading ? (
            <Loader2 className="size-8 animate-spin text-blue-600 dark:text-blue-400" />
          ) : (
            <UploadCloud className="size-8 text-muted-foreground" />
          )}
          <div>
            <p className="text-sm font-medium">파일을 여기로 끌어다 놓거나 클릭해서 선택하세요</p>
            <p className="mt-1 text-xs text-muted-foreground">PDF · PNG/JPG · XLSX · CSV · TXT</p>
          </div>
          <input
            ref={inputRef}
            type="file"
            multiple
            hidden
            accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv,.txt"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>

        <div className="rounded-xl border bg-card p-5 shadow-sm">
          <h2 className="text-sm font-semibold">업로드된 문서 ({documents.length})</h2>
          {documents.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">아직 업로드된 문서가 없습니다.</p>
          ) : (
            <ul className="mt-3 divide-y">
              {documents.map((doc) => {
                const Icon = TYPE_ICON[doc.doc_type] ?? FileText;
                const statusMeta = STATUS_META[doc.status];
                return (
                  <li key={doc.id} className="flex items-center justify-between gap-4 py-3">
                    <div className="flex min-w-0 items-center gap-3">
                      {doc.status === "analyzed" ? (
                        <CheckCircle2 className="size-4 shrink-0 text-[#0ca30c]" />
                      ) : (
                        <Icon className="size-4 shrink-0 text-muted-foreground" />
                      )}
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{doc.filename}</p>
                        <p className="text-xs text-muted-foreground">
                          {CATEGORY_OPTIONS.find((c) => c.value === doc.category)?.label ?? doc.category}
                        </p>
                      </div>
                    </div>
                    <span className={`shrink-0 whitespace-nowrap rounded-full px-2 py-0.5 text-xs ${statusMeta.className}`}>
                      {statusMeta.label}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="rounded-xl border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-sm font-semibold">교차검증 실행</h2>
              <p className="text-xs text-muted-foreground">
                {isDemo
                  ? "데모 프로젝트는 미리 준비된 데이터를 사용하므로 교차검증을 다시 실행할 수 없습니다. 대시보드에서 결과를 확인하세요."
                  : "업로드된 문서에서 추출된 설비 데이터를 기준으로 문서 간 불일치를 검증하고 이슈를 생성합니다."}
              </p>
            </div>
            <Button
              onClick={handleRunCrossCheck}
              disabled={isDemo || documents.length === 0 || runningCrossCheck}
              className="shrink-0 gap-2 bg-blue-600 hover:bg-blue-700"
            >
              {runningCrossCheck ? <Loader2 className="size-4 animate-spin" /> : <PlayCircle className="size-4" />}
              교차검증 실행
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
