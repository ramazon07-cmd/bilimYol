export type UserRole = "student" | "parent" | "teacher" | "admin";

export type LiveUser = {
  id: number;
  username: string;
  full_name: string;
  role: UserRole;
  email?: string;
  phone?: string;
  avatar_url?: string;
};

export type LiveSubjectResult = {
  id?: number;
  earned_points?: string | number;
  possible_points?: string | number;
  weight_percent?: string | number;
  score: string | number;
  percentile: number;
  potential: number;
  level: string;
  subject: { id?: number; slug: string; title: string; color: string };
};

export type LiveBreakdownResult = {
  id: number;
  earned_points: string | number;
  possible_points: string | number;
  score: string | number;
  question_count: number;
  confidence: string;
  topic?: { id: number; code: string; title: string; subject?: number };
  skill?: { id: number; slug: string; title: string; subject?: number };
};

export type LiveAnswerSummary = {
  total: number;
  correct: number;
  incorrect: number;
  unanswered: number;
};

export type LiveQuestionReview = {
  exam_question_id: number;
  code: string;
  context: string;
  prompt: string;
  subject: { id: number; slug: string; title: string };
  topic: { id: number; code: string; title: string };
  skills: { id: number; slug: string; title: string }[];
  difficulty: "basic" | "medium" | "high";
  points: string | number;
  selected_option: { id: number; label: string; text: string } | null;
  correct_option?: { id: number; label: string; text: string } | null;
  is_answered: boolean;
  is_correct: boolean;
  earned_points: string | number;
  is_flagged: boolean;
  answered_at: string | null;
  explanation?: string;
};

export type LivePreviousAttempt = {
  id: number;
  attempt_id: number;
  exam_id: number;
  exam_title: string;
  overall_score: string | number;
  readiness: "ready" | "not_ready";
  generated_at: string;
  same_exam: boolean;
};

export type LiveComparisonRow = {
  id: number;
  title: string;
  current_score: number;
  previous_score: number;
  delta: number;
};

export type LiveReportComparison = {
  current: { id: number; exam_title: string; overall_score: string | number; generated_at: string };
  previous: { id: number; exam_title: string; overall_score: string | number; generated_at: string };
  overall_delta: number;
  subjects: LiveComparisonRow[];
  topics: LiveComparisonRow[];
  skills: LiveComparisonRow[];
};

export type LiveDiagnosticReport = {
  id: number;
  overall_score: string | number;
  range_low: string | number;
  range_high: string | number;
  expected_score: string | number;
  readiness: "ready" | "not_ready";
  summary?: string;
  generated_at?: string;
  student: { id?: number; full_name: string; username: string };
  exam?: { id: number; title: string; grade: number | null; purpose?: string };
  subject_results: LiveSubjectResult[];
  topic_results?: LiveBreakdownResult[];
  skill_results?: LiveBreakdownResult[];
  grade?: number | null;
  classroom?: { id: number; name: string; grade: number } | null;
  answer_summary?: LiveAnswerSummary;
  roadmap?: {
    id: number;
    status: string;
    target_score: number;
    weekly_hours: number;
    primary_goal_title?: string | null;
    admin_note?: string;
    stages?: {
      id: number;
      order: number;
      title: string;
      start_month: number;
      end_month: number;
      start_score: number;
      target_score: number;
      weekly_hours: number;
      rationale: string;
      subject?: { title: string };
      focus_topic?: { title: string };
    }[];
  } | null;
};

export type LiveDiagnosticReportDetail = LiveDiagnosticReport & {
  attempt_detail: {
    id: number;
    assignment_id: number;
    status: string;
    started_at: string;
    submitted_at: string | null;
    expires_at: string;
    started_by: string | null;
    submitted_by: string | null;
    earned_points: string | number;
    delivery_mode: string;
  };
  question_review: LiveQuestionReview[];
  strengths: { kind: "skill" | "topic"; title: string; subject: string; score: string | number }[];
  weaknesses: { kind: "skill" | "topic"; title: string; subject: string; score: string | number }[];
  previous_attempts: LivePreviousAttempt[];
};

export type LiveDashboard = {
  role: UserRole;
  students: number;
  active_assignments: number;
  completed_attempts: number;
  average_score: string | number;
  readiness: { readiness: "ready" | "not_ready"; count: number }[];
};

export type LiveUniversityRequirement = {
  key: string;
  label: string;
  current: number;
  target: number;
  unit: string;
  source: "mock" | "certificate";
  progress: number;
  complete: boolean;
  has_certificate?: boolean | null;
};

export type LiveUniversityGoal = {
  id: number;
  target_year: number;
  university_detail: { id: number; name: string; country: string; city: string };
  progress: {
    overall: number;
    status: string;
    latest_mock: string | null;
    latest_mock_score: number | null;
    requirements: LiveUniversityRequirement[];
  };
};

export type WorkspaceSession = {
  role: UserRole;
  user: LiveUser;
  dashboard: LiveDashboard;
  report: LiveDiagnosticReport | null;
  university_goal: LiveUniversityGoal | null;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

const demoUsers: Record<UserRole, LiveUser> = {
  student: { id: 1, username: "student", full_name: "Bobur Xasanboyev", role: "student", email: "student@bilimyol.uz" },
  parent: { id: 2, username: "parent", full_name: "Dilnoza Xasanboyeva", role: "parent", email: "parent@bilimyol.uz" },
  teacher: { id: 3, username: "teacher", full_name: "Madina Karimova", role: "teacher", email: "teacher@bilimyol.uz" },
  admin: { id: 4, username: "admin", full_name: "Azizbek Rahimov", role: "admin", email: "admin@bilimyol.uz" },
};

const demoDashboards: Record<UserRole, LiveDashboard> = {
  student: { role: "student", students: 1, active_assignments: 3, completed_attempts: 1, average_score: 41, readiness: [{ readiness: "not_ready", count: 1 }] },
  parent: { role: "parent", students: 1, active_assignments: 3, completed_attempts: 1, average_score: 41, readiness: [{ readiness: "not_ready", count: 1 }] },
  teacher: { role: "teacher", students: 24, active_assignments: 18, completed_attempts: 21, average_score: 63.4, readiness: [{ readiness: "ready", count: 9 }, { readiness: "not_ready", count: 15 }] },
  admin: { role: "admin", students: 486, active_assignments: 312, completed_attempts: 428, average_score: 67.8, readiness: [{ readiness: "ready", count: 214 }, { readiness: "not_ready", count: 214 }] },
};

export const demoCredentials: Record<UserRole, { username: string; password: string; label: string }> = {
  student: { username: "", password: "", label: "O‘quvchi" },
  parent: { username: "", password: "", label: "Ota-ona" },
  teacher: { username: "", password: "", label: "O‘qituvchi" },
  admin: { username: "", password: "", label: "Administrator" },
};

export function hasLiveApi() {
  return Boolean(apiBase);
}

export function hasDemoMode() {
  return process.env.NEXT_PUBLIC_ENABLE_DEMO_MODE === "true";
}

export function createDemoWorkspace(role: UserRole): WorkspaceSession {
  return { role, user: demoUsers[role], dashboard: demoDashboards[role], report: null, university_goal: null };
}

const ACCESS_TOKEN_KEY = "bilimyol_access";
const REFRESH_TOKEN_KEY = "bilimyol_refresh";

function readStoredToken(key: string) {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key) ?? window.sessionStorage.getItem(key);
}

function storeTokens(tokens: { access: string; refresh?: string }) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  if (tokens.refresh) window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getAccessToken() {
  return readStoredToken(ACCESS_TOKEN_KEY);
}

function getRefreshToken() {
  return readStoredToken(REFRESH_TOKEN_KEY);
}

async function refreshAccessToken() {
  if (!apiBase) return null;
  const refresh = getRefreshToken();
  if (!refresh) return null;

  const response = await fetch(`${apiBase}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) return null;
  const tokens = await response.json() as { access: string; refresh?: string };
  storeTokens({ access: tokens.access, refresh: tokens.refresh ?? refresh });
  return tokens.access;
}

async function fetchWithAuth(path: string, options: RequestInit, allowRefresh = true) {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  const access = getAccessToken();
  if (access) headers.set("Authorization", `Bearer ${access}`);

  let response = await fetch(`${apiBase}${path}`, { ...options, headers });
  if (response.status === 401 && allowRefresh) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      headers.set("Authorization", `Bearer ${newAccess}`);
      response = await fetch(`${apiBase}${path}`, { ...options, headers });
    }
  }
  return response;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!apiBase) throw new Error("API manzili sozlanmagan.");
  const response = await fetchWithAuth(path, options);
  const payload = await response.json().catch(() => null) as Record<string, unknown> | null;
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : null;
    const fieldEntries = payload ? Object.entries(payload) : [];
    const firstFieldEntry = fieldEntries.find(([, value]) => Array.isArray(value) && typeof value[0] === "string");

    const fieldName = firstFieldEntry?.[0] ?? "";
    const rawFieldMessage = firstFieldEntry && Array.isArray(firstFieldEntry[1])
      ? String(firstFieldEntry[1][0])
      : null;

    const translatedFieldMessage = fieldName === "weekly_study_hours"
      ? "Haftalik vaqt 1 dan 50 soatgacha bo‘lishi kerak."
      : fieldName === "target_score"
        ? "Maqsad balli 0 dan 100 gacha bo‘lishi kerak."
        : fieldName === "username"
          ? "Bu login band yoki noto‘g‘ri kiritilgan."
          : rawFieldMessage;

    throw new Error(detail ?? translatedFieldMessage ?? "Server bilan ishlashda xatolik yuz berdi.");
  }
  return payload as T;
}

async function loadWorkspaceSession(): Promise<WorkspaceSession> {
  const [user, dashboard] = await Promise.all([
    apiRequest<LiveUser>("/auth/me/"),
    apiRequest<LiveDashboard>("/dashboard/"),
  ]);

  const [reportResult, goalResult] = await Promise.allSettled([
    apiRequest<PaginatedResponse<LiveDiagnosticReport> | LiveDiagnosticReport[]>("/reports/?page_size=1"),
    apiRequest<PaginatedResponse<LiveUniversityGoal> | LiveUniversityGoal[]>("/university-goals/?page_size=1"),
  ]);

  const reportPayload = reportResult.status === "fulfilled" ? reportResult.value : [];
  const goalPayload = goalResult.status === "fulfilled" ? goalResult.value : [];
  const reports = Array.isArray(reportPayload) ? reportPayload : reportPayload.results ?? [];
  const goals = Array.isArray(goalPayload) ? goalPayload : goalPayload.results ?? [];

  return { role: user.role, user, dashboard, report: reports[0] ?? null, university_goal: goals[0] ?? null };
}

export async function loginWorkspace(username: string, password: string): Promise<WorkspaceSession> {
  if (!apiBase) throw new Error("API manzili sozlanmagan.");
  const tokenResponse = await fetch(`${apiBase}/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!tokenResponse.ok) throw new Error("Login yoki parol noto‘g‘ri.");
  const tokens = await tokenResponse.json() as { access: string; refresh: string };
  storeTokens(tokens);
  return loadWorkspaceSession();
}

export async function restoreWorkspaceSession(): Promise<WorkspaceSession | null> {
  if (!apiBase || (!getAccessToken() && !getRefreshToken())) return null;
  try {
    return await loadWorkspaceSession();
  } catch {
    clearApiSession();
    return null;
  }
}

export function clearApiSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}
