import type {
  Dashboard,
  Document,
  EquipmentDetail,
  EquipmentSummary,
  ExtractedChunk,
  Issue,
  IssueReviewInput,
  Project,
  Severity,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function loadDemoProject() {
  return request<{ project_id: number; message: string }>("/api/demo/load", { method: "POST" });
}

export function createProject(name: string) {
  return request<Project>("/api/projects", { method: "POST", body: JSON.stringify({ name }) });
}

export function getProject(projectId: number) {
  return request<Project>(`/api/projects/${projectId}`);
}

export function getDashboard(projectId: number) {
  return request<Dashboard>(`/api/projects/${projectId}/dashboard`);
}

export function listEquipment(projectId: number) {
  return request<EquipmentSummary[]>(`/api/projects/${projectId}/equipment`);
}

export function getEquipmentDetail(projectId: number, tag: string) {
  return request<EquipmentDetail>(`/api/projects/${projectId}/equipment/${encodeURIComponent(tag)}`);
}

export function listIssues(projectId: number, severity?: Severity) {
  const qs = severity ? `?severity=${severity}` : "";
  return request<Issue[]>(`/api/projects/${projectId}/issues${qs}`);
}

export function getIssue(issueId: number) {
  return request<Issue>(`/api/issues/${issueId}`);
}

export function updateIssueReview(issueId: number, input: IssueReviewInput) {
  return request<Issue>(`/api/issues/${issueId}/review`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function listDocuments(projectId: number) {
  return request<Document[]>(`/api/projects/${projectId}/documents`);
}

export function getDocumentContent(projectId: number, documentId: number) {
  return request<ExtractedChunk[]>(`/api/projects/${projectId}/documents/${documentId}/content`);
}

export function uploadDocument(projectId: number, file: File, category: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("category", category);
  return request<Document>(`/api/projects/${projectId}/documents`, { method: "POST", body: form });
}

export interface CrossCheckRunResult {
  issue_count: number;
  high_risk_count: number;
  equipment_count: number;
}

export function runCrossCheck(projectId: number) {
  return request<CrossCheckRunResult>(`/api/projects/${projectId}/crosscheck/run`, { method: "POST" });
}

export { ApiError };
