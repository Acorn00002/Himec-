"use client";

import { useEffect, useState } from "react";
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

export function useCurrentProject() {
  const router = useRouter();
  const [projectId] = useState<number | null>(() => getStoredProjectId());
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
