"use client";

import { useEffect, useSyncExternalStore } from "react";
import { Monitor, Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "theme";
const listeners = new Set<() => void>();

function readTheme(): Theme {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v === "light" || v === "dark" || v === "system") return v;
  } catch {}
  return "system";
}

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function applyToDocument(theme: Theme) {
  const dark = theme === "dark" || (theme === "system" && systemPrefersDark());
  document.documentElement.classList.toggle("dark", dark);
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  window.addEventListener("storage", cb);
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener("change", cb);
  return () => {
    listeners.delete(cb);
    window.removeEventListener("storage", cb);
    mq.removeEventListener("change", cb);
  };
}

// Snapshot changes whenever the stored choice OR the resolved dark state changes,
// so the button highlight and the <html> class both stay in sync — including when
// the OS theme flips while the app is open in "system" mode.
function getSnapshot(): string {
  return `${readTheme()}|${systemPrefersDark()}`;
}

function getServerSnapshot(): string {
  return "system|false";
}

function setTheme(next: Theme) {
  try {
    localStorage.setItem(STORAGE_KEY, next);
  } catch {}
  applyToDocument(next);
  listeners.forEach((l) => l());
}

const OPTIONS: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "라이트", icon: Sun },
  { value: "dark", label: "다크", icon: Moon },
  { value: "system", label: "시스템", icon: Monitor },
];

export function ThemeToggle() {
  const snap = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const current = snap.split("|")[0] as Theme;

  // Keep <html class="dark"> in sync — covers the case where the OS theme flips
  // while the app is open in "system" mode (snap changes -> effect re-runs).
  useEffect(() => {
    applyToDocument(current);
  }, [snap, current]);

  return (
    <div className="flex items-center gap-0.5 rounded-lg border bg-card p-0.5" role="group" aria-label="테마">
      {OPTIONS.map((opt) => {
        const Icon = opt.icon;
        const active = current === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => setTheme(opt.value)}
            aria-pressed={active}
            title={opt.label}
            className={cn(
              "flex flex-1 items-center justify-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors",
              active
                ? "bg-accent text-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className="size-3.5" />
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
