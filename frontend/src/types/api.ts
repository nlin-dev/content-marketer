import type {
  UserRole, ContentType, Audience, Goal, Tone,
  ProjectStatus, ClaimCategory, AssetType, ComplianceStatus, EventType,
} from './enums';

export interface UserResponse {
  id: string;
  display_name: string;
  email: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  display_name: string;
  email: string;
  role?: UserRole;
}

export interface ProjectCreate {
  name: string;
  content_type: ContentType;
  audience: Audience;
  goal: Goal;
  tone: Tone;
}

export interface ProjectBriefUpdate {
  brief_responses: Record<string, unknown>;
}

export interface ProjectResponse {
  id: string;
  name: string;
  content_type: ContentType;
  audience: Audience;
  goal: Goal;
  tone: Tone;
  status: ProjectStatus;
  brief_responses: Record<string, unknown> | null;
  user_id: string;
  user: UserResponse | null;
  created_at: string;
  updated_at: string;
}

export interface ClaimSourceResponse {
  source_id: string;
}

export interface ClaimResponse {
  id: string;
  text: string;
  category: ClaimCategory;
  sources: ClaimSourceResponse[];
  is_active: boolean;
  created_at: string;
}

export interface ClaimSearchResult {
  claim: ClaimResponse;
  distance: number;
}

export interface AssetResponse {
  id: string;
  name: string;
  asset_type: AssetType;
  file_url: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface AssetSearchResult {
  asset: AssetResponse;
  relevance: number;
}

export interface ComplianceCheckResponse {
  id: string;
  content_version_id: string;
  check_name: string;
  status: ComplianceStatus;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface ComplianceReportResponse {
  checks: ComplianceCheckResponse[];
  overall_status: ComplianceStatus;
}

export interface CommentCreate {
  text: string;
  anchor_selector?: string | null;
  parent_comment_id?: string | null;
}

export interface CommentResponse {
  id: string;
  content_version_id: string;
  user_id: string;
  parent_comment_id: string | null;
  text: string;
  anchor_selector: string | null;
  resolved: boolean;
  created_at: string;
  updated_at: string;
}

export interface CommentResolve {
  resolved: boolean;
}

export interface GenerateRequest {
  claim_ids: string[];
  asset_ids: string[];
}

export interface EditRequest {
  instruction: string;
}

export interface DirectEditRequest {
  html_content: string;
}

export interface AssetSwapRequest {
  old_asset_id: string;
  new_asset_id: string;
}

export interface RevertRequest {
  target_version_id: string;
}

export interface VersionSummary {
  id: string;
  version_number: number;
  edit_instruction: string | null;
  created_at: string;
}

export interface VersionResponse {
  id: string;
  project_id: string;
  parent_version_id: string | null;
  version_number: number;
  html_content: string;
  edit_instruction: string | null;
  created_at: string;
  claim_ids: string[];
  asset_ids: string[];
  compliance_checks: ComplianceCheckResponse[];
}

export interface GenerateResponse {
  version: VersionResponse;
}

export interface EditResponse {
  version: VersionResponse;
}

export interface ExportResponse {
  project_name: string;
  html_content: string;
  version_number: number;
  compliance_status: string;
  exported_at: string;
}

export interface AuditLogResponse {
  id: string;
  event_type: EventType;
  user_id: string | null;
  project_id: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
}
