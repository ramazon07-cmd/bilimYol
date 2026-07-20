"use client";

import {
  ArrowRight,
  BarChart3,
  Bell,
  BookOpenCheck,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  ClipboardList,
  Clock3,
  FileBarChart,
  FilePlus2,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  MessageCircle,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  School,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  UserCheck,
  UserCog,
  UserRound,
  UsersRound,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import type { WorkspaceSession } from "../lib/api";
import type { MiniExamResult } from "../lib/mini-exam";
import { AdminTestsPanel } from "./admin-tests-panel";
import { UniversityJourney } from "./dream-university";

type NavItem = { id: string; label: string; icon: LucideIcon; badge?: string };

const parentNav: NavItem[] = [
  { id: "overview", label: "Umumiy ko‘rinish", icon: LayoutDashboard },
  { id: "results", label: "Farzand natijalari", icon: FileBarChart },
  { id: "university", label: "Dream University", icon: GraduationCap },
  { id: "tasks", label: "Vazifalar", icon: ClipboardCheck, badge: "5" },
  { id: "messages", label: "Xabarlar", icon: MessageCircle, badge: "2" },
];

const teacherNav: NavItem[] = [
  { id: "overview", label: "Bosh sahifa", icon: LayoutDashboard },
  { id: "classroom", label: "Sinf diagnostikasi", icon: UsersRound },
  { id: "roadmaps", label: "Roadmaplar", icon: Target, badge: "4" },
  { id: "assignments", label: "Topshiriqlar", icon: ClipboardList },
];

const adminNav: NavItem[] = [
  { id: "overview", label: "Dashboard", icon: LayoutDashboard },
  { id: "exams", label: "Imtihonlar", icon: ClipboardList, badge: "6" },
  { id: "classes", label: "Sinflar", icon: School },
  { id: "users", label: "Foydalanuvchilar", icon: UserCog },
  { id: "settings", label: "Tizim sozlamalari", icon: Settings },
];

const students = [
  { name: "Bobur Xasanboyev", code: "BY-0821", score: 41, math: 15, english: 56, critical: 54, status: "Riskda", task: "62%" },
  { name: "Mohira Ibragimova", code: "MI-0814", score: 78, math: 81, english: 74, critical: 79, status: "Tayyor", task: "91%" },
  { name: "Asadbek Karimov", code: "AK-0807", score: 66, math: 63, english: 72, critical: 62, status: "Kuzatuvda", task: "84%" },
  { name: "Nilufar G‘aniyeva", code: "NG-0819", score: 84, math: 88, english: 82, critical: 81, status: "Tayyor", task: "96%" },
  { name: "Temur Shodiyev", code: "TS-0805", score: 53, math: 49, english: 61, critical: 50, status: "Riskda", task: "58%" },
];

type ParentConversationId = "teacher" | "academic";
type ParentChatMessage = { id: string; own: boolean; text: string };

const parentConversationProfiles: Record<ParentConversationId, { initials: string; name: string; role: string; preview: string; time: string }> = {
  teacher: { initials: "MK", name: "Madina Karimova", role: "Matematika o‘qituvchisi", preview: "Boburning yangi roadmapini tasdiqladim...", time: "10:24" },
  academic: { initials: "BA", name: "BilimYo‘l akademik bo‘limi", role: "Akademik yordam markazi", preview: "Keyingi diagnostika sanasi yangilandi.", time: "Kecha" },
};

function PortalBrand() {
  return (
    <div className="portal-brand">
      <span><BookOpenCheck size={21} /></span>
      <div><strong>BilimYo‘l</strong><small>Learning system</small></div>
    </div>
  );
}

function WorkspaceShell({ session, nav, active, onChange, onLogout, roleLabel, children }: {
  session: WorkspaceSession;
  nav: NavItem[];
  active: string;
  onChange: (id: string) => void;
  onLogout: () => void;
  roleLabel: string;
  children: ReactNode;
}) {
  const initials = session.user.full_name.split(" ").map((part) => part[0]).slice(0, 2).join("");
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    if (typeof window === "undefined") return true;
    try {
      const saved = window.localStorage.getItem("bilimyol_sidebar_open");
      return saved === null ? true : saved === "true";
    } catch {
      return true;
    }
  });

  useEffect(() => {
    const closeSidebarForExam = () => {
      setSidebarOpen(false);
      try {
        window.localStorage.setItem("bilimyol_sidebar_open", "false");
      } catch {
        // The toggle still works when storage is unavailable.
      }
    };

    window.addEventListener("bilimyol-exam-start", closeSidebarForExam);
    return () => window.removeEventListener("bilimyol-exam-start", closeSidebarForExam);
  }, []);

  useEffect(() => {
    const syncSettings = () => {
      try {
        const saved = window.localStorage.getItem("bilimyol_system_settings");
        if (saved) setNotificationsEnabled(Boolean((JSON.parse(saved) as { notifications?: boolean }).notifications));
      } catch {
        setNotificationsEnabled(true);
      }
    };
    syncSettings();
    window.addEventListener("bilimyol-settings-change", syncSettings);
    return () => window.removeEventListener("bilimyol-settings-change", syncSettings);
  }, []);

  const toggleSidebar = () => {
    setSidebarOpen((current) => {
      const next = !current;
      try {
        window.localStorage.setItem("bilimyol_sidebar_open", String(next));
      } catch {
        // Keep the interaction available even if localStorage is blocked.
      }
      return next;
    });
  };

  return (
    <main className={`workspace-shell ${sidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
      <aside className="workspace-sidebar" aria-hidden={!sidebarOpen}>
        <PortalBrand />
        <div className="workspace-role"><span>{roleLabel}</span><small>Prezident maktabi · Demo</small></div>
        <nav aria-label={`${roleLabel} bo‘limlari`}>
          {nav.map((item) => {
            const Icon = item.icon;
            return <button key={item.id} className={active === item.id ? "active" : ""} onClick={() => onChange(item.id)}><Icon size={18} /><span>{item.label}</span>{item.badge && <em>{item.badge}</em>}</button>;
          })}
        </nav>
        <div className="sidebar-support"><Sparkles size={18} /><strong>Yordam kerakmi?</strong><p>Metodist bilan 0000 raqami orqali bog‘laning.</p><a href="tel:0000">Yordam markazi <ArrowRight size={14} /></a></div>
        <button className="sidebar-logout" onClick={onLogout}><LogOut size={17} /> Tizimdan chiqish</button>
      </aside>
      <section className="workspace-main">
        <header className="workspace-topbar">
          <div className="topbar-left">
            <button
              className="sidebar-toggle"
              onClick={toggleSidebar}
              aria-label={sidebarOpen ? "Yon menyuni yopish" : "Yon menyuni ochish"}
              aria-expanded={sidebarOpen}
              title={sidebarOpen ? "Yon menyuni yopish" : "Yon menyuni ochish"}
            >
              {sidebarOpen ? <PanelLeftClose size={19} /> : <PanelLeftOpen size={19} />}
            </button>
            <div className="workspace-search"><Search size={17} /><input aria-label="Kabinet bo‘yicha izlash" placeholder="Qidirish..." /></div>
          </div>
          <div className="topbar-actions"><button aria-label="Bildirishnomalar"><Bell size={18} />{notificationsEnabled && <i />}</button><div className="profile-chip"><span>{initials}</span><div><strong>{session.user.full_name}</strong><small>{roleLabel}</small></div><ChevronDown size={15} /></div></div>
        </header>
        <div className="workspace-content">{children}</div>
      </section>
    </main>
  );
}

function MetricCard({ icon: Icon, label, value, note, tone = "navy" }: { icon: LucideIcon; label: string; value: string | number; note: string; tone?: string }) {
  return <article className={`portal-metric ${tone}`}><span><Icon size={20} /></span><div><small>{label}</small><strong>{value}</strong><p>{note}</p></div></article>;
}

function ScoreRing({ score, label }: { score: number; label: string }) {
  return <div className="mini-score-ring" style={{ "--score": `${score * 3.6}deg` } as CSSProperties}><div><strong>{score}</strong><small>/100</small></div><span>{label}</span></div>;
}

function SubjectProgress({ title, score, color }: { title: string; score: number; color: string }) {
  return <div className="subject-progress"><div><strong>{title}</strong><span>{score}/100</span></div><div><i style={{ width: `${score}%`, background: color }} /></div></div>;
}

function PageTitle({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="portal-page-title"><div><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}

export function ParentWorkspace({ session, onLogout, onOpenReport }: { session: WorkspaceSession; onLogout: () => void; onOpenReport: () => void }) {
  const [active, setActive] = useState("overview");
  const [selectedConversation, setSelectedConversation] = useState<ParentConversationId>("teacher");
  const [draftMessage, setDraftMessage] = useState("");
  const [unreadConversations, setUnreadConversations] = useState<Set<ParentConversationId>>(() => new Set(["teacher", "academic"]));
  const [parentMessages, setParentMessages] = useState<Record<ParentConversationId, ParentChatMessage[]>>({
    teacher: [
      { id: "teacher-1", own: false, text: "Assalomu alaykum. Boburning yangi roadmapini tasdiqladim. Bu hafta qisqa ko‘paytirish formulalariga e’tibor beramiz." },
      { id: "teacher-2", own: true, text: "Rahmat, uyda mashq vaqtini kalendarga kiritamiz." },
    ],
    academic: [
      { id: "academic-1", own: false, text: "Assalomu alaykum. Boburning keyingi diagnostikasi 24-iyulga belgilandi." },
      { id: "academic-2", own: false, text: "Imtihondan oldin shaxsiy kabinetdagi barcha vazifalarni yakunlashni tavsiya qilamiz." },
    ],
  });
  const messageInputRef = useRef<HTMLInputElement>(null);
  const score = session.report ? Math.round(Number(session.report.overall_score)) : 41;
  const activeConversation = parentConversationProfiles[selectedConversation];
  const parentNavigation = parentNav.map((item) => item.id === "messages" ? { ...item, badge: unreadConversations.size ? String(unreadConversations.size) : undefined } : item);

  const openConversation = (conversationId: ParentConversationId) => {
    setSelectedConversation(conversationId);
    setUnreadConversations((current) => {
      const next = new Set(current);
      next.delete(conversationId);
      return next;
    });
  };

  const sendParentMessage = () => {
    const text = draftMessage.trim();
    if (!text) return;
    setParentMessages((current) => ({
      ...current,
      [selectedConversation]: [...current[selectedConversation], { id: `${selectedConversation}-${Date.now()}`, own: true, text }],
    }));
    setDraftMessage("");
    window.setTimeout(() => messageInputRef.current?.focus(), 0);
  };

  const overview = <>
    <PageTitle eyebrow="Ota-ona kabineti" title={`Assalomu alaykum, ${session.user.full_name.split(" ")[0]}!`} description="Farzandingizning natijasi, vazifalari va o‘sish yo‘li bir joyda." action={<button className="portal-primary" onClick={onOpenReport}><FileBarChart size={17} /> To‘liq hisobot</button>} />
    <section className="parent-alert"><div><ShieldCheck size={23} /><span><strong>Bu hafta e’tibor:</strong> qisqa ko‘paytirish formulalari</span></div><p>Bobur 3 ta vazifadan 2 tasini bajardi. Yakshanbagacha yana 15 ta mashq qolgan.</p><button onClick={() => setActive("tasks")}>Vazifalarni ko‘rish <ArrowRight size={15} /></button></section>
    <div className="portal-metrics-grid"><MetricCard icon={TrendingUp} label="Umumiy natija" value={`${score}/100`} note="Oxirgi diagnostika" tone="red" /><MetricCard icon={ClipboardCheck} label="Haftalik bajarilish" value="67%" note="2 / 3 vazifa bajarildi" tone="gold" /><MetricCard icon={Clock3} label="O‘qish vaqti" value="3s 40d" note="Bu hafta" tone="green" /><MetricCard icon={CalendarDays} label="Keyingi nazorat" value="24-iyul" note="6 kun qoldi" tone="blue" /></div>
    <div className="portal-two-column">
      <article className="portal-card child-overview"><div className="portal-card-head"><div><span>Farzand profili</span><h2>Bobur Xasanboyev</h2></div><em>8-sinf · Prezident maktabi</em></div><div className="child-score-layout"><ScoreRing score={score} label="Umumiy ball" /><div className="subject-progress-list"><SubjectProgress title="Matematika" score={15} color="#c8564e" /><SubjectProgress title="Ingliz tili" score={56} color="#d79c10" /><SubjectProgress title="IQ" score={54} color="#4568a8" /></div></div><div className="child-insight"><Target size={19} /><span><strong>Asosiy maqsad:</strong> 3 oyda matematika natijasini 15 balldan 44 ballga olib chiqish.</span></div></article>
      <article className="portal-card"><div className="portal-card-head"><div><span>Haftalik reja</span><h2>Joriy vazifalar</h2></div><button className="portal-text-button" onClick={() => setActive("tasks")}>Barchasi</button></div><div className="compact-task-list"><div className="done"><Check size={15} /><span><strong>Qisqa ko‘paytirish videosi</strong><small>O‘quvchi · Dushanba</small></span><em>Bajarildi</em></div><div className="done"><Check size={15} /><span><strong>15 ta boshlang‘ich mashq</strong><small>O‘quvchi · Chorshanba</small></span><em>Bajarildi</em></div><div><Clock3 size={15} /><span><strong>Xato daftarini tekshirish</strong><small>Ota-ona · Yakshanba</small></span><em>Kutilmoqda</em></div></div></article>
    </div>
  </>;

  const results = <><PageTitle eyebrow="Natijalar" title="Boburning diagnostika tarixi" description="Fanlar kesimida o‘sish, kuchli tomonlar va yopilishi kerak bo‘lgan bo‘shliqlar." action={<button className="portal-primary" onClick={onOpenReport}>Diagnostik hisobot <ArrowRight size={16} /></button>} /><div className="portal-metrics-grid three"><MetricCard icon={BarChart3} label="So‘nggi ball" value={`${score}/100`} note="18-iyul diagnostikasi" tone="red" /><MetricCard icon={TrendingUp} label="O‘sish" value="+8 ball" note="Oldingi testga nisbatan" tone="green" /><MetricCard icon={Target} label="3 oylik maqsad" value="53/100" note="Roadmap prognozi" tone="gold" /></div><article className="portal-card result-detail-card"><div className="portal-card-head"><div><span>Fanlar bo‘yicha</span><h2>Joriy holat</h2></div><em>18-iyul, 2026</em></div><div className="large-subject-list"><SubjectProgress title="Matematika · algebra poydevori" score={15} color="#c8564e" /><SubjectProgress title="Ingliz tili · inferensial o‘qish" score={56} color="#d79c10" /><SubjectProgress title="Tanqidiy fikrlash · shartli mulohaza" score={54} color="#4568a8" /></div><div className="result-callout"><Sparkles size={20} /><p><strong>Metodist tavsiyasi:</strong> Matematikadagi 2 ta poydevor mavzu umumiy natijaga eng katta ta’sir qiladi. Avval qisqa ko‘paytirish formulalaridan boshlang.</p></div></article></>;

  const tasks = <><PageTitle eyebrow="Vazifalar" title="Oilaviy o‘quv rejasi" description="O‘quvchi, ota-ona va o‘qituvchiga biriktirilgan haftalik vazifalar." /><div className="task-board"><section><div className="task-column-head"><span className="role-icon student"><UserRound size={18} /></span><div><strong>O‘quvchi</strong><small>3 ta vazifa</small></div></div>{["Video darsni ko‘rish", "15 ta boshlang‘ich mashq", "Mini-test · 75% maqsad"].map((task, index) => <article key={task} className={index < 2 ? "complete" : ""}><span>{index < 2 ? <Check size={15} /> : <Clock3 size={15} />}</span><div><strong>{task}</strong><small>{index < 2 ? "Bajarildi" : "Yakshanbagacha"}</small></div></article>)}</section><section><div className="task-column-head"><span className="role-icon parent"><UsersRound size={18} /></span><div><strong>Ota-ona</strong><small>2 ta vazifa</small></div></div>{["Xato daftarini ko‘rib chiqish", "20 daqiqalik vaqtni kalendarga kiritish"].map((task) => <article key={task}><span><Clock3 size={15} /></span><div><strong>{task}</strong><small>Bu hafta</small></div></article>)}</section><section><div className="task-column-head"><span className="role-icon teacher"><BookOpenCheck size={18} /></span><div><strong>O‘qituvchi</strong><small>2 ta vazifa</small></div></div>{["Fokus mavzuga 10 daqiqa ajratish", "Mini-diagnostika tayyorlash"].map((task) => <article key={task}><span><Clock3 size={15} /></span><div><strong>{task}</strong><small>Keyingi dars</small></div></article>)}</section></div></>;

  const university = <UniversityJourney session={session} />;

  const messages = <>
    <PageTitle eyebrow="Aloqa" title="Xabarlar" description="O‘qituvchi va akademik bo‘limdan kelgan xabarlarni alohida oching va javob yuboring." action={<button className="portal-primary" onClick={() => messageInputRef.current?.focus()}><Plus size={16} /> Yangi xabar</button>} />
    <div className="message-layout">
      <div className="message-list">
        {(Object.keys(parentConversationProfiles) as ParentConversationId[]).map((conversationId) => {
          const profile = parentConversationProfiles[conversationId];
          const isUnread = unreadConversations.has(conversationId);
          return <article key={conversationId} role="button" tabIndex={0} className={selectedConversation === conversationId ? "active" : ""} onClick={() => openConversation(conversationId)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") openConversation(conversationId); }}><span>{profile.initials}</span><div><strong>{profile.name}{isUnread && <i className="message-unread-dot" />}</strong><p>{profile.preview}</p></div><small>{profile.time}</small></article>;
        })}
      </div>
      <article className="message-preview">
        <div className="message-person"><span>{activeConversation.initials}</span><div><strong>{activeConversation.name}</strong><small>{activeConversation.role}</small></div></div>
        <div className="message-thread">{parentMessages[selectedConversation].map((message) => <div key={message.id} className={`message-bubble ${message.own ? "own" : ""}`}>{message.text}</div>)}</div>
        <div className="message-compose"><input ref={messageInputRef} value={draftMessage} onChange={(event) => setDraftMessage(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") sendParentMessage(); }} placeholder={`${activeConversation.name}ga xabar yozing...`} /><button aria-label="Xabar yuborish" onClick={sendParentMessage}><ArrowRight size={17} /></button></div>
      </article>
    </div>
  </>;

  const content = active === "overview" ? overview : active === "results" ? results : active === "university" ? university : active === "tasks" ? tasks : messages;
  return <WorkspaceShell session={session} nav={parentNavigation} active={active} onChange={(id) => { setActive(id); if (id === "messages") openConversation(selectedConversation); }} onLogout={onLogout} roleLabel="Ota-ona">{content}</WorkspaceShell>;
}

export function TeacherWorkspace({ session, onLogout, onOpenReport }: { session: WorkspaceSession; onLogout: () => void; onOpenReport: () => void }) {
  const [active, setActive] = useState("overview");
  const [classroom, setClassroom] = useState("8-A");
  const [approvedRoadmaps, setApprovedRoadmaps] = useState<Set<string>>(new Set());
  const visibleStudents = classroom === "8-A" ? students : students.slice(1, 4);
  const classAverage = Math.round(visibleStudents.reduce((sum, item) => sum + item.score, 0) / visibleStudents.length);
  const pendingRoadmaps = Math.max(0, 4 - approvedRoadmaps.size);
  const teacherNavigation = teacherNav.map((item) => item.id === "roadmaps" ? { ...item, badge: pendingRoadmaps ? String(pendingRoadmaps) : undefined } : item);

  useEffect(() => {
    let savedRoadmaps: string[] = [];
    try {
      const saved = window.localStorage.getItem("bilimyol_approved_roadmaps");
      if (saved) savedRoadmaps = JSON.parse(saved) as string[];
    } catch {
      savedRoadmaps = [];
    }
    const timer = window.setTimeout(() => setApprovedRoadmaps(new Set(savedRoadmaps)), 0);
    return () => window.clearTimeout(timer);
  }, []);

  const approveRoadmap = (studentCode: string) => {
    setApprovedRoadmaps((current) => {
      const next = new Set(current);
      next.add(studentCode);
      window.localStorage.setItem("bilimyol_approved_roadmaps", JSON.stringify([...next]));
      return next;
    });
  };

  const studentTable = <article className="portal-card students-table-card"><div className="portal-card-head"><div><span>O‘quvchilar</span><h2>{classroom} sinf natijalari</h2></div><div className="table-actions"><div className="mini-search"><Search size={15} /><input placeholder="O‘quvchi izlash" /></div><button><MoreHorizontal size={18} /></button></div></div><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>O‘quvchi</th><th>Umumiy</th><th>Matematika</th><th>Ingliz tili</th><th>Tanqidiy</th><th>Vazifa</th><th>Holat</th><th /></tr></thead><tbody>{visibleStudents.map((student) => <tr key={student.code}><td><div className="table-person"><span>{student.name.split(" ").map((part) => part[0]).slice(0,2).join("")}</span><div><strong>{student.name}</strong><small>{student.code}</small></div></div></td><td><strong>{student.score}</strong></td><td>{student.math}</td><td>{student.english}</td><td>{student.critical}</td><td>{student.task}</td><td><em className={`table-status ${student.status === "Tayyor" ? "ready" : student.status === "Riskda" ? "risk" : "watch"}`}>{student.status}</em></td><td><button className="row-action" onClick={onOpenReport}><ArrowRight size={15} /></button></td></tr>)}</tbody></table></div></article>;

  const overview = <><PageTitle eyebrow="O‘qituvchi kabineti" title={`Xayrli kun, ${session.user.full_name.split(" ")[0]}!`} description="Sinf natijalari, roadmap tasdiqlari va haftalik ishlar holati." action={<div className="class-select"><School size={16} /><select value={classroom} onChange={(event) => setClassroom(event.target.value)}><option>8-A</option><option>8-B</option><option>7-A</option></select><ChevronDown size={14} /></div>} /><div className="portal-metrics-grid"><MetricCard icon={UsersRound} label="O‘quvchilar" value={visibleStudents.length === 5 ? 24 : 18} note={`${classroom} sinf ro‘yxati`} tone="navy" /><MetricCard icon={BarChart3} label="Sinf o‘rtachasi" value={`${classAverage}/100`} note="Oxirgi diagnostika" tone="gold" /><MetricCard icon={Target} label="Risk guruhida" value={visibleStudents.filter((item) => item.status === "Riskda").length} note="Qo‘shimcha e’tibor kerak" tone="red" /><MetricCard icon={ClipboardCheck} label="Roadmap tasdiqlash" value={pendingRoadmaps} note={pendingRoadmaps ? "Sizni kutmoqda" : "Barchasi tasdiqlangan"} tone="green" /></div><div className="teacher-highlight-grid"><article className="portal-card class-pulse"><div className="portal-card-head"><div><span>Sinf pulsi</span><h2>Fanlar o‘rtachasi</h2></div><em>+6.4% o‘sish</em></div><SubjectProgress title="Matematika" score={58} color="#c8564e" /><SubjectProgress title="Ingliz tili" score={71} color="#d79c10" /><SubjectProgress title="Tanqidiy fikrlash" score={64} color="#4568a8" /></article><article className="portal-card"><div className="portal-card-head"><div><span>Bugungi reja</span><h2>3 ta muhim ish</h2></div><CalendarDays size={20} /></div><div className="teacher-agenda"><div><span>09:00</span><p><strong>8-A · Algebra fokusi</strong>Qisqa ko‘paytirish formulalari</p></div><div><span>12:30</span><p><strong>Roadmap ko‘rib chiqish</strong>4 o‘quvchi tasdiq kutmoqda</p></div><div><span>15:00</span><p><strong>Mini-diagnostika</strong>8-B sinf · 25 daqiqa</p></div></div></article></div>{studentTable}</>;

  const classroomPanel = <><PageTitle eyebrow="Sinf diagnostikasi" title="O‘quvchilar kesimidagi natijalar" description="Sinfni tanlang, har bir o‘quvchining fan natijasi va holatini ko‘ring." action={<div className="class-select"><School size={16} /><select value={classroom} onChange={(event) => setClassroom(event.target.value)}><option>8-A</option><option>8-B</option><option>7-A</option></select><ChevronDown size={14} /></div>} /><div className="portal-metrics-grid three"><MetricCard icon={UsersRound} label="Sinf hajmi" value="24" note="22 faol o‘quvchi" /><MetricCard icon={BarChart3} label="O‘rtacha ball" value={`${classAverage}/100`} note="Uch fan bo‘yicha" tone="gold" /><MetricCard icon={UserCheck} label="Tayyor o‘quvchilar" value="9" note="Minimal chegaradan yuqori" tone="green" /></div>{studentTable}</>;

  const roadmaps = <><PageTitle eyebrow="Roadmaplar" title="Tasdiqlash navbati" description="Diagnostikadan keyin yaratilgan individual rejalarni ko‘rib chiqing." /><div className="approval-grid">{students.slice(0,4).map((student, index) => {
    const approved = approvedRoadmaps.has(student.code);
    return <article className={`portal-card approval-card ${approved ? "approved-card" : ""}`} key={student.code}><div className="approval-head"><span>{student.name.split(" ").map((part) => part[0]).slice(0,2).join("")}</span><div><strong>{student.name}</strong><small>{student.code} · 8-A</small></div><em className={approved ? "approved-status" : ""}>{approved ? "Tasdiqlandi" : index === 0 ? "Yangi" : "Ko‘rib chiqish"}</em></div><div className="approval-focus"><small>Asosiy fokus</small><strong>{index % 2 ? "Inferensial o‘qish" : "Qisqa ko‘paytirish formulalari"}</strong><span>{student.score} → {Math.min(student.score + 24, 88)} ball</span></div><div className="approval-actions"><button onClick={onOpenReport}>Ko‘rib chiqish</button><button className={`approve ${approved ? "approved" : ""}`} disabled={approved} onClick={() => approveRoadmap(student.code)}><CheckCircle2 size={15} /> {approved ? "Tasdiqlandi" : "Tasdiqlash"}</button></div></article>;
  })}</div></>;

  const assignments = <><PageTitle eyebrow="Topshiriqlar" title="Sinf uchun vazifalar" description="Haftalik mashqlarni yarating, biriktiring va bajarilishini kuzating." action={<button className="portal-primary"><Plus size={16} /> Yangi topshiriq</button>} /><article className="portal-card"><div className="portal-card-head"><div><span>Joriy hafta</span><h2>Faol topshiriqlar</h2></div><em>18–24 iyul</em></div><div className="assignment-list">{[["Qisqa ko‘paytirish · 20 mashq","8-A","18 / 24","75%"],["Inference reading · 2 passage","8-A","21 / 24","88%"],["Shartli mulohaza · mini-test","8-B","12 / 18","67%"]].map((item) => <div key={item[0]}><span className="assignment-icon"><ClipboardList size={18} /></span><div><strong>{item[0]}</strong><small>{item[1]} sinf</small></div><p><strong>{item[2]}</strong><small>Bajardi</small></p><em>{item[3]}</em><button><MoreHorizontal size={17} /></button></div>)}</div></article></>;

  const content = active === "overview" ? overview : active === "classroom" ? classroomPanel : active === "roadmaps" ? roadmaps : assignments;
  return <WorkspaceShell session={session} nav={teacherNavigation} active={active} onChange={setActive} onLogout={onLogout} roleLabel="O‘qituvchi">{content}</WorkspaceShell>;
}

export function AdminWorkspace({ session, onLogout, onOpenReport, onOpenExamResult }: {
  session: WorkspaceSession;
  onLogout: () => void;
  onOpenReport: () => void;
  onOpenExamResult: (result: MiniExamResult) => void;
}) {
  const [active, setActive] = useState("overview");
  const [selectedClass, setSelectedClass] = useState("Barcha sinflar");
  const [, setShowCreateExam] = useState(false);
  const [systemSettings, setSystemSettings] = useState({ notifications: true, autoSave: true, compactMode: false });
  const [settingsNotice, setSettingsNotice] = useState("");
  const filteredStudents = useMemo(() => selectedClass === "Barcha sinflar" ? students : selectedClass === "8-A" ? students : students.slice(1, 4), [selectedClass]);

  useEffect(() => {
    let savedSettings = { notifications: true, autoSave: true, compactMode: false };
    try {
      const saved = window.localStorage.getItem("bilimyol_system_settings");
      if (saved) savedSettings = JSON.parse(saved) as typeof savedSettings;
    } catch {
      savedSettings = { notifications: true, autoSave: true, compactMode: false };
    }
    const timer = window.setTimeout(() => setSystemSettings(savedSettings), 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("bilimyol-compact", systemSettings.compactMode);
  }, [systemSettings.compactMode]);

  const toggleSystemSetting = (key: keyof typeof systemSettings) => {
    setSystemSettings((current) => {
      const next = { ...current, [key]: !current[key] };
      window.localStorage.setItem("bilimyol_system_settings", JSON.stringify(next));
      window.dispatchEvent(new Event("bilimyol-settings-change"));
      return next;
    });
    setSettingsNotice("Sozlama saqlandi");
    window.setTimeout(() => setSettingsNotice(""), 1800);
  };

  const classPicker = <div className="class-select"><School size={16} /><select value={selectedClass} onChange={(event) => setSelectedClass(event.target.value)}><option>Barcha sinflar</option><option>8-A</option><option>8-B</option><option>7-A</option></select><ChevronDown size={14} /></div>;

  const overview = <><PageTitle eyebrow="Administrator paneli" title="Akademik boshqaruv markazi" description="Imtihonlar, sinflar, foydalanuvchilar va tizim holati bir joyda." action={<button className="portal-primary" onClick={() => { setActive("exams"); setShowCreateExam(true); }}><FilePlus2 size={17} /> Yangi imtihon</button>} /><div className="portal-metrics-grid"><MetricCard icon={GraduationCap} label="Jami o‘quvchi" value={session.dashboard.students || 486} note="+32 bu oy" tone="navy" /><MetricCard icon={ClipboardList} label="Faol imtihon" value="6" note="3 tasi bugun" tone="gold" /><MetricCard icon={CheckCircle2} label="Yakunlangan" value={session.dashboard.completed_attempts || 428} note="88% topshirish darajasi" tone="green" /><MetricCard icon={BarChart3} label="Platforma o‘rtachasi" value={`${Math.round(Number(session.dashboard.average_score) || 68)}/100`} note="Uch fan bo‘yicha" tone="blue" /></div><div className="admin-overview-grid"><article className="portal-card admin-chart-card"><div className="portal-card-head"><div><span>Faollik</span><h2>Haftalik test topshirish</h2></div><em>+18.2%</em></div><div className="bar-chart-demo">{[38,56,44,72,64,88,76].map((height,index) => <div key={index}><i style={{height:`${height}%`}} /><span>{["Du","Se","Cho","Pa","Ju","Sha","Ya"][index]}</span></div>)}</div></article><article className="portal-card"><div className="portal-card-head"><div><span>Tayyorlik</span><h2>Umumiy holat</h2></div><ShieldCheck size={21} /></div><div className="readiness-donut"><div><strong>50%</strong><small>Tayyor</small></div></div><div className="donut-legend"><span><i className="ready" />214 tayyor</span><span><i className="risk" />214 tayyor emas</span></div></article></div><article className="portal-card"><div className="portal-card-head"><div><span>So‘nggi imtihonlar</span><h2>Faol jarayonlar</h2></div><button className="portal-text-button" onClick={() => setActive("exams")}>Barchasini ko‘rish</button></div><div className="exam-compact-list">{[["8-sinf kirish diagnostikasi","8-A, 8-B","186 / 220","Faol"],["Matematika mini-diagnostika","7-A","42 / 48","Faol"],["Ingliz tili nazorat testi","8-A","24 / 24","Yakunlangan"]].map((exam) => <div key={exam[0]}><span><ClipboardList size={18} /></span><div><strong>{exam[0]}</strong><small>{exam[1]}</small></div><p>{exam[2]}<small>Topshirdi</small></p><em className={exam[3] === "Faol" ? "active" : "done"}>{exam[3]}</em><button><MoreHorizontal size={17} /></button></div>)}</div></article></>;

  const exams = <AdminTestsPanel onComplete={onOpenExamResult} />;

  const classes = <><PageTitle eyebrow="Sinf boshqaruvi" title="Sinflar va o‘quvchilar" description="Sinfni tanlang — tarkibi, o‘qituvchisi va diagnostika holati avtomatik chiqadi." action={classPicker} /><div className="class-summary-grid">{[["8-A","24 o‘quvchi","Madina Karimova","68"],["8-B","18 o‘quvchi","Akmal Saidov","61"],["7-A","22 o‘quvchi","Nigora Aliyeva","72"]].map((item) => <button key={item[0]} className={selectedClass === item[0] ? "active" : ""} onClick={() => setSelectedClass(item[0])}><span><School size={21} /></span><div><strong>{item[0]}</strong><small>{item[1]} · {item[2]}</small></div><em>{item[3]}<small>o‘rtacha</small></em></button>)}</div><article className="portal-card students-table-card"><div className="portal-card-head"><div><span>{selectedClass}</span><h2>O‘quvchilar ro‘yxati</h2></div><button className="portal-primary"><Plus size={16} /> O‘quvchi qo‘shish</button></div><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>O‘quvchi</th><th>Kod</th><th>Umumiy ball</th><th>Vazifalar</th><th>Holat</th><th /></tr></thead><tbody>{filteredStudents.map((student) => <tr key={student.code}><td><div className="table-person"><span>{student.name.split(" ").map((part) => part[0]).slice(0,2).join("")}</span><strong>{student.name}</strong></div></td><td>{student.code}</td><td><strong>{student.score}/100</strong></td><td>{student.task}</td><td><em className={`table-status ${student.status === "Tayyor" ? "ready" : student.status === "Riskda" ? "risk" : "watch"}`}>{student.status}</em></td><td><button className="row-action" onClick={onOpenReport}><ArrowRight size={15} /></button></td></tr>)}</tbody></table></div></article></>;

  const users = <><PageTitle eyebrow="Foydalanuvchilar" title="Rollar va kirishlar" description="O‘quvchi, ota-ona, o‘qituvchi va administrator hisoblarini boshqaring." action={<button className="portal-primary"><Plus size={16} /> Foydalanuvchi qo‘shish</button>} /><div className="portal-metrics-grid"><MetricCard icon={GraduationCap} label="O‘quvchilar" value="486" note="24 ta sinf" /><MetricCard icon={UsersRound} label="Ota-onalar" value="421" note="86% bog‘langan" tone="gold" /><MetricCard icon={BookOpenCheck} label="O‘qituvchilar" value="38" note="12 ta fan yo‘nalishi" tone="green" /><MetricCard icon={ShieldCheck} label="Administratorlar" value="4" note="Barcha faol" tone="blue" /></div><article className="portal-card"><div className="portal-card-head"><div><span>Oxirgi qo‘shilganlar</span><h2>Foydalanuvchilar</h2></div><div className="mini-search"><Search size={15} /><input placeholder="Ism yoki login" /></div></div><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>Foydalanuvchi</th><th>Login</th><th>Rol</th><th>Holat</th><th>Qo‘shilgan</th><th /></tr></thead><tbody>{[["Bobur Xasanboyev","student","O‘quvchi","Faol","18-iyul"],["Dilnoza Xasanboyeva","parent","Ota-ona","Faol","18-iyul"],["Madina Karimova","teacher","O‘qituvchi","Faol","12-iyul"],["Azizbek Rahimov","admin","Administrator","Faol","01-iyul"]].map((user) => <tr key={user[1]}><td><strong>{user[0]}</strong></td><td>{user[1]}</td><td><span className="role-label">{user[2]}</span></td><td><em className="table-status ready">{user[3]}</em></td><td>{user[4]}</td><td><button className="row-action"><MoreHorizontal size={16} /></button></td></tr>)}</tbody></table></div></article></>;

  const settings = <>
    <PageTitle eyebrow="Sozlamalar" title="Oddiy tizim sozlamalari" description="Faqat kundalik boshqaruv uchun kerak bo‘lgan 3 ta asosiy sozlama qoldirildi." action={settingsNotice ? <span className="settings-saved"><CheckCircle2 size={15} /> {settingsNotice}</span> : undefined} />
    <div className="settings-grid simple-settings">
      <article className="portal-card setting-card"><span><Bell size={21} /></span><div><strong>Kabinet bildirishnomalari</strong><p>Yangi xabar, natija va roadmap bo‘yicha kabinet ichida ogohlantirish ko‘rsatiladi.</p><small>{systemSettings.notifications ? "Yoqilgan" : "O‘chirilgan"}</small></div><button className={`setting-toggle ${systemSettings.notifications ? "on" : ""}`} aria-pressed={systemSettings.notifications} onClick={() => toggleSystemSetting("notifications")}><i /></button></article>
      <article className="portal-card setting-card"><span><ClipboardCheck size={21} /></span><div><strong>Imtihonni avtomatik saqlash</strong><p>Yakunlangan mini-imtihonlar administrator tarixida avtomatik saqlanadi.</p><small>{systemSettings.autoSave ? "Yoqilgan" : "O‘chirilgan"}</small></div><button className={`setting-toggle ${systemSettings.autoSave ? "on" : ""}`} aria-pressed={systemSettings.autoSave} onClick={() => toggleSystemSetting("autoSave")}><i /></button></article>
      <article className="portal-card setting-card"><span><UserCheck size={21} /></span><div><strong>Ixcham interfeys</strong><p>Yon menyu va sahifa oraliqlarini kichraytirib, ekranga ko‘proq ma’lumot joylaydi.</p><small>{systemSettings.compactMode ? "Yoqilgan" : "O‘chirilgan"}</small></div><button className={`setting-toggle ${systemSettings.compactMode ? "on" : ""}`} aria-pressed={systemSettings.compactMode} onClick={() => toggleSystemSetting("compactMode")}><i /></button></article>
    </div>
  </>;

  const content = active === "overview" ? overview : active === "exams" ? exams : active === "classes" ? classes : active === "users" ? users : settings;
  return <WorkspaceShell session={session} nav={adminNav} active={active} onChange={setActive} onLogout={onLogout} roleLabel="Administrator">{content}</WorkspaceShell>;
}
