"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  FileSearch,
  GitCompareArrows,
  Loader2,
  Network,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ThemeToggle } from "@/components/theme-toggle";
import { createProject, loadDemoProject } from "@/lib/api";
import { setStoredProjectId } from "@/hooks/useCurrentProject";

const VALUE_PROPS = [
  {
    icon: FileSearch,
    title: "1. 흩어진 정보를 연결",
    body: "사양서 PDF, 도면, 계산서 Excel, 설비 목록 등 서로 다른 형식의 문서에서 같은 설비 TAG를 찾아 정보를 한곳에 모읍니다.",
  },
  {
    icon: GitCompareArrows,
    title: "2. 문서 간 불일치 탐지",
    body: "같은 설비의 같은 항목이 문서마다 다른 값으로 적혀 있는지 검증 엔진이 비교하고, 불일치·누락을 근거와 함께 제시합니다.",
  },
  {
    icon: Network,
    title: "3. 영향 가능 항목 확인",
    body: "그 불일치가 전류 계산·케이블·차단기 등 어떤 후속 설계 항목에 영향을 줄 수 있는지 흐름으로 보여줍니다.",
  },
];

export default function LandingPage() {
  const router = useRouter();
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [creating, setCreating] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  async function handleLoadDemo() {
    setLoadingDemo(true);
    try {
      const { project_id, message } = await loadDemoProject();
      setStoredProjectId(project_id);
      toast.success(message);
      router.push("/dashboard");
    } catch {
      toast.error("데모 프로젝트를 불러오지 못했습니다. 백엔드 서버가 실행 중인지 확인해주세요.");
    } finally {
      setLoadingDemo(false);
    }
  }

  async function handleCreateProject() {
    if (!projectName.trim()) return;
    setCreating(true);
    try {
      const project = await createProject(projectName.trim());
      setStoredProjectId(project.id);
      toast.success(`프로젝트 "${project.name}"를 생성했습니다.`);
      router.push("/upload");
    } catch {
      toast.error("프로젝트 생성에 실패했습니다.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="relative flex min-h-screen flex-col items-center bg-gradient-to-b from-white to-muted/40 px-6 py-16 dark:from-background dark:to-muted/20">
      <div className="fixed bottom-4 left-4 z-10">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-4xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border bg-card px-4 py-1.5 text-xs font-medium text-muted-foreground">
          <ShieldAlert className="size-3.5 text-blue-600 dark:text-blue-400" />
          설계 검토 보조 도구 — 설계를 승인하지 않고, 검토를 돕습니다
        </div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Engineering CrossCheck AI</h1>
        <p className="mt-2 text-sm font-medium text-muted-foreground">설계문서 교차검증 시스템</p>
        <p className="mx-auto mt-5 max-w-3xl text-balance text-lg text-muted-foreground">
          여러 설계 문서에 흩어진 <span className="font-semibold text-foreground">동일 설비의 정보</span>를 AI가 교차 검증하여
          문서 간 불일치와 영향 가능 항목을 찾아주는 <span className="font-semibold text-foreground">엔지니어링 검토 지원 시스템</span>입니다.
        </p>
        <p className="mx-auto mt-2 max-w-2xl text-sm text-muted-foreground">
          문서를 요약해주는 도구가 아니라, 문서들 사이의 <span className="font-medium">모순</span>을 찾아내는 도구입니다.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button size="lg" className="gap-2 bg-blue-600 hover:bg-blue-700" onClick={handleLoadDemo} disabled={loadingDemo}>
            {loadingDemo ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            데모 프로젝트 불러오기
          </Button>

          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger render={<Button size="lg" variant="outline" />}>새 프로젝트</DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>새 프로젝트 만들기</DialogTitle>
                <DialogDescription>
                  프로젝트 이름을 입력하면 설계 문서를 업로드할 수 있는 빈 프로젝트가 생성됩니다.
                </DialogDescription>
              </DialogHeader>
              <Input
                placeholder="예: OO 플랜트 전기설비 패키지"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreateProject()}
              />
              <DialogFooter>
                <Button onClick={handleCreateProject} disabled={creating || !projectName.trim()}>
                  {creating ? <Loader2 className="size-4 animate-spin" /> : "생성"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          데모 프로젝트는 발표용으로 미리 준비된 샘플 데이터입니다 — 실제 파일 분석 결과가 아닙니다.
          <br />
          모든 화면 상단에 데이터 출처(데모 / 실사용)가 표시됩니다.
        </p>
      </div>

      <div className="mt-20 grid w-full max-w-4xl gap-6 sm:grid-cols-3">
        {VALUE_PROPS.map((v) => (
          <div key={v.title} className="rounded-xl border bg-card p-5 text-left shadow-sm">
            <v.icon className="size-5 text-blue-600 dark:text-blue-400" />
            <h3 className="mt-3 text-sm font-semibold">{v.title}</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">{v.body}</p>
          </div>
        ))}
      </div>

      <p className="mt-16 max-w-2xl text-center text-xs text-muted-foreground">
        이 시스템은 설계를 승인하지 않습니다. 모든 AI 검토 결과는 근거 문서와 함께 제시되며,
        최종 설계 판단은 담당 엔지니어가 확인해야 합니다.
      </p>
    </main>
  );
}
