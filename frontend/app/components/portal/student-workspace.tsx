"use client";

import {
  ArrowRight,
  BarChart3,
  Check,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  Clock3,
  FileBarChart,
  GraduationCap,
  LayoutDashboard,
  LoaderCircle,
  Play,
  Target,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  apiRequest,
  type LiveAssignment,
  type LiveDiagnosticReport,
  type LiveRoadmap,
  type PaginatedResponse,
  type WorkspaceSession,
  unpackList,
} from "../../lib/api";
import type { Exam } from "../../lib/profiling-api";
import { RBIS_COLORS } from "../../lib/rbis-theme";
import { UniversityJourney } from "../dream-university";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PageTitle,
  SubjectProgress,
  WorkspaceShell,
  type NavItem,
} from "./portal-ui";

type StudentAttempt = {
  id: number;
  assignment: number;
  status: "in_progress" | "submitted" | "expired";
  remaining_seconds: number;
  question_order: number[];
  answers: { exam_question: number; selected_option: number }[];
};

const studentNav: NavItem[] = [
  { id: "overview", label: "Bosh sahifa", icon: LayoutDashboard },
  { id: "test", label: "English testi", icon: ClipboardList },
  { id: "results", label: "Natijalar", icon: FileBarChart },
  { id: "roadmap", label: "Roadmap", icon: Target },
  { id: "university", label: "Dream University", icon: GraduationCap },
];

export function StudentWorkspace({
  session,
  onLogout,
  onOpenReport,
}: {
  session: WorkspaceSession;
  onLogout: () => void;
  onOpenReport: (report: LiveDiagnosticReport) => void;
}) {
  const [active, setActive] = useState("overview");
  const [assignments, setAssignments] = useState<LiveAssignment[]>([]);
  const [reports, setReports] = useState<LiveDiagnosticReport[]>([]);
  const [roadmaps, setRoadmaps] = useState<LiveRoadmap[]>([]);
  const [activeAssignment, setActiveAssignment] = useState<LiveAssignment | null>(null);
  const [attempt, setAttempt] = useState<StudentAttempt | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [savingQuestion, setSavingQuestion] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [assignmentPayload, attemptPayload, reportPayload, roadmapPayload] = await Promise.all([
        apiRequest<PaginatedResponse<LiveAssignment> | LiveAssignment[]>("/assignments/?is_active=true&page_size=100"),
        apiRequest<PaginatedResponse<StudentAttempt> | StudentAttempt[]>("/attempts/?page_size=100&ordering=-started_at"),
        apiRequest<PaginatedResponse<LiveDiagnosticReport> | LiveDiagnosticReport[]>("/reports/?page_size=100&ordering=-generated_at"),
        apiRequest<PaginatedResponse<LiveRoadmap> | LiveRoadmap[]>("/roadmaps/?page_size=100&ordering=-updated_at"),
      ]);
      const nextAssignments = unpackList(assignmentPayload);
      const nextAttempts = unpackList(attemptPayload);
      const nextReports = unpackList(reportPayload).filter((report) =>
        report.subject_results.some((result) => result.subject.slug === "english"),
      );
      const inProgress = nextAttempts.find((item) => item.status === "in_progress");
      const matchingAssignment = inProgress ? nextAssignments.find((item) => item.id === inProgress.assignment) ?? null : null;
      setAssignments(nextAssignments);
      setReports(nextReports);
      setRoadmaps(unpackList(roadmapPayload));
      if (inProgress && matchingAssignment) {
        setAttempt(inProgress);
        setActiveAssignment(matchingAssignment);
        setAnswers(Object.fromEntries(inProgress.answers.map((answer) => [answer.exam_question, answer.selected_option])));
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "O‘quvchi kabineti yuklanmadi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, []);

  const latestReport = reports[0] ?? session.report;
  const latestRoadmap = roadmaps[0] ?? null;
  const tasks = latestRoadmap?.stages.flatMap((stage) => stage.weekly_tasks) ?? [];

  const orderedQuestions = useMemo(() => {
    if (!activeAssignment) return [];
    const questions = activeAssignment.exam_detail.exam_questions as Exam["exam_questions"];
    if (!attempt?.question_order.length) return questions;
    const byId = new Map(questions.map((item) => [item.id, item]));
    const ordered = attempt.question_order.map((id) => byId.get(id)).filter((item): item is Exam["exam_questions"][number] => Boolean(item));
    const orderedIds = new Set(ordered.map((item) => item.id));
    return [...ordered, ...questions.filter((item) => !orderedIds.has(item.id))];
  }, [activeAssignment, attempt]);

  const startTest = async (assignment: LiveAssignment) => {
    setLoading(true);
    setError("");
    try {
      const nextAttempt = await apiRequest<StudentAttempt>(`/assignments/${assignment.id}/start/`, { method: "POST" });
      setActiveAssignment(assignment);
      setAttempt(nextAttempt);
      setAnswers(Object.fromEntries(nextAttempt.answers.map((answer) => [answer.exam_question, answer.selected_option])));
      window.dispatchEvent(new Event("bilimyol-exam-start"));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Testni boshlashda xatolik.");
    } finally {
      setLoading(false);
    }
  };

  const saveAnswer = async (examQuestionId: number, optionId: number) => {
    if (!attempt) return;
    const previous = answers[examQuestionId];
    setAnswers((current) => ({ ...current, [examQuestionId]: optionId }));
    setSavingQuestion(examQuestionId);
    setError("");
    try {
      await apiRequest(`/attempts/${attempt.id}/answer/`, {
        method: "POST",
        body: JSON.stringify({ exam_question: examQuestionId, selected_option: optionId, is_flagged: false }),
      });
    } catch (requestError) {
      setAnswers((current) => {
        const next = { ...current };
        if (previous) next[examQuestionId] = previous;
        else delete next[examQuestionId];
        return next;
      });
      setError(requestError instanceof Error ? requestError.message : "Javob saqlanmadi.");
    } finally {
      setSavingQuestion(null);
    }
  };

  const submitTest = async () => {
    if (!attempt) return;
    const unanswered = orderedQuestions.length - Object.keys(answers).length;
    if (unanswered > 0) {
      setError(`Yana ${unanswered} ta savolga javob berilmagan.`);
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const report = await apiRequest<LiveDiagnosticReport>(`/attempts/${attempt.id}/submit/`, { method: "POST" });
      setReports((current) => [report, ...current]);
      setAssignments((current) => current.filter((item) => item.id !== activeAssignment?.id));
      setAttempt(null);
      setActiveAssignment(null);
      setAnswers({});
      onOpenReport(report);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Test yakunlanmadi.");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleTask = async (taskId: number, isCompleted: boolean) => {
    setError("");
    try {
      await apiRequest(`/weekly-tasks/${taskId}/`, {
        method: "PATCH",
        body: JSON.stringify({ is_completed: !isCompleted }),
      });
      setRoadmaps((current) => current.map((roadmap) => ({
        ...roadmap,
        stages: roadmap.stages.map((stage) => ({
          ...stage,
          weekly_tasks: stage.weekly_tasks.map((task) => task.id === taskId ? { ...task, is_completed: !isCompleted } : task),
        })),
      })));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Vazifa holati saqlanmadi.");
    }
  };

  const overview = (
    <>
      <PageTitle eyebrow="O‘quvchi kabineti" title={`Xush kelibsiz, ${session.user.full_name.split(" ")[0]}!`} description="Test, natija va roadmap ma’lumotlaringiz real backenddan olinadi." />
      <div className="portal-metrics-grid">
        <MetricCard icon={ClipboardList} label="Faol test" value={assignments.length} note="Sizga biriktirilgan" />
        <MetricCard icon={FileBarChart} label="Yakunlangan" value={reports.length} note="English diagnostika" tone="green" />
        <MetricCard icon={BarChart3} label="Oxirgi natija" value={latestReport ? `${Math.round(Number(latestReport.overall_score))}/100` : "—"} note={latestReport?.subject_results[0]?.level ?? "Natija hali yo‘q"} tone="gold" />
        <MetricCard icon={ClipboardCheck} label="Vazifalar" value={`${tasks.filter((task) => task.is_completed).length}/${tasks.length}`} note="Roadmap bajarilishi" tone="red" />
      </div>
      {latestReport ? (
        <article className="portal-card result-detail-card">
          <div className="portal-card-head"><div><span>Oxirgi diagnostika</span><h2>{latestReport.exam?.title ?? "English diagnostikasi"}</h2></div><button className="portal-text-button" onClick={() => onOpenReport(latestReport)}>Hisobotni ochish</button></div>
          <div className="large-subject-list">{latestReport.subject_results.map((item) => <SubjectProgress key={item.subject.slug} title={`${item.subject.title} · ${item.level}`} score={Number(item.score)} color={item.subject.color || RBIS_COLORS.primary} />)}</div>
        </article>
      ) : <EmptyState title="Diagnostika natijasi yo‘q" description="Admin English testini biriktirgach, testni ishlab natijani shu yerda ko‘rasiz." icon={FileBarChart} />}
    </>
  );

  const testContent = (
    <>
      <PageTitle eyebrow="English testi" title={attempt ? activeAssignment?.exam_detail.title ?? "English diagnostikasi" : "Biriktirilgan testlar"} description={attempt ? "Har bir javob database’da darhol saqlanadi." : "Faqat admin biriktirgan faol English testlari ko‘rsatiladi."} />
      {error && <div className="admin-flow-message error">{error}</div>}
      {loading && !attempt ? <LoadingState label="Testlar yuklanmoqda..." /> : attempt && activeAssignment ? (
        <section className="student-live-exam">
          <article className="portal-card student-exam-progress"><div><span>English · {activeAssignment.exam_detail.grade}-sinf</span><strong>{Object.keys(answers).length}/{orderedQuestions.length} savol</strong></div><div><Clock3 size={18} /><strong>{Math.max(0, Math.ceil(attempt.remaining_seconds / 60))} daqiqa</strong></div></article>
          <div className="admin-question-stack">
            {orderedQuestions.map((examQuestion, index) => {
              const question = examQuestion.question_detail;
              return (
                <article className="portal-card mini-question-card" key={examQuestion.id}>
                  <div className="mini-question-head"><span>{index + 1}</span><div><small>English</small>{question.context && <blockquote className="mini-question-context">{question.context}</blockquote>}<h3>{question.prompt}</h3></div>{savingQuestion === examQuestion.id && <LoaderCircle className="spin" size={18} />}</div>
                  <div className="mini-question-options">{question.options.map((option) => <button type="button" key={option.id} className={answers[examQuestion.id] === option.id ? "selected" : ""} onClick={() => void saveAnswer(examQuestion.id, option.id)} disabled={savingQuestion === examQuestion.id}><i>{option.label}</i><span>{option.text}</span></button>)}</div>
                </article>
              );
            })}
          </div>
          <article className="portal-card admin-submit-bar"><div><strong>{Object.keys(answers).length}/{orderedQuestions.length} savol</strong><p>Natija yakunlangach kabinetda saqlanadi.</p></div><button className="portal-primary" onClick={() => void submitTest()} disabled={submitting || Object.keys(answers).length !== orderedQuestions.length}>{submitting ? <LoaderCircle className="spin" size={17} /> : <CheckCircle2 size={17} />} Testni yakunlash</button></article>
        </section>
      ) : assignments.length ? (
        <div className="student-assignment-grid">{assignments.map((assignment) => <article className="portal-card student-assignment-card" key={assignment.id}><span><ClipboardList size={24} /></span><div><small>Biriktirilgan test</small><h2>{assignment.exam_detail.title}</h2><p>{assignment.exam_detail.grade}-sinf · {assignment.exam_detail.exam_questions.length} savol · {assignment.exam_detail.duration_minutes} daqiqa</p></div><button className="portal-primary" onClick={() => void startTest(assignment)} disabled={loading}>{loading ? <LoaderCircle className="spin" size={17} /> : <Play size={17} />}{assignment.has_attempt ? "Davom ettirish" : "Boshlash"}</button></article>)}</div>
      ) : <EmptyState title="Faol English testi yo‘q" description="Admin testni biriktirgandan keyin shu sahifada paydo bo‘ladi." icon={ClipboardList} />}
    </>
  );

  const results = (
    <>
      <PageTitle eyebrow="Natijalar" title="English diagnostika tarixi" description="Barcha topshirilgan testlar database’dan olinadi." />
      {loading ? <LoadingState /> : reports.length ? <div className="student-result-list">{reports.map((report) => {
        const english = report.subject_results.find((item) => item.subject.slug === "english");
        return <article className="portal-card" key={report.id}><span><FileBarChart size={22} /></span><div><strong>{report.exam?.title ?? "English diagnostikasi"}</strong><small>{report.generated_at ? new Date(report.generated_at).toLocaleDateString("uz-UZ") : "—"} · {report.grade ?? report.exam?.grade ?? "—"}-sinf</small></div><p><strong>{Math.round(Number(report.overall_score))}/100</strong><small>{english?.level ?? "—"}</small></p><button className="portal-secondary" onClick={() => onOpenReport(report)}>Ochish <ArrowRight size={15} /></button></article>;
      })}</div> : <EmptyState title="Natija hali yo‘q" description="English testini yakunlaganingizdan keyin shu yerda chiqadi." icon={FileBarChart} />}
    </>
  );

  const roadmap = (
    <>
      <PageTitle eyebrow="Roadmap" title={latestRoadmap?.primary_goal_title ?? "Shaxsiy o‘sish yo‘li"} description="Roadmap holati va haftalik vazifalar backendda saqlanadi." />
      {loading ? <LoadingState label="Roadmap yuklanmoqda..." /> : latestRoadmap ? (
        <>
          <article className="portal-card roadmap-live-summary"><div><span>Holat</span><strong>{latestRoadmap.status}</strong></div><div><span>Maqsad</span><strong>{latestRoadmap.target_score}/100</strong></div><div><span>Haftalik vaqt</span><strong>{latestRoadmap.weekly_hours} soat</strong></div></article>
          <div className="approval-grid">{latestRoadmap.stages.map((stage) => <article className="portal-card approval-card" key={stage.id}><div className="approval-head"><span>{stage.order}</span><div><strong>{stage.title}</strong><small>{stage.start_month}–{stage.end_month} oy · {stage.weekly_hours} soat/hafta</small></div><em>{stage.start_score} → {stage.target_score}</em></div><div className="roadmap-task-list">{stage.weekly_tasks.filter((task) => task.audience === "student").map((task) => <button type="button" key={task.id} className={task.is_completed ? "complete" : ""} onClick={() => void toggleTask(task.id, task.is_completed)}><span>{task.is_completed ? <Check size={15} /> : <Clock3 size={15} />}</span><div><strong>{task.title}</strong><small>{task.description}</small></div></button>)}</div></article>)}</div>
        </>
      ) : <EmptyState title="Roadmap hali yaratilmagan" description="Test yakunlangach roadmap avtomatik yaratiladi va o‘qituvchi tasdiqlaydi." icon={Target} />}
    </>
  );

  let content = overview;
  if (active === "test") content = testContent;
  if (active === "results") content = results;
  if (active === "roadmap") content = roadmap;
  if (active === "university") content = <UniversityJourney session={session} studentId={session.user.id} />;
  if (error && active === "overview") content = <ErrorState message={error} onRetry={() => void load()} />;

  return <WorkspaceShell session={session} nav={studentNav} active={active} onChange={setActive} onLogout={onLogout} roleLabel="O‘quvchi">{content}</WorkspaceShell>;
}
