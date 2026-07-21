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
  score: string | number;
  percentile: number;
  potential: number;
  level: string;
  subject: { slug: string; title: string; color: string };
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
  roadmap?: {
    id: number;
    status: string;
    target_score: number;
    weekly_hours: number;
    primary_goal_title?: string | null;
  } | null;
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
  student: { username: "BILIM-2026", password: "student123", label: "O‘quvchi" },
  parent: { username: "parent", password: "parent123", label: "Ota-ona" },
  teacher: { username: "teacher", password: "teacher123", label: "O‘qituvchi" },
  admin: { username: "admin", password: "admin12345", label: "Administrator" },
};

export function hasLiveApi() {
  return Boolean(apiBase);
}

export function createDemoWorkspace(role: UserRole): WorkspaceSession {
  return { role, user: demoUsers[role], dashboard: demoDashboards[role], report: null, university_goal: null };
}

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("bilimyol_access");
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!apiBase) throw new Error("API manzili sozlanmagan.");
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${apiBase}${path}`, { ...options, headers });
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

export async function loginWorkspace(username: string, password: string): Promise<WorkspaceSession> {
  if (!apiBase) throw new Error("API manzili sozlanmagan.");
  const normalizedUsername = username === "BILIM-2026" ? "student" : username;
  const tokenResponse = await fetch(`${apiBase}/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: normalizedUsername, password }),
  });
  if (!tokenResponse.ok) throw new Error("Login yoki parol noto‘g‘ri.");
  const tokens = await tokenResponse.json() as { access: string; refresh: string };
  sessionStorage.setItem("bilimyol_access", tokens.access);
  sessionStorage.setItem("bilimyol_refresh", tokens.refresh);

  const [user, dashboard, reportPayload, goalPayload] = await Promise.all([
    apiRequest<LiveUser>("/auth/me/"),
    apiRequest<LiveDashboard>("/dashboard/"),
    apiRequest<PaginatedResponse<LiveDiagnosticReport> | LiveDiagnosticReport[]>("/reports/?page_size=1"),
    apiRequest<PaginatedResponse<LiveUniversityGoal> | LiveUniversityGoal[]>("/university-goals/?page_size=1"),
  ]);
  const reports = Array.isArray(reportPayload) ? reportPayload : reportPayload.results ?? [];
  const goals = Array.isArray(goalPayload) ? goalPayload : goalPayload.results ?? [];
  return { role: user.role, user, dashboard, report: reports[0] ?? null, university_goal: goals[0] ?? null };
}

export function clearApiSession() {
  sessionStorage.removeItem("bilimyol_access");
  sessionStorage.removeItem("bilimyol_refresh");
}
