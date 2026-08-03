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
  image_url?: string;
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
  exam_title?: string;
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
  batch_id?: string | null;
  batch_order?: number;
  batch_size?: number;
  is_combined?: boolean;
  component_report_ids?: number[];
  component_reports?: {
    id: number;
    exam?: { id: number; title: string; grade: number | null };
    overall_score: string | number;
    generated_at?: string;
    batch_order?: number;
  }[];
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
  question_review?: LiveQuestionReview[];
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
  student: number;
  target_year: number;
  university: number;
  university_detail: LiveUniversity;
  progress: {
    overall: number;
    status: string;
    latest_mock: string | null;
    latest_mock_score: number | null;
    requirements: LiveUniversityRequirement[];
  };
};

export type LiveUniversity = {
  id: number;
  name: string;
  country: string;
  city: string;
  logo_url?: string;
  target_math: number;
  target_english: number;
  target_iq: number;
  target_ielts: string | number;
  target_sat: number;
  is_active: boolean;
};

export type LiveCertificate = {
  id: number;
  student: number;
  student_detail: LiveUser;
  kind: "ielts" | "sat" | "cefr" | "other";
  title: string;
  score: string | number;
  issued_at: string;
  expires_at: string | null;
  file_url: string;
  is_verified: boolean;
  verification_status: "pending" | "verified" | "rejected";
  verification_note: string;
  reviewed_at: string | null;
  verified_by_name: string | null;
  created_at: string;
};

export type LiveWeeklyTask = {
  id: number;
  stage: number;
  week_number: number;
  audience: "student" | "parent" | "teacher";
  title: string;
  description: string;
  resource_url: string;
  is_completed: boolean;
  completed_at: string | null;
};

export type LiveRoadmapStage = {
  id: number;
  order: number;
  title: string;
  start_month: number;
  end_month: number;
  start_score: number;
  target_score: number;
  weekly_hours: number;
  rationale: string;
  subject?: { id: number; slug: string; title: string; color: string };
  focus_topic?: { id: number; title: string };
  weekly_tasks: LiveWeeklyTask[];
};

export type LiveRoadmap = {
  id: number;
  report: number;
  student: number;
  student_detail: LiveUser;
  teacher_detail: LiveUser | null;
  primary_goal_title: string | null;
  target_score: number;
  weekly_hours: number;
  status: "draft" | "approved" | "active" | "completed";
  approved_at: string | null;
  admin_note: string;
  stages: LiveRoadmapStage[];
  created_at: string;
  updated_at: string;
};

export type LiveClassroom = {
  id: number;
  name: string;
  grade: number;
  program: string;
  teacher: number | null;
  teacher_detail: LiveUser | null;
  is_active: boolean;
  student_count: number;
  enrollments: {
    id: number;
    student: number;
    student_detail: LiveUser;
    joined_at: string;
  }[];
};

export type LiveAssignment = {
  id: number;
  batch_id?: string | null;
  batch_order?: number;
  batch_size?: number;
  exam: number;
  exam_detail: {
    id: number;
    title: string;
    grade: number | null;
    duration_minutes: number;
    question_count: number;
    exam_questions?: unknown[];
  };
  classroom: number | null;
  classroom_detail: LiveClassroom | null;
  student: number;
  student_detail: LiveUser;
  available_from: string | null;
  due_at: string | null;
  is_active: boolean;
  delivery_mode: "self" | "administered";
  has_attempt: boolean;
  created_at: string;
};

export type LiveParentStudent = {
  id: number;
  parent: number;
  parent_detail: LiveUser;
  student: number;
  student_detail: LiveUser;
  relationship: string;
  created_at: string;
};

export type LiveNotification = {
  id: number;
  kind: "assignment" | "result" | "roadmap" | "university" | "certificate" | "message" | "system";
  title: string;
  message: string;
  action_path: string;
  metadata: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type LiveMessage = {
  id: number;
  conversation: number;
  sender: number;
  sender_detail: LiveUser;
  body: string;
  created_at: string;
};

export type LiveConversation = {
  id: number;
  kind: "teacher" | "academic";
  title: string;
  student: number;
  student_detail: LiveUser;
  parent: number;
  parent_detail: LiveUser;
  teacher: number | null;
  teacher_detail: LiveUser | null;
  messages: LiveMessage[];
  last_message: LiveMessage | null;
  created_at: string;
  updated_at: string;
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

export const roleLoginDefaults: Record<UserRole, { username: string; password: string; label: string }> = {
  student: { username: "", password: "", label: "O‘quvchi" },
  parent: { username: "", password: "", label: "Ota-ona" },
  teacher: { username: "", password: "", label: "O‘qituvchi" },
  admin: { username: "", password: "", label: "Administrator" },
};

export function hasLiveApi() {
  return Boolean(apiBase);
}

const ACCESS_TOKEN_KEY = "bilimyol_access";
const REFRESH_TOKEN_KEY = "bilimyol_refresh";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

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

  if (!response.ok) {
    if (response.status === 400 || response.status === 401) return null;
    throw new ApiError("Sessiyani yangilashda server xatosi yuz berdi.", response.status);
  }
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
          : fieldName === "password"
            ? "Parol kamida 8 belgidan iborat va yetarlicha murakkab bo‘lishi kerak."
          : rawFieldMessage;

    throw new ApiError(
      detail ?? translatedFieldMessage ?? "Server bilan ishlashda xatolik yuz berdi.",
      response.status,
    );
  }
  return payload as T;
}

export function unpackList<T>(payload: PaginatedResponse<T> | T[]): T[] {
  return Array.isArray(payload) ? payload : payload.results ?? [];
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

  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      return await loadWorkspaceSession();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearApiSession();
        return null;
      }
      if (attempt < 2) {
        await new Promise((resolve) => window.setTimeout(resolve, 800 * (attempt + 1)));
      }
    }
  }

  // Cold start, internet uzilishi yoki 5xx xatosida tokenlar saqlanib qoladi.
  return null;
}

export function clearApiSession() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}
