"use client";

import {
  ArrowRight,
  Check,
  ClipboardCheck,
  Clock3,
  FileBarChart,
  GraduationCap,
  LayoutDashboard,
  MessageCircle,
  Send,
  Target,
  TrendingUp,
  UserRound,
  UsersRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  apiRequest,
  type LiveAssignment,
  type LiveConversation,
  type LiveDiagnosticReport,
  type LiveParentStudent,
  type LiveRoadmap,
  type PaginatedResponse,
  type WorkspaceSession,
  unpackList,
} from "../../lib/api";
import { RBIS_COLORS } from "../../lib/rbis-theme";
import { UniversityJourney } from "../dream-university";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  MetricCard,
  PageTitle,
  ScoreRing,
  SubjectProgress,
  WorkspaceShell,
  type NavItem,
} from "./portal-ui";

const parentNav: NavItem[] = [
  { id: "overview", label: "Umumiy ko‘rinish", icon: LayoutDashboard },
  { id: "results", label: "Farzand natijalari", icon: FileBarChart },
  { id: "university", label: "Dream University", icon: GraduationCap },
  { id: "tasks", label: "Vazifalar", icon: ClipboardCheck },
  { id: "messages", label: "Xabarlar", icon: MessageCircle },
];

export function ParentWorkspace({
  session,
  onLogout,
  onOpenReport,
}: {
  session: WorkspaceSession;
  onLogout: () => void;
  onOpenReport: (report: LiveDiagnosticReport) => void;
}) {
  const [active, setActive] = useState("overview");
  const [links, setLinks] = useState<LiveParentStudent[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [reports, setReports] = useState<LiveDiagnosticReport[]>([]);
  const [roadmaps, setRoadmaps] = useState<LiveRoadmap[]>([]);
  const [assignments, setAssignments] = useState<LiveAssignment[]>([]);
  const [conversations, setConversations] = useState<LiveConversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [draftMessage, setDraftMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [linkPayload, reportPayload, roadmapPayload, assignmentPayload, conversationPayload] = await Promise.all([
        apiRequest<PaginatedResponse<LiveParentStudent> | LiveParentStudent[]>("/parent-students/?page_size=100"),
        apiRequest<PaginatedResponse<LiveDiagnosticReport> | LiveDiagnosticReport[]>("/reports/?page_size=100&ordering=-generated_at"),
        apiRequest<PaginatedResponse<LiveRoadmap> | LiveRoadmap[]>("/roadmaps/?page_size=100&ordering=-updated_at"),
        apiRequest<PaginatedResponse<LiveAssignment> | LiveAssignment[]>("/assignments/?page_size=100"),
        apiRequest<PaginatedResponse<LiveConversation> | LiveConversation[]>("/conversations/?page_size=100"),
      ]);
      const nextLinks = unpackList(linkPayload).filter((item) => item.parent === session.user.id);
      const nextConversations = unpackList(conversationPayload);
      const initialStudentId = selectedStudentId ?? nextLinks[0]?.student ?? null;
      setLinks(nextLinks);
      setSelectedStudentId(initialStudentId);
      setReports(unpackList(reportPayload));
      setRoadmaps(unpackList(roadmapPayload));
      setAssignments(unpackList(assignmentPayload));
      setConversations(nextConversations);
      setSelectedConversationId((current) => current ?? nextConversations.find((item) => item.student === initialStudentId)?.id ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Ota-ona kabineti yuklanmadi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
    // Initial load only; later refreshes are explicit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedLink = links.find((item) => item.student === selectedStudentId) ?? null;
  const childReports = reports.filter((item) => item.student.id === selectedStudentId);
  const latestReport = childReports[0] ?? null;
  const childRoadmap = roadmaps.find((item) => item.student === selectedStudentId) ?? null;
  const childAssignments = assignments.filter((item) => item.student === selectedStudentId && item.is_active);
  const childConversations = conversations.filter((item) => item.student === selectedStudentId);
  const selectedConversation = childConversations.find((item) => item.id === selectedConversationId) ?? childConversations[0] ?? null;
  const allTasks = childRoadmap?.stages.flatMap((stage) => stage.weekly_tasks) ?? [];
  const completedTasks = allTasks.filter((task) => task.is_completed).length;
  const taskPercent = allTasks.length ? Math.round((completedTasks / allTasks.length) * 100) : 0;
  const score = latestReport ? Math.round(Number(latestReport.overall_score)) : 0;
  const nextAssignment = useMemo(
    () => [...childAssignments].filter((item) => item.due_at).sort((a, b) => String(a.due_at).localeCompare(String(b.due_at)))[0] ?? null,
    [childAssignments],
  );

  const selectStudent = (studentId: number) => {
    setSelectedStudentId(studentId);
    const conversation = conversations.find((item) => item.student === studentId);
    setSelectedConversationId(conversation?.id ?? null);
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

  const sendMessage = async () => {
    const body = draftMessage.trim();
    if (!body || !selectedConversation) return;
    setSending(true);
    setError("");
    try {
      const created = await apiRequest<LiveConversation["messages"][number]>("/messages/", {
        method: "POST",
        body: JSON.stringify({ conversation: selectedConversation.id, body }),
      });
      setConversations((current) => current.map((conversation) => conversation.id === selectedConversation.id ? { ...conversation, messages: [...conversation.messages, created], last_message: created } : conversation));
      setDraftMessage("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Xabar yuborilmadi.");
    } finally {
      setSending(false);
    }
  };

  const childSelector = links.length > 1 ? (
    <label className="class-select"><UsersRound size={16} /><select value={selectedStudentId ?? ""} onChange={(event) => selectStudent(Number(event.target.value))}>{links.map((link) => <option value={link.student} key={link.id}>{link.student_detail.full_name}</option>)}</select></label>
  ) : undefined;

  if (loading) return <WorkspaceShell session={session} nav={parentNav} active={active} onChange={setActive} onLogout={onLogout} roleLabel="Ota-ona"><LoadingState label="Farzand ma’lumotlari yuklanmoqda..." /></WorkspaceShell>;
  if (error && !links.length) return <WorkspaceShell session={session} nav={parentNav} active={active} onChange={setActive} onLogout={onLogout} roleLabel="Ota-ona"><ErrorState message={error} onRetry={() => void load()} /></WorkspaceShell>;
  if (!selectedLink) return <WorkspaceShell session={session} nav={parentNav} active={active} onChange={setActive} onLogout={onLogout} roleLabel="Ota-ona"><EmptyState title="Farzand biriktirilmagan" description="Administrator ota-ona hisobini o‘quvchiga bog‘lagach ma’lumotlar ko‘rinadi." icon={UsersRound} /></WorkspaceShell>;

  const overview = (
    <>
      <PageTitle eyebrow="Ota-ona kabineti" title={`${selectedLink.student_detail.full_name} · umumiy holat`} description="Faqat sizga biriktirilgan farzand ma’lumotlari ko‘rsatiladi." action={childSelector} />
      {error && <div className="admin-flow-message error">{error}</div>}
      <div className="portal-metrics-grid">
        <MetricCard icon={TrendingUp} label="Umumiy natija" value={latestReport ? `${score}/100` : "—"} note="Oxirgi diagnostika" tone="red" />
        <MetricCard icon={ClipboardCheck} label="Roadmap bajarilishi" value={allTasks.length ? `${taskPercent}%` : "—"} note={`${completedTasks}/${allTasks.length} vazifa`} tone="gold" />
        <MetricCard icon={Clock3} label="Haftalik reja" value={childRoadmap ? `${childRoadmap.weekly_hours} soat` : "—"} note="Roadmap yuklamasi" tone="green" />
        <MetricCard icon={ClipboardCheck} label="Faol testlar" value={childAssignments.length} note={nextAssignment?.due_at ? `Muddat: ${new Date(nextAssignment.due_at).toLocaleDateString("uz-UZ")}` : "Biriktirilgan test"} />
      </div>
      {latestReport ? (
        <div className="portal-two-column">
          <article className="portal-card child-overview">
            <div className="portal-card-head"><div><span>Farzand profili</span><h2>{selectedLink.student_detail.full_name}</h2></div><em>{latestReport.grade ?? latestReport.classroom?.grade ?? "—"}-sinf · {latestReport.classroom?.name ?? "Sinf belgilanmagan"}</em></div>
            <div className="child-score-layout"><ScoreRing score={score} label="Umumiy ball" /><div className="subject-progress-list">{latestReport.subject_results.map((item) => <SubjectProgress key={item.subject.slug} title={`${item.subject.title} · ${item.level}`} score={Number(item.score)} color={item.subject.color || RBIS_COLORS.primary} />)}</div></div>
            {childRoadmap && <div className="child-insight"><Target size={19} /><span><strong>Asosiy maqsad:</strong> {childRoadmap.primary_goal_title ?? `${childRoadmap.target_score}/100 natija`}</span></div>}
          </article>
          <article className="portal-card">
            <div className="portal-card-head"><div><span>Haftalik reja</span><h2>Joriy vazifalar</h2></div><button className="portal-text-button" onClick={() => setActive("tasks")}>Barchasi</button></div>
            {allTasks.length ? <div className="compact-task-list">{allTasks.slice(0, 5).map((task) => <div className={task.is_completed ? "done" : ""} key={task.id}>{task.is_completed ? <Check size={15} /> : <Clock3 size={15} />}<span><strong>{task.title}</strong><small>{task.audience} · {task.description}</small></span><em>{task.is_completed ? "Bajarildi" : "Kutilmoqda"}</em></div>)}</div> : <EmptyState title="Vazifalar yo‘q" description="Roadmap yaratilgach vazifalar shu yerda chiqadi." icon={ClipboardCheck} />}
          </article>
        </div>
      ) : <EmptyState title="Farzand natijasi hali yo‘q" description="English testi yakunlangach diagnostika natijasi ko‘rinadi." icon={FileBarChart} />}
    </>
  );

  const results = (
    <>
      <PageTitle eyebrow="Natijalar" title={`${selectedLink.student_detail.full_name} · diagnostika tarixi`} description="Faqat tanlangan farzandning backenddagi hisobotlari." action={childSelector} />
      {childReports.length ? <div className="student-result-list">{childReports.map((report) => <article className="portal-card" key={report.id}><span><FileBarChart size={22} /></span><div><strong>{report.exam?.title ?? "English diagnostikasi"}</strong><small>{report.generated_at ? new Date(report.generated_at).toLocaleDateString("uz-UZ") : "—"}</small></div><p><strong>{Math.round(Number(report.overall_score))}/100</strong><small>{report.subject_results[0]?.level ?? "—"}</small></p><button className="portal-secondary" onClick={() => onOpenReport(report)}>Hisobot <ArrowRight size={15} /></button></article>)}</div> : <EmptyState title="Hisobot yo‘q" description="Farzandingiz testni yakunlagach natija shu yerda chiqadi." icon={FileBarChart} />}
    </>
  );

  const tasks = (
    <>
      <PageTitle eyebrow="Vazifalar" title="Oilaviy o‘quv rejasi" description="Roadmapdagi real vazifalar rol bo‘yicha ajratiladi." action={childSelector} />
      {allTasks.length ? <div className="task-board">{(["student", "parent", "teacher"] as const).map((audience) => {
        const audienceTasks = allTasks.filter((task) => task.audience === audience);
        const Icon = audience === "student" ? UserRound : audience === "parent" ? UsersRound : Target;
        return <section key={audience}><div className="task-column-head"><span className={`role-icon ${audience}`}><Icon size={18} /></span><div><strong>{audience === "student" ? "O‘quvchi" : audience === "parent" ? "Ota-ona" : "O‘qituvchi"}</strong><small>{audienceTasks.length} ta vazifa</small></div></div>{audienceTasks.map((task) => <article key={task.id} className={task.is_completed ? "complete" : ""} onClick={audience === "parent" ? () => void toggleTask(task.id, task.is_completed) : undefined}><span>{task.is_completed ? <Check size={15} /> : <Clock3 size={15} />}</span><div><strong>{task.title}</strong><small>{task.description}</small></div></article>)}{!audienceTasks.length && <p className="task-empty">Vazifa yo‘q</p>}</section>;
      })}</div> : <EmptyState title="Roadmap vazifalari yo‘q" description="Roadmap yaratilgach oilaviy reja shu yerda chiqadi." icon={ClipboardCheck} />}
    </>
  );

  const messages = (
    <>
      <PageTitle eyebrow="Aloqa" title="Xabarlar" description="O‘qituvchi va akademik bo‘lim bilan yozishmalar database’da saqlanadi." action={childSelector} />
      {error && <div className="admin-flow-message error">{error}</div>}
      {childConversations.length ? (
        <div className="message-layout">
          <div className="message-list">{childConversations.map((conversation) => <article key={conversation.id} role="button" tabIndex={0} className={selectedConversation?.id === conversation.id ? "active" : ""} onClick={() => setSelectedConversationId(conversation.id)}><span>{conversation.kind === "teacher" ? "OT" : "AB"}</span><div><strong>{conversation.title}</strong><p>{conversation.last_message?.body ?? "Xabar yo‘q"}</p></div><small>{conversation.last_message ? new Date(conversation.last_message.created_at).toLocaleDateString("uz-UZ") : ""}</small></article>)}</div>
          {selectedConversation && <article className="message-preview"><div className="message-person"><span>{selectedConversation.kind === "teacher" ? "OT" : "AB"}</span><div><strong>{selectedConversation.title}</strong><small>{selectedConversation.kind === "teacher" ? selectedConversation.teacher_detail?.full_name ?? "O‘qituvchi" : "RBIS akademik bo‘limi"}</small></div></div><div className="message-thread">{selectedConversation.messages.map((message) => <div key={message.id} className={`message-bubble ${message.sender === session.user.id ? "own" : ""}`}><small>{message.sender_detail.full_name}</small>{message.body}</div>)}</div><div className="message-compose"><input value={draftMessage} onChange={(event) => setDraftMessage(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void sendMessage(); }} placeholder="Xabar yozing..." /><button aria-label="Xabar yuborish" onClick={() => void sendMessage()} disabled={sending || !draftMessage.trim()}><Send size={17} /></button></div></article>}
        </div>
      ) : <EmptyState title="Suhbat kanali yo‘q" description="Administrator ota-ona uchun o‘qituvchi yoki akademik kanal yaratgach shu yerda paydo bo‘ladi." icon={MessageCircle} />}
    </>
  );

  let content = overview;
  if (active === "results") content = results;
  if (active === "tasks") content = tasks;
  if (active === "messages") content = messages;
  if (active === "university") content = <UniversityJourney session={session} studentId={selectedStudentId ?? undefined} />;

  return <WorkspaceShell session={session} nav={parentNav} active={active} onChange={setActive} onLogout={onLogout} roleLabel="Ota-ona">{content}</WorkspaceShell>;
}
