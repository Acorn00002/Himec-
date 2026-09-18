"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { getProject } from "@/lib/api";
import type { Project } from "@/lib/types";

const STORAGE_KEY = "ecca_project_id";

export function getStoredProjectId(): number | null {
  if (typeof window === "undefined") return null;
  const v = window.localStorage.getItem(STORAGE_KEY);
  return v ? Number(v) : null;
}

export function setStoredProjectId(id: number) {
  window.localStorage.setItem(STORAGE_KEY, String(id));
}

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getServerSnapshot(): number | null {
  return null; // the server has no localStorage — this is also the client's pre-hydration value
}

export function useCurrentProject() {
  const router = useRouter();
  // useSyncExternalStore (not a useState lazy initializer) so the client's first paint
  // uses the same value as the server render (null) and only picks up the real stored id
  // after hydration — reading localStorage synchronously in useState() diverged from the
  // server-rendered HTML and crashed the dev server with a hydration-mismatch error.
  const projectId = useSyncExternalStore(subscribe, getStoredProjectId, getServerSnapshot);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) {
      router.replace("/");
      return;
    }
    getProject(projectId)
      .then(setProject)
      .catch(() => router.replace("/"))
      .finally(() => setLoading(false));
  }, [projectId, router]);

  return { projectId, project, loading };
}
