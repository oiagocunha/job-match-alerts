const API_BASE = (import.meta.env.VITE_API_URL ?? "").trim().replace(/\/$/, "");

/** Em produção na Vercel, VITE_API_URL precisa apontar para o Render (definida antes do build). */
export function isApiConfigured(): boolean {
  return Boolean(API_BASE) || import.meta.env.DEV;
}

export function getApiConfigError(): string | null {
  if (import.meta.env.DEV) return null;
  if (!API_BASE) {
    return (
      "API não configurada: na Vercel, defina VITE_API_URL=https://job-match-alerts.onrender.com " +
      "(Environment Variables) e faça Redeploy — variáveis VITE_ só entram no build."
    );
  }
  return null;
}

function apiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (API_BASE) {
    return `${API_BASE}${normalized}`;
  }
  if (import.meta.env.DEV) {
    return `/api${normalized}`;
  }
  throw new Error(getApiConfigError() ?? "API não configurada.");
}

async function readJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  const trimmed = text.trimStart();
  if (trimmed.startsWith("<") || trimmed.startsWith("<!")) {
    throw new Error(
      "A API respondeu HTML em vez de JSON. Confira: (1) VITE_API_URL na Vercel = URL do Render, " +
        "sem barra no final e sem /api; (2) Redeploy após salvar a variável; " +
        "(3) CORS_ORIGINS no Render inclui a URL da Vercel.",
    );
  }
  if (!text) {
    throw new Error(`Resposta vazia da API (${res.status}).`);
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(`JSON inválido (${res.status}): ${text.slice(0, 160)}`);
  }
}

async function parseError(response: Response): Promise<string> {
  const text = await response.text();
  if (text.trimStart().startsWith("<")) {
    return (
      "API retornou HTML (página do site). Verifique VITE_API_URL na Vercel e redeploy."
    );
  }
  try {
    const body = JSON.parse(text) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    /* ignore */
  }
  return `Erro ${response.status}`;
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), init);
  if (!res.ok) throw new Error(await parseError(res));
  if (res.status === 204) return undefined as T;
  return readJson<T>(res);
}

export type AlertFrequency = "daily" | "weekly";

export interface AlertRule {
  id: number;
  demo_user_id: string;
  name: string;
  keywords: string | null;
  remote_only: boolean;
  min_score: number;
  frequency: AlertFrequency;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertRuleCreate {
  name: string;
  keywords?: string | null;
  remote_only?: boolean;
  min_score?: number;
  frequency?: AlertFrequency;
  is_active?: boolean;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

export async function fetchAlertRules(): Promise<AlertRule[]> {
  return apiRequest<AlertRule[]>("/alert-rules");
}

export async function createAlertRule(payload: AlertRuleCreate): Promise<AlertRule> {
  return apiRequest<AlertRule>("/alert-rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteAlertRule(id: number): Promise<void> {
  await apiRequest<void>(`/alert-rules/${id}`, { method: "DELETE" });
}

export interface IntegrationCheck {
  configured: boolean;
  ok: boolean;
  message: string;
}

export interface IntegrationStatus {
  openai: IntegrationCheck;
}

export interface JobRead {
  id: number;
  external_id: string;
  source: string;
  title: string;
  company: string | null;
  description: string;
  location: string | null;
  url: string | null;
  seniority: string | null;
  is_remote: boolean | null;
}

export interface MatchBreakdown {
  skills: number;
  seniority: number;
  experience: number;
  semantic_match: number;
}

export interface MatchResult {
  score: number;
  breakdown: MatchBreakdown;
  matched: string[];
  missing: string[];
  job_seniority: string;
  candidate_seniority: string;
  explanation: string[];
}

export interface JobImportResult {
  job: JobRead;
  match: MatchResult | null;
  profile_required: boolean;
}

export async function fetchIntegrationsStatus(): Promise<IntegrationStatus> {
  return apiRequest<IntegrationStatus>("/integrations/status");
}

export async function importJobUrl(
  url: string,
  profileId?: number | null,
): Promise<JobImportResult> {
  const q = new URLSearchParams({ analyze: "true" });
  if (profileId != null) q.set("profile_id", String(profileId));
  return apiRequest<JobImportResult>(`/jobs/import?${q}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

export async function listJobs(): Promise<JobRead[]> {
  return apiRequest<JobRead[]>("/jobs");
}

export async function deleteJob(id: number): Promise<void> {
  await apiRequest<void>(`/jobs/${id}`, { method: "DELETE" });
}

export interface ProfileStructured {
  name: string | null;
  email: string | null;
  headline: string | null;
  skills: string[];
  experience_years: Record<string, number>;
  seniority: string;
  languages: string[];
  education: string[];
  experiences: Record<string, unknown>[];
}

export interface ProfileSummary {
  id: number;
  label: string;
  name: string | null;
  headline: string | null;
  skills_count: number;
  seniority: string;
  source_filename: string | null;
  updated_at: string;
}

export interface ProfileRead {
  id: number;
  demo_user_id: string;
  label: string;
  raw_text: string | null;
  structured: ProfileStructured;
  source_filename: string | null;
  created_at: string;
  updated_at: string;
}

export async function listProfiles(): Promise<ProfileSummary[]> {
  return apiRequest<ProfileSummary[]>("/profiles");
}

export async function fetchProfile(id: number): Promise<ProfileRead> {
  return apiRequest<ProfileRead>(`/profiles/${id}`);
}

export async function parseResume(file: File, useAi = true): Promise<ProfileRead> {
  const form = new FormData();
  form.append("file", file);
  return apiRequest<ProfileRead>(`/profiles/parse?use_ai=${useAi}`, {
    method: "POST",
    body: form,
  });
}

export async function updateProfile(
  id: number,
  payload: {
    label?: string;
    structured: ProfileStructured;
    raw_text?: string;
  },
): Promise<ProfileRead> {
  return apiRequest<ProfileRead>(`/profiles/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteProfile(id: number): Promise<void> {
  await apiRequest<void>(`/profiles/${id}`, { method: "DELETE" });
}

export interface RankedJobMatch {
  job_id: number;
  title: string;
  company: string | null;
  source: string;
  url: string | null;
  is_remote: boolean | null;
  seniority: string | null;
  match: MatchResult;
}

export async function fetchMatchRank(params: {
  profile_id?: number | null;
  remote_only?: boolean;
  seniority?: string;
  min_score?: number;
  limit?: number;
}): Promise<{ results: RankedJobMatch[]; profile_required: boolean }> {
  const q = new URLSearchParams();
  if (params.profile_id != null) q.set("profile_id", String(params.profile_id));
  if (params.remote_only) q.set("remote_only", "true");
  if (params.seniority && params.seniority !== "any") q.set("seniority", params.seniority);
  if (params.min_score != null) q.set("min_score", String(params.min_score));
  if (params.limit) q.set("limit", String(params.limit));
  return apiRequest<{ results: RankedJobMatch[]; profile_required: boolean }>(
    `/match/rank?${q}`,
  );
}
