import { useUserStore } from '@/stores/user';
import type {
  UserCreate, UserResponse,
  ProjectCreate, ProjectResponse, ProjectBriefUpdate,
  ClaimSearchResult, ClaimResponse,
  AssetResponse,
  GenerateRequest, GenerateResponse,
  EditRequest, EditResponse,
  DirectEditRequest, AssetSwapRequest, RevertRequest,
  VersionSummary, VersionResponse,
  CommentCreate, CommentResponse, CommentResolve,
  ExportResponse,
} from '@/types';

const API_BASE = '/api';

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const userId = useUserStore.getState().userId;
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId,
      ...opts.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as Record<string, string>).detail || `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// Users
export function createUser(data: UserCreate): Promise<UserResponse> {
  return request('/users/', { method: 'POST', body: JSON.stringify(data) });
}

export function getMe(): Promise<UserResponse> {
  return request('/users/me');
}

export function getUser(id: string): Promise<UserResponse> {
  return request(`/users/${id}`);
}

// Projects
export function createProject(data: ProjectCreate): Promise<ProjectResponse> {
  return request('/projects/', { method: 'POST', body: JSON.stringify(data) });
}

export function getProject(id: string): Promise<ProjectResponse> {
  return request(`/projects/${id}`);
}

export function updateBrief(id: string, data: ProjectBriefUpdate): Promise<ProjectResponse> {
  return request(`/projects/${id}/brief`, { method: 'PATCH', body: JSON.stringify(data) });
}

// Claims
export function discoverClaims(query: string): Promise<ClaimSearchResult[]> {
  return request(`/claims/discover?${new URLSearchParams({ q: query })}`);
}

export function searchClaims(query: string): Promise<ClaimSearchResult[]> {
  return request(`/claims/search?${new URLSearchParams({ q: query })}`);
}

export function getAllClaims(): Promise<ClaimResponse[]> {
  return request('/claims/all');
}

// Assets
export function getAssets(assetType?: string): Promise<AssetResponse[]> {
  const params = assetType ? `?${new URLSearchParams({ asset_type: assetType })}` : '';
  return request(`/assets/${params}`);
}

export function searchAssets(query: string): Promise<AssetResponse[]> {
  return request(`/assets/search?${new URLSearchParams({ q: query })}`);
}

export function getAsset(id: string): Promise<AssetResponse> {
  return request(`/assets/${id}`);
}

// Content
export function generateContent(projectId: string, data: GenerateRequest): Promise<GenerateResponse> {
  return request(`/content/${projectId}/generate`, { method: 'POST', body: JSON.stringify(data) });
}

export function editContent(projectId: string, data: EditRequest): Promise<EditResponse> {
  return request(`/content/${projectId}/edit`, { method: 'POST', body: JSON.stringify(data) });
}

export function directEditContent(projectId: string, data: DirectEditRequest): Promise<EditResponse> {
  return request(`/content/${projectId}/direct-edit`, { method: 'POST', body: JSON.stringify(data) });
}

export function swapAsset(projectId: string, data: AssetSwapRequest): Promise<EditResponse> {
  return request(`/content/${projectId}/swap-asset`, { method: 'POST', body: JSON.stringify(data) });
}

export function getVersions(projectId: string): Promise<VersionSummary[]> {
  return request(`/content/${projectId}/versions`);
}

export function getVersion(projectId: string, versionId: string): Promise<VersionResponse> {
  return request(`/content/${projectId}/versions/${versionId}`);
}

export function revertVersion(projectId: string, data: RevertRequest): Promise<VersionResponse> {
  return request(`/content/${projectId}/revert`, { method: 'POST', body: JSON.stringify(data) });
}

// Comments
export function createComment(contentVersionId: string, data: CommentCreate): Promise<CommentResponse> {
  return request(`/comments/?${new URLSearchParams({ content_version_id: contentVersionId })}`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getComments(versionId: string): Promise<CommentResponse[]> {
  return request(`/comments/version/${versionId}`);
}

export function resolveComment(id: string, data: CommentResolve): Promise<CommentResponse> {
  return request(`/comments/${id}/resolve`, { method: 'PATCH', body: JSON.stringify(data) });
}

// Export
export function exportVersion(versionId: string): Promise<ExportResponse> {
  return request(`/export/${versionId}`, { method: 'POST' });
}

// SSE Streaming
export function streamGenerate(
  data: GenerateRequest,
  projectId: string,
  onToken: (token: string) => void,
  onComplete: (fullHtml: string) => void,
  onError: (error: string) => void,
): AbortController {
  const controller = new AbortController();
  const userId = useUserStore.getState().userId;

  fetch(`${API_BASE}/content/${projectId}/generate/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-Id': userId },
    body: JSON.stringify(data),
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      onError((body as Record<string, string>).detail || `API error ${res.status}`);
      return;
    }
    if (!res.body) {
      onError('No response body');
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop()!;
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const payload = JSON.parse(line.slice(6)) as {
            error?: string;
            type?: string;
            content?: string;
          };
          if (payload.error) { onError(payload.error); return; }
          if (payload.type === 'token' && payload.content) onToken(payload.content);
          if (payload.type === 'complete' && payload.content) onComplete(payload.content);
        } catch {
          onError('Malformed SSE data');
          return;
        }
      }
    }
  }).catch((err: Error) => {
    if (err.name !== 'AbortError') onError(err.message);
  });

  return controller;
}
