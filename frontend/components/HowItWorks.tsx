import { ArrowRight, Bot, Ruler } from "lucide-react";

const PIPELINE = [
  "문서 업로드",
  "설비 TAG 인식",
  "정보 추출",
  "문서 간 교차검증",
  "불일치 탐지",
  "영향 가능 항목 확인",
];

const ROLES: { icon: typeof Bot; title: string; items: string[]; tone: string }[] = [
  {
    icon: Bot,
    title: "AI가 하는 일",
    items: ["문서 내용 이해", "설비 TAG 식별", "관련 값 추출"],
    tone: "text-blue-700 border-blue-200 bg-blue-50/60 dark:text-blue-300 dark:border-blue-900 dark:bg-blue-950/40",
  },
  {
    icon: Ruler,
    title: "검증 엔진이 하는 일",
    items: ["수치 비교", "단위 환산·비교", "일치 / 불일치 판정"],
    tone: "text-emerald-700 border-emerald-200 bg-emerald-50/60 dark:text-emerald-300 dark:border-emerald-900 dark:bg-emerald-950/40",
  },
];

/**
 * Explains, for a first-time viewer, what the system actually does and where the
 * line between the language model and the deterministic checker sits.
 */
export function HowItWorks({ className }: { className?: string }) {
  return (
    <div className={className}>
      <h2 className="text-sm font-semibold">AI가 하는 일</h2>
      <p className="text-xs text-muted-foreground">
        PDF·Excel·도면 등 서로 다른 형식의 설계 문서에서 동일한 설비 TAG를 찾아 정보를 연결하고, 문서 간 값의 불일치를 검토합니다.
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-x-1.5 gap-y-2">
        {PIPELINE.map((step, i) => (
          <div key={step} className="flex items-center gap-1.5">
            <span className="rounded-md border bg-muted/50 px-2 py-1 text-xs font-medium">{step}</span>
            {i < PIPELINE.length - 1 && <ArrowRight className="size-3.5 shrink-0 text-muted-foreground" />}
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {ROLES.map((role) => {
          const Icon = role.icon;
          return (
            <div key={role.title} className={`rounded-lg border p-3 ${role.tone}`}>
              <p className="flex items-center gap-1.5 text-xs font-semibold">
                <Icon className="size-4" />
                {role.title}
              </p>
              <ul className="mt-1.5 space-y-0.5 text-xs text-foreground/80">
                {role.items.map((it) => (
                  <li key={it}>· {it}</li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      <p className="mt-3 text-xs text-muted-foreground">
        AI가 문서에서 정보를 추출하고, 수치 비교와 일치 여부 판정은 별도의 검증 로직이 수행합니다. AI가 임의의 숫자를 만들어내지 않습니다.
      </p>
    </div>
  );
}
