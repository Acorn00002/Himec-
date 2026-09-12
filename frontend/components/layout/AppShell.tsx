"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FlaskConical, LayoutDashboard, ListTree, ShieldAlert, Sparkles, UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCurrentProject } from "@/hooks/useCurrentProject";
import { ThemeToggle } from "@/components/theme-toggle";

function DataSourceBadge({ isDemo }: { isDemo: boolean }) {
  if (isDemo) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-violet-200 bg-violet-50 px-2 py-0.5 text-[11px] font-semibold text-violet-700 dark:border-violet-900 dark:bg-violet-950/40 dark:text-violet-300">
        <FlaskConical className="size-3" />
        데모 데이터 — 미리 준비된 샘플 (실제 파일 분석 아님)
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300">
      <Sparkles className="size-3" />
      실사용 모드 — 업로드한 문서에서 추출한 결과
    </span>
  );
}

const NAV = [
  { href: "/dashboard", label: "대시보드", icon: LayoutDashboard },
  { href: "/equipment", label: "설비 탐색", icon: ListTree },
  { href: "/upload", label: "문서 업로드", icon: UploadCloud },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { project, loading } = useCurrentProject();

  return (
    <div className="flex min-h-screen bg-muted/30">
      <aside className="hidden w-64 shrink-0 flex-col border-r bg-card md:flex">
        <div className="flex h-16 items-center gap-2 border-b px-5">
          <ShieldAlert className="size-5 text-blue-600 dark:text-blue-400" />
          <span className="text-sm font-semibold leading-tight">
            Engineering CrossCheck AI
            <br />
            <span className="text-xs font-medium text-muted-foreground">설계문서 교차검증</span>
          </span>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.map((item) => {
            const active = pathname?.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active ? "bg-blue-600 text-white" : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <Icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="space-y-2 border-t p-3">
          <ThemeToggle />
          <button
            onClick={() => router.push("/")}
            className="w-full rounded-md px-3 py-2 text-left text-xs text-muted-foreground hover:bg-accent"
          >
            ← 새 프로젝트 / 프로젝트 전환
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-6">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">
              {loading ? "불러오는 중…" : project?.name ?? "프로젝트"}
            </p>
            {!loading && project && (
              <div className="mt-1">
                <DataSourceBadge isDemo={project.is_demo} />
              </div>
            )}
          </div>
        </header>
        <div className="border-b bg-amber-50 px-6 py-2 text-xs text-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
          ⚠ AI 검토 결과이며 최종 설계 판단은 담당 엔지니어의 확인이 필요합니다. 이 시스템은 설계를 승인하지 않습니다.
        </div>
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
