const API_BASE = import.meta.env.VITE_API_URL ?? "";

function apiUrl(path: string): string {
  if (API_BASE) {
    return `${API_BASE.replace(/\/$/, "")}${path}`;
  }
  return `/api${path}`;
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

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    /* ignore */
  }
  return `Erro ${response.status}`;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(apiUrl("/health"));
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<HealthResponse>;
}

export async function fetchAlertRules(): Promise<AlertRule[]> {
  const res = await fetch(apiUrl("/alert-rules"));
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<AlertRule[]>;
}

export async function createAlertRule(payload: AlertRuleCreate): Promise<AlertRule> {
  const res = await fetch(apiUrl("/alert-rules"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<AlertRule>;
}

export async function deleteAlertRule(id: number): Promise<void> {
  const res = await fetch(apiUrl(`/alert-rules/${id}`), { method: "DELETE" });
  if (!res.ok) throw new Error(await parseError(res));
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
  const res = await fetch(apiUrl("/integrations/status"));
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<IntegrationStatus>;
}

export async function importJobUrl(
  url: string,
  profileId?: number | null,
): Promise<JobImportResult> {
  const q = new URLSearchParams({ analyze: "true" });
  if (profileId != null) q.set("profile_id", String(profileId));
  const res = await fetch(apiUrl(`/jobs/import?${q}`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<JobImportResult>;
}

export async function listJobs(): Promise<JobRead[]> {
  const res = await fetch(apiUrl("/jobs"));
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<JobRead[]>;
}

export async function deleteJob(id: number): Promise<void> {
  const res = await fetch(apiUrl(`/jobs/${id}`), { method: "DELETE" });
  if (!res.ok) throw new Error(await parseError(res));
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
  const res = await fetch(apiUrl("/profiles"));
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<ProfileSummary[]>;
}

export async function fetchProfile(id: number): Promise<ProfileRead> {
  const res = await fetch(apiUrl(`/profiles/${id}`));
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<ProfileRead>;
}

export async function parseResume(file: File, useAi = true): Promise<ProfileRead> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(apiUrl(`/profiles/parse?use_ai=${useAi}`), {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<ProfileRead>;
}

export async function updateProfile(
  id: number,
  payload: {
    label?: string;
    structured: ProfileStructured;
    raw_text?: string;
  },
): Promise<ProfileRead> {
  const res = await fetch(apiUrl(`/profiles/${id}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<ProfileRead>;
}

export async function deleteProfile(id: number): Promise<void> {
  const res = await fetch(apiUrl(`/profiles/${id}`), { method: "DELETE" });
  if (!res.ok) throw new Error(await parseError(res));
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
  const res = await fetch(apiUrl(`/match/rank?${q}`));
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{ results: RankedJobMatch[]; profile_required: boolean }>;
}
