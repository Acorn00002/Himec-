export type ProjectMode = "demo" | "live";

export interface Project {
  id: number;
  name: string;
  is_demo: boolean;
  mode: ProjectMode; // "demo" = 미리 준비된 샘플, "live" = 업로드 문서 기반
  created_at: string;
}

export type DocType = "pdf" | "image" | "xlsx" | "csv" | "txt";
export type DocCategory = "spec" | "drawing" | "calculation" | "equipment_list" | "pid" | "other";
export type DocStatus = "uploaded" | "parsed" | "analyzed";

export interface Document {
  id: number;
  project_id: number;
  filename: string;
  doc_type: DocType;
  category: DocCategory;
  status: DocStatus;
  uploaded_at: string;
}

export interface ParameterSourceValue {
  document_id: number;
  document_name: string;
  value: string;
  unit: string | null;
  location: string | null;
  raw_snippet: string | null;
}

export type ParameterStatus = "match" | "mismatch";

export interface ParameterRow {
  name: string; // 한글 표시 라벨 (예: "정격출력")
  key: string; // 정규화 키 (예: "Power") — 언어와 무관한 식별자
  sources: ParameterSourceValue[];
  status: ParameterStatus;
}

export interface EquipmentSummary {
  id: number;
  tag: string;
  equipment_type: string;
  document_count: number;
  issue_count: number;
  max_severity: Severity | null;
  top_issue_label: string | null; // 가장 높은 위험도 이슈 한 줄 요약
}

export type Severity = "HIGH" | "MEDIUM" | "LOW" | "INFO";

export interface IssueEvidenceItem {
  document: string;
  document_id: number | null;
  location: string | null;
  value: string;
  unit: string | null;
  raw_snippet: string | null;
}

export interface ExtractedChunk {
  id: number;
  document_id: number;
  location: string;
  content_type: "text" | "table";
  text: string;
}

export type IssueStatus = "open" | "reviewed" | "resolved";

// The reviewing engineer's call on an issue (Human-in-the-Loop).
export type IssueDisposition = "open" | "intentional" | "action_required" | "resolved";

export interface Issue {
  id: number;
  project_id: number;
  equipment_id: number | null;
  equipment_tag: string | null;
  parameter_name: string | null;
  parameter_label: string | null;
  issue_type: string;
  severity: Severity;
  title: string;
  description: string;
  reasoning: string;
  evidence: IssueEvidenceItem[];
  impact_items: string[];
  status: IssueStatus;
  disposition: IssueDisposition;
  review_comment: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface IssueReviewInput {
  disposition?: IssueDisposition;
  review_comment?: string;
  reviewed_by?: string;
}

export interface EquipmentDetail {
  id: number;
  tag: string;
  equipment_type: string;
  parameters: ParameterRow[];
  issues: Issue[];
}

export interface SeverityBreakdownEntry {
  severity: Severity;
  count: number;
}

export interface Dashboard {
  project_id: number;
  project_name: string;
  mode: ProjectMode;
  document_count: number;
  equipment_count: number;
  issue_count: number;
  high_risk_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  reviewed_count: number;
  open_count: number;
  review_progress_percent: number;
  severity_breakdown: SeverityBreakdownEntry[];
}
