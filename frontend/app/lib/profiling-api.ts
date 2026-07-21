import { apiRequest, type PaginatedResponse } from "./api";

export type ProfileStatus =
  | "new"
  | "interview_draft"
  | "interview_completed"
  | "test_recommended"
  | "test_assigned"
  | "diagnosed"
  | "roadmap_draft"
  | "active"
  | "paused";

export type GuardianContact = {
  id: number;
  full_name: string;
  relationship: string;
  phone: string;
  email: string;
  workplace?: string;
  is_primary: boolean;
};

export type Category = {
  id: number;
  code: string;
  title: string;
  description: string;
  kind: string;
  subject_slug: string;
  color: string;
  is_active: boolean;
  order: number;
};

export type StudentCategory = {
  id: number;
  category: number;
  category_detail: Category;
  source: string;
  confidence: number;
  note: string;
  is_active: boolean;
};

export type StudentGoal = {
  id: number;
  goal_type: string;
  title: string;
  description: string;
  current_value: string;
  target_value: string;
  target_score: number | null;
  target_date: string | null;
  priority: number;
  is_primary: boolean;
  is_active: boolean;
};

export type InterviewAnswer = {
  id?: number;
  question_key: string;
  question_text: string;
  answer_text: string;
  score?: number | null;
  order: number;
};

export type StudentInterview = {
  id: number;
  status: "draft" | "completed";
  strengths: string;
  weaknesses: string;
  interests: string;
  main_problem: string;
  motivation_level: string;
  independence_level: string;
  parent_support_level: string;
  admin_summary: string;
  recommendation: string;
  next_step: string;
  answers: InterviewAnswer[];
};

export type StudentProfile = {
  id: number;
  admission_code: string;
  student: {
    id: number;
    username: string;
    full_name: string;
    email?: string;
    phone?: string;
  };
  birth_date: string | null;
  school_name: string;
  grade: number | null;
  region: string;
  district: string;
  weekly_study_hours: number;
  learning_style: string;
  internet_access: boolean;
  device_access: boolean;
  assigned_teacher: number | null;
  status: ProfileStatus;
  guardian_contacts: GuardianContact[];
  goals: StudentGoal[];
  category_links: StudentCategory[];
  interviews: StudentInterview[];
  created_at: string;
  updated_at: string;
};

export type OnboardingPayload = {
  username: string;
  password: string;
  full_name: string;
  phone?: string;
  email?: string;
  birth_date?: string | null;
  school_name?: string;
  grade: number;
  region?: string;
  district?: string;
  weekly_study_hours: number;
  guardian_name: string;
  guardian_phone: string;
  guardian_relationship: string;
};

export type ExamQuestion = {
  id: number;
  points: string | number;
  order: number;
  question_detail: {
    id: number;
    prompt: string;
    subject_title: string;
    options: { id: number; label: string; text: string }[];
  };
};

export type Exam = {
  id: number;
  title: string;
  grade: number | null;
  purpose: string;
  description: string;
  duration_minutes: number;
  status: string;
  exam_questions: ExamQuestion[];
};

export function getStudentProfiles(query = "") {
  return apiRequest<PaginatedResponse<StudentProfile>>(`/student-profiles/${query ? `?${query}` : ""}`);
}

export function getStudentProfile(id: number) {
  return apiRequest<StudentProfile>(`/student-profiles/${id}/`);
}

export function onboardStudent(data: OnboardingPayload) {
  return apiRequest<StudentProfile>("/student-profiles/onboard/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateStudentProfile(id: number, data: Record<string, unknown>) {
  return apiRequest<StudentProfile>(`/student-profiles/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function createStudentInterview(data: Record<string, unknown>) {
  return apiRequest<StudentInterview>("/student-interviews/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateStudentInterview(id: number, data: Record<string, unknown>) {
  return apiRequest<StudentInterview>(`/student-interviews/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function createStudentGoal(data: Record<string, unknown>) {
  return apiRequest<StudentGoal>("/student-goals/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function assignStudentCategory(data: Record<string, unknown>) {
  return apiRequest<StudentCategory>("/student-categories/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function completeStudentInterview(profileId: number) {
  return apiRequest<StudentProfile>(`/student-profiles/${profileId}/complete-interview/`, { method: "POST" });
}

export function recommendStudentTests(profileId: number) {
  return apiRequest<{ profile: number; student: string; tests: Exam[] }>(
    `/student-profiles/${profileId}/recommend-tests/`,
  );
}

export function getCategories(query = "is_active=true") {
  return apiRequest<PaginatedResponse<Category>>(`/categories/?${query}`);
}

export function createCategory(data: Record<string, unknown>) {
  return apiRequest<Category>("/categories/", { method: "POST", body: JSON.stringify(data) });
}
