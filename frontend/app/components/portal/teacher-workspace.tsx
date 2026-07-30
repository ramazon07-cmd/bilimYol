"use client";

import {
  ArrowRight,
  Award,
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  LayoutDashboard,
  LoaderCircle,
  School,
  Target,
  UsersRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  apiRequest,
  type LiveAssignment,
  type LiveClassroom,
  type LiveDiagnosticReport,
  type LiveRoadmap,
  type PaginatedResponse,
  type WorkspaceSession,
  unpackList,
} from "../../lib/api";
import { RBIS_COLORS } from "../../lib/rbis-theme";
import { CertificateReviewPanel } from "./certificate-review-panel";
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

const teacherNav: NavItem[] = [
  { id: "overview", label: "Bosh sahifa", icon: LayoutDashboard },
  { id: "classroom", label: "Sinf diagnostikasi", icon: UsersRound },
  { id: "roadmaps", label: "Roadmaplar", icon: Target },
  { id: "assignments", label: "Biriktirilgan testlar", icon: ClipboardList },
  { id: "certificates", label: "Sertifikatlar", icon: Award },
];

export function TeacherWorkspace({
  session,
  onLogout,
  onOpenReport,
}: {
  session: WorkspaceSession;
  onLogout: () => void;
  onOpenReport: (report: LiveDiagnosticReport) => void;
}) {
  const [active, setActive] = useState("overview");
  const [classrooms, setClassrooms] = useState<LiveClassroom[]>([]);
  const [reports, setReports] = useState<LiveDiagnosticReport[]>([]);
  const [roadmaps, setRoadmaps] = useState<LiveRoadmap[]>([]);
  const [assignments, setAssignments] = useState<LiveAssignment[]>([]);
  const [selectedClassroomId, setSelectedClassroomId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [approvingId, setApprovingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [classroomPayload, reportPayload, roadmapPayload, assignmentPayload] = await Promise.all([
        apiRequest<PaginatedResponse<LiveClassroom> | LiveClassroom[]>("/classrooms/?is_active=true&page_size=100"),
        apiRequest<PaginatedResponse<LiveDiagnosticReport> | LiveDiagnosticReport[]>("/reports/?page_size=500&ordering=-generated_at"),
        apiRequest<PaginatedResponse<LiveRoadmap> | LiveRoadmap[]>("/roadmaps/?page_size=500&ordering=-updated_at"),
        apiRequest<PaginatedResponse<LiveAssignment> | LiveAssignment[]>("/assignments/?page_size=500"),
      ]);
      const nextClassrooms = unpackList(classroomPayload);
      setClassrooms(nextClassrooms);
      setReports(unpackList(reportPayload));
      setRoadmaps(unpackList(roadmapPayload));
      setAssignments(unpackList(assignmentPayload));
      setSelectedClassroomId((current) => current ?? nextClassrooms[0]?.id ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "O‘qituvchi kabineti yuklanmadi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, []);

  const selectedClassroom = classrooms.find((item) => item.id === selectedClassroomId) ?? null;
  const studentIds = useMemo(
    () => new Set(selectedClassroom?.enrollments.map((item) => item.student) ?? []),
    [selectedClassroom],
  );
  const latestByStudent = useMemo(() => {
    const map = new Map<number, LiveDiagnosticReport>();
    reports.forEach((report) => {
      const studentId = report.student.id;
      if (studentId && studentIds.has(studentId) && !map.has(studentId)) map.set(studentId, report);
    });
    return map;
  }, [reports, studentIds]);
  const visibleEnrollments = (selectedClassroom?.enrollments ?? []).filter((item) =>
    item.student_detail.full_name.toLowerCase().includes(search.toLowerCase()),
  );
  const scoredReports = useMemo(() => [...latestByStudent.values()], [latestByStudent]);
  const classAverage = scoredReports.length ? Math.round(scoredReports.reduce((sum, report) => sum + Number(report.overall_score), 0) / scoredReports.length) : 0;
  const readyCount = scoredReports.filter((report) => report.readiness === "ready").length;
  const riskCount = scoredReports.filter((report) => report.readiness === "not_ready").length;
  const classRoadmaps = roadmaps.filter((roadmap) => studentIds.has(roadmap.student));
  const pendingRoadmaps = classRoadmaps.filter((roadmap) => roadmap.status === "draft");
  const classAssignments = assignments.filter((assignment) => assignment.classroom === selectedClassroomId);
  const teacherNavigation = teacherNav.map((item) => item.id === "roadmaps" && pendingRoadmaps.length ? { ...item, badge: String(pendingRoadmaps.length) } : item);

  const subjectAverages = useMemo(() => {
    const values = new Map<string, { title: string; color: string; total: number; count: number }>();
    scoredReports.forEach((report) => report.subject_results.forEach((item) => {
      const current = values.get(item.subject.slug) ?? { title: item.subject.title, color: item.subject.color, total: 0, count: 0 };
      current.total += Number(item.score);
      current.count += 1;
      values.set(item.subject.slug, current);
    }));
    return [...values.entries()].map(([slug, item]) => ({ slug, ...item, score: item.count ? Math.round(item.total / item.count) : 0 }));
  }, [scoredReports]);

  const approveRoadmap = async (roadmap: LiveRoadmap) => {
    setApprovingId(roadmap.id);
    setError("");
    try {
      const updated = await apiRequest<LiveRoadmap>(`/roadmaps/${roadmap.id}/approve/`, { method: "POST" });
      setRoadmaps((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Roadmap tasdiqlanmadi.");
    } finally {
      setApprovingId(null);
    }
  };

  const classSelector = classrooms.length ? (
    <label className="class-select"><School size={16} /><select value={selectedClassroomId ?? ""} onChange={(event) => setSelectedClassroomId(Number(event.target.value))}>{classrooms.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
  ) : undefined;

  const studentTable = selectedClassroom ? (
    <article className="portal-card students-table-card">
      <div className="portal-card-head"><div><span>O‘quvchilar</span><h2>{selectedClassroom.name} sinf natijalari</h2></div><div className="table-actions"><div className="mini-search"><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="O‘quvchi izlash" /></div></div></div>
      <div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>O‘quvchi</th><th>Oxirgi ball</th><th>English daraja</th><th>Testlar</th><th>Holat</th><th /></tr></thead><tbody>{visibleEnrollments.map((enrollment) => {
        const report = latestByStudent.get(enrollment.student);
        const english = report?.subject_results.find((item) => item.subject.slug === "english");
        const attemptCount = reports.filter((item) => item.student.id === enrollment.student).length;
        return <tr key={enrollment.id}><td><div className="table-person"><span>{enrollment.student_detail.full_name.split(" ").map((part) => part[0]).slice(0, 2).join("")}</span><div><strong>{enrollment.student_detail.full_name}</strong><small>{enrollment.student_detail.username}</small></div></div></td><td><strong>{report ? Math.round(Number(report.overall_score)) : "—"}</strong></td><td>{english?.level ?? "—"}</td><td>{attemptCount}</td><td><em className={`table-status ${report?.readiness === "ready" ? "ready" : report ? "risk" : "watch"}`}>{report?.readiness === "ready" ? "Tayyor" : report ? "Riskda" : "Test ishlamagan"}</em></td><td>{report && <button className="row-action" onClick={() => onOpenReport(report)}><ArrowRight size={15} /></button>}</td></tr>;
      })}</tbody></table></div>
      {!visibleEnrollments.length && <EmptyState title="O‘quvchi topilmadi" description="Bu sinfda mos o‘quvchi yo‘q." icon={UsersRound} />}
    </article>
  ) : <EmptyState title="Sinf biriktirilmagan" description="Administrator o‘qituvchini sinfga biriktirgach real o‘quvchilar ko‘rinadi." icon={School} />;

  const overview = (
    <>
      <PageTitle eyebrow="O‘qituvchi kabineti" title={`Xayrli kun, ${session.user.full_name.split(" ")[0]}!`} description="Faqat sizga biriktirilgan sinf va o‘quvchilar ma’lumotlari." action={classSelector} />
      {error && <div className="admin-flow-message error">{error}</div>}
      <div className="portal-metrics-grid">
        <MetricCard icon={UsersRound} label="O‘quvchilar" value={selectedClassroom?.student_count ?? 0} note={selectedClassroom?.name ?? "Sinf yo‘q"} />
        <MetricCard icon={BarChart3} label="Sinf o‘rtachasi" value={scoredReports.length ? `${classAverage}/100` : "—"} note={`${scoredReports.length} ta natija`} tone="gold" />
        <MetricCard icon={Target} label="Risk guruhida" value={riskCount} note="Oxirgi diagnostika" tone="red" />
        <MetricCard icon={ClipboardCheck} label="Roadmap tasdiqlash" value={pendingRoadmaps.length} note="Backenddagi navbat" tone="green" />
      </div>
      <div className="teacher-highlight-grid">
        <article className="portal-card class-pulse"><div className="portal-card-head"><div><span>Sinf pulsi</span><h2>Fanlar o‘rtachasi</h2></div><em>{readyCount} ta tayyor</em></div>{subjectAverages.length ? subjectAverages.map((subject) => <SubjectProgress key={subject.slug} title={subject.title} score={subject.score} color={subject.color || RBIS_COLORS.primary} />) : <EmptyState title="Natija yo‘q" description="O‘quvchilar testni yakunlagach fan o‘rtachasi chiqadi." icon={BarChart3} />}</article>
        <article className="portal-card"><div className="portal-card-head"><div><span>Faol testlar</span><h2>{selectedClassroom?.name ?? "Sinf"} diagnostikasi</h2></div><ClipboardList size={20} /></div>{classAssignments.length ? <div className="assignment-list">{classAssignments.slice(0, 5).map((assignment) => <div key={assignment.id}><span className="assignment-icon"><ClipboardList size={18} /></span><div><strong>{assignment.exam_detail.title}</strong><small>{assignment.student_detail.full_name}</small></div><p><strong>{assignment.is_active ? "Faol" : "Yakunlangan"}</strong><small>{assignment.due_at ? new Date(assignment.due_at).toLocaleDateString("uz-UZ") : "Muddat yo‘q"}</small></p></div>)}</div> : <EmptyState title="Biriktirilgan test yo‘q" description="Admin test biriktirgach shu yerda ko‘rinadi." icon={ClipboardList} />}</article>
      </div>
      {studentTable}
    </>
  );

  const classroomPanel = (
    <>
      <PageTitle eyebrow="Sinf diagnostikasi" title="O‘quvchilar kesimidagi natijalar" description="Sinf ro‘yxati va har bir o‘quvchining oxirgi real natijasi." action={classSelector} />
      <div className="portal-metrics-grid three">
        <MetricCard icon={UsersRound} label="Sinf hajmi" value={selectedClassroom?.student_count ?? 0} note="Faol o‘quvchilar" />
        <MetricCard icon={BarChart3} label="O‘rtacha ball" value={scoredReports.length ? `${classAverage}/100` : "—"} note="Oxirgi natijalar" tone="gold" />
        <MetricCard icon={CheckCircle2} label="Tayyor o‘quvchilar" value={readyCount} note="Chegaradan yuqori" tone="green" />
      </div>
      {studentTable}
    </>
  );

  const roadmapPanel = (
    <>
      <PageTitle eyebrow="Roadmaplar" title="Tasdiqlash navbati" description="Faqat o‘z sinfingizdagi real roadmaplar." action={classSelector} />
      {error && <div className="admin-flow-message error">{error}</div>}
      {classRoadmaps.length ? <div className="approval-grid">{classRoadmaps.map((roadmap) => {
        const firstStage = roadmap.stages[0];
        const report = reports.find((item) => item.id === roadmap.report);
        return <article className={`portal-card approval-card ${roadmap.status !== "draft" ? "approved-card" : ""}`} key={roadmap.id}><div className="approval-head"><span>{roadmap.student_detail.full_name.split(" ").map((part) => part[0]).slice(0, 2).join("")}</span><div><strong>{roadmap.student_detail.full_name}</strong><small>{roadmap.primary_goal_title ?? "Shaxsiy roadmap"}</small></div><em className={roadmap.status !== "draft" ? "approved-status" : ""}>{roadmap.status === "draft" ? "Tasdiq kutmoqda" : roadmap.status}</em></div><div className="approval-focus"><small>Asosiy fokus</small><strong>{firstStage?.focus_topic?.title ?? firstStage?.title ?? "Bosqich yaratilmagan"}</strong><span>{firstStage ? `${firstStage.start_score} → ${firstStage.target_score} ball` : `${roadmap.target_score}/100 maqsad`}</span></div><div className="approval-actions">{report && <button onClick={() => onOpenReport(report)}>Hisobot</button>}<button className={`approve ${roadmap.status !== "draft" ? "approved" : ""}`} disabled={roadmap.status !== "draft" || approvingId === roadmap.id} onClick={() => void approveRoadmap(roadmap)}>{approvingId === roadmap.id ? <LoaderCircle className="spin" size={15} /> : <CheckCircle2 size={15} />} {roadmap.status === "draft" ? "Tasdiqlash" : "Tasdiqlangan"}</button></div></article>;
      })}</div> : <EmptyState title="Roadmap yo‘q" description="O‘quvchilar diagnostikani yakunlagach roadmaplar shu yerda chiqadi." icon={Target} />}
    </>
  );

  const assignmentPanel = (
    <>
      <PageTitle eyebrow="Testlar" title="Sinfga biriktirilgan diagnostikalar" description="Admin biriktirgan real testlar va ularning holati." action={classSelector} />
      {classAssignments.length ? <article className="portal-card"><div className="assignment-list">{classAssignments.map((assignment) => <div key={assignment.id}><span className="assignment-icon"><ClipboardList size={18} /></span><div><strong>{assignment.exam_detail.title}</strong><small>{assignment.student_detail.full_name} · {assignment.delivery_mode}</small></div><p><strong>{assignment.has_attempt ? "Urinish bor" : "Boshlanmagan"}</strong><small>{assignment.is_active ? "Faol" : "Yopilgan"}</small></p><em>{assignment.due_at ? new Date(assignment.due_at).toLocaleDateString("uz-UZ") : "—"}</em></div>)}</div></article> : <EmptyState title="Test biriktirilmagan" description="Administrator English testini biriktirgach ro‘yxat yangilanadi." icon={ClipboardList} />}
    </>
  );

  let content = overview;
  if (active === "classroom") content = classroomPanel;
  if (active === "roadmaps") content = roadmapPanel;
  if (active === "assignments") content = assignmentPanel;
  if (active === "certificates") content = <CertificateReviewPanel />;
  if (loading) content = <LoadingState label="Sinf va o‘quvchilar yuklanmoqda..." />;
  if (error && !classrooms.length) content = <ErrorState message={error} onRetry={() => void load()} />;

  return <WorkspaceShell session={session} nav={teacherNavigation} active={active} onChange={setActive} onLogout={onLogout} roleLabel="O‘qituvchi">{content}</WorkspaceShell>;
}
