"use client";

import {
  ArrowRight,
  Award,
  BarChart3,
  Bell,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  FileBarChart,
  GraduationCap,
  LayoutDashboard,
  School,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  UserCheck,
  UserCog,
  UserRound,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import type { LiveDiagnosticReport, WorkspaceSession } from "../../lib/api";
import { AdminTestsPanel } from "../admin-tests-panel";
import { AdminAdmissionsPanel } from "../admin/admin-admissions-panel";
import { AdminCategoriesPanel } from "../admin/admin-categories-panel";
import { AdminClassesPanel } from "../admin/admin-classes-panel";
import { AdminStudentsPanel } from "../admin/admin-students-panel";
import { AdminUsersPanel } from "../admin/admin-users-panel";
import { CertificateReviewPanel } from "./certificate-review-panel";
import { MetricCard, PageTitle, WorkspaceShell, type NavItem } from "./portal-ui";

const adminNav: NavItem[] = [
  { id: "overview", label: "Dashboard", icon: LayoutDashboard },
  { id: "admissions", label: "Qabul va profiling", icon: UserCheck },
  { id: "students", label: "O‘quvchilar", icon: GraduationCap },
  { id: "exams", label: "Diagnostika", icon: ClipboardList },
  { id: "classes", label: "Sinflar", icon: School },
  { id: "categories", label: "Kategoriyalar", icon: Target },
  { id: "certificates", label: "Sertifikatlar", icon: Award },
  { id: "users", label: "Foydalanuvchilar", icon: UserCog },
  { id: "settings", label: "Tizim sozlamalari", icon: Settings },
];

export function AdminWorkspace({
  session,
  onLogout,
  onOpenReport,
  onOpenExamResult,
}: {
  session: WorkspaceSession;
  onLogout: () => void;
  onOpenReport: (report: LiveDiagnosticReport) => void;
  onOpenExamResult: (result: LiveDiagnosticReport) => void;
}) {
  const [active, setActive] = useState("overview");
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
  const [systemSettings, setSystemSettings] = useState(() => {
    if (typeof window === "undefined") return { autoSave: true, compactMode: false };
    const saved = window.localStorage.getItem("bilimyol_ui_settings");
    if (!saved) return { autoSave: true, compactMode: false };
    try {
      return JSON.parse(saved) as { autoSave: boolean; compactMode: boolean };
    } catch {
      return { autoSave: true, compactMode: false };
    }
  });
  const [settingsNotice, setSettingsNotice] = useState("");

  useEffect(() => {
    document.documentElement.classList.toggle("bilimyol-compact", systemSettings.compactMode);
  }, [systemSettings.compactMode]);

  const toggleSystemSetting = (key: keyof typeof systemSettings) => {
    setSystemSettings((current) => {
      const next = { ...current, [key]: !current[key] };
      window.localStorage.setItem("bilimyol_ui_settings", JSON.stringify(next));
      return next;
    });
    setSettingsNotice("Interfeys sozlamasi saqlandi");
    window.setTimeout(() => setSettingsNotice(""), 1800);
  };

  const readyCount = session.dashboard.readiness.find((item) => item.readiness === "ready")?.count ?? 0;
  const riskCount = session.dashboard.readiness.find((item) => item.readiness === "not_ready")?.count ?? 0;
  const completedCount = session.dashboard.completed_attempts || 0;
  const readyPercent = completedCount ? Math.round((readyCount / completedCount) * 100) : 0;
  const latestReport = session.report;

  const journeySteps = [
    { icon: UserCheck, title: "Qabul va suhbat", description: "Profil, maqsad va suhbat xulosasi database’da saqlanadi." },
    { icon: Target, title: "Kategoriyalash", description: "Yo‘nalish va qo‘llab-quvvatlash darajasi belgilanadi." },
    { icon: ClipboardList, title: "Diagnostik test", description: "Admin sinfga mos testni biriktiradi va credential beradi." },
    { icon: UserRound, title: "Student kabineti", description: "O‘quvchi testni mustaqil ishlaydi; javoblar saqlanadi." },
    { icon: CheckCircle2, title: "Shaxsiy roadmap", description: "Natijadan draft yaratiladi va o‘qituvchi tasdiqlaydi." },
  ];

  const overview = (
    <>
      <PageTitle eyebrow="Administrator paneli" title="Individual ta’lim boshqaruvi" description="Qabul, diagnostika va shaxsiy rivojlanish real backend orqali boshqariladi." action={<button className="portal-primary" onClick={() => setActive("admissions")}><UserCheck size={18} /> Yangi qabul</button>} />
      <div className="portal-metrics-grid">
        <MetricCard icon={GraduationCap} label="Jami o‘quvchi" value={session.dashboard.students || 0} note="Database ma’lumoti" />
        <MetricCard icon={ClipboardList} label="Faol testlar" value={session.dashboard.active_assignments || 0} note="Biriktirilgan diagnostika" tone="gold" />
        <MetricCard icon={CheckCircle2} label="Yakunlangan" value={completedCount} note="Hisobot yaratilgan" tone="green" />
        <MetricCard icon={BarChart3} label="O‘rtacha natija" value={`${Math.round(Number(session.dashboard.average_score) || 0)}/100`} note="Barcha diagnostikalar" tone="red" />
      </div>
      <section className="admin-journey-card portal-card">
        <div className="admin-journey-head"><div><span>Asosiy ish oqimi</span><h2>Qabuldan shaxsiy roadmapgacha</h2><p>Har bir bosqich database’dagi oldingi ma’lumotga tayanadi.</p></div><Sparkles size={23} /></div>
        <div className="admin-journey-grid">{journeySteps.map(({ icon: Icon, title, description }, index) => <article key={title}><div className="journey-step-top"><span>{index + 1}</span><Icon size={20} /></div><strong>{title}</strong><p>{description}</p>{index < journeySteps.length - 1 && <i aria-hidden="true" />}</article>)}</div>
      </section>
      <div className="admin-dashboard-lower-grid">
        <article className="portal-card admin-readiness-card"><div className="admin-readiness-head"><div><span>Tayyorlik</span><h2>Diagnostika holati</h2></div><ShieldCheck size={22} /></div><div className="admin-readiness-value"><strong>{readyPercent}%</strong><span>tayyor o‘quvchilar</span></div><div className="admin-readiness-track"><i style={{ width: `${readyPercent}%` }} /></div><div className="admin-readiness-stats"><div><span className="ready" /><strong>{readyCount}</strong><small>Tayyor</small></div><div><span className="risk" /><strong>{riskCount}</strong><small>Tayyor emas</small></div><div><span className="neutral" /><strong>{completedCount}</strong><small>Jami hisobot</small></div></div></article>
        <article className="portal-card admin-actions-card"><div className="admin-readiness-head"><div><span>Tezkor amallar</span><h2>Keyingi qadam</h2></div></div><div className="admin-quick-actions"><button type="button" onClick={() => setActive("admissions")}><span><UserCheck size={20} /></span><div><strong>Qabul va suhbat</strong><small>Yangi profil yaratish</small></div><ArrowRight size={17} /></button><button type="button" onClick={() => setActive("exams")}><span><ClipboardList size={20} /></span><div><strong>Diagnostika</strong><small>Sinfga mos testni biriktirish</small></div><ArrowRight size={17} /></button><button type="button" onClick={() => setActive("certificates")}><span><Award size={20} /></span><div><strong>Sertifikatlar</strong><small>Tekshiruv navbati</small></div><ArrowRight size={17} /></button><button type="button" disabled={!latestReport} onClick={() => latestReport && onOpenReport(latestReport)}><span><FileBarChart size={20} /></span><div><strong>Oxirgi hisobot</strong><small>{latestReport ? latestReport.student.full_name : "Hisobot hali yo‘q"}</small></div><ArrowRight size={17} /></button></div></article>
      </div>
    </>
  );

  const settings = (
    <>
      <PageTitle eyebrow="Sozlamalar" title="Interfeys sozlamalari" description="Faqat qurilma ko‘rinishiga ta’sir qiladigan lokal sozlamalar." action={settingsNotice ? <span className="settings-saved"><CheckCircle2 size={15} /> {settingsNotice}</span> : undefined} />
      <div className="settings-grid simple-settings">
        <article className="portal-card setting-card"><span><ClipboardCheck size={21} /></span><div><strong>Javoblarni avtomatik saqlash</strong><p>Real diagnostikada har bir javob backendga yuboriladi.</p><small>{systemSettings.autoSave ? "Yoqilgan" : "O‘chirilgan"}</small></div><button className={`setting-toggle ${systemSettings.autoSave ? "on" : ""}`} onClick={() => toggleSystemSetting("autoSave")}><i /></button></article>
        <article className="portal-card setting-card"><span><UserCheck size={21} /></span><div><strong>Ixcham interfeys</strong><p>Ekranga ko‘proq ma’lumot joylashtiradi.</p><small>{systemSettings.compactMode ? "Yoqilgan" : "O‘chirilgan"}</small></div><button className={`setting-toggle ${systemSettings.compactMode ? "on" : ""}`} onClick={() => toggleSystemSetting("compactMode")}><i /></button></article>
        <article className="portal-card setting-card"><span><Bell size={21} /></span><div><strong>Real bildirishnomalar</strong><p>Natija, roadmap, sertifikat va xabarlar backenddan olinadi.</p><small>Doim faol</small></div><span className="setting-live"><CheckCircle2 size={16} /> API</span></article>
      </div>
    </>
  );

  const contentBySection: Record<string, ReactNode> = {
    overview,
    admissions: <AdminAdmissionsPanel selectedProfileId={selectedProfileId} onSelectProfile={setSelectedProfileId} onOpenTests={() => setActive("exams")} />,
    students: <AdminStudentsPanel selectedProfileId={selectedProfileId} onSelectProfile={setSelectedProfileId} />,
    exams: <AdminTestsPanel key={selectedProfileId ?? "none"} selectedProfileId={selectedProfileId} onComplete={onOpenExamResult} />,
    classes: <AdminClassesPanel />,
    categories: <AdminCategoriesPanel />,
    certificates: <CertificateReviewPanel />,
    users: <AdminUsersPanel />,
    settings,
  };

  return <WorkspaceShell session={session} nav={adminNav} active={active} onChange={setActive} onLogout={onLogout} roleLabel="Administrator">{contentBySection[active] ?? overview}</WorkspaceShell>;
}
