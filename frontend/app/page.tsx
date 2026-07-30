"use client";

import {
  ArrowRight,
  BarChart3,
  BookOpenCheck,
  BrainCircuit,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Download,
  Eye,
  EyeOff,
  FileCheck2,
  Languages,
  Lightbulb,
  LockKeyhole,
  LogOut,
  Menu,
  Printer,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  UserRound,
  UsersRound,
  X,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { AdminWorkspace, ParentWorkspace, StudentWorkspace, TeacherWorkspace } from "./components/role-workspaces";
import { UniversityJourney } from "./components/dream-university";
import { RbisBrand } from "./components/rbis-brand";
import {
  MINI_EXAM_STORAGE_KEY,
  MINI_EXAM_STUDENT_RESULTS_KEY,
  hydrateMiniExamResult,
  miniExamQuestions,
  normalizeCandidate,
  type MiniExamResult,
} from "./lib/mini-exam";
import {
  clearApiSession,
  createDemoWorkspace,
  demoCredentials,
  hasDemoMode,
  hasLiveApi,
  loginWorkspace,
  restoreWorkspaceSession,
  type LiveDiagnosticReport,
  type UserRole,
  type WorkspaceSession,
} from "./lib/api";
import { RBIS_COLORS, rbisChartColor } from "./lib/rbis-theme";

type SubjectId = "overall" | "math" | "english" | "critical";
type ReportTab = SubjectId | "university";
type QuestionStatus = "correct" | "wrong";

type Question = {
  code: string;
  status: QuestionStatus;
  topic: string;
  skill: string;
  difficulty: "Boshlang‘ich" | "O‘rta" | "Yuqori";
};

type Subject = {
  id: Exclude<SubjectId, "overall">;
  title: string;
  score: number;
  rank: string;
  percentile: number;
  potential: number;
  accent: string;
  pale: string;
  icon: LucideIcon;
  strong: string[];
  weak: string[];
  skills: number[];
  questions: Question[];
  focus: string;
  nextFocus: string;
};

const skillLabels = [
  "Algebraik fikrlash",
  "Geometrik-fazoviy tafakkur",
  "Masalani modellashtirish",
  "Muammoni yechish",
  "Konseptual tushunish",
  "Hisoblash aniqligi",
  "Mantiqiy mulohaza",
];

const mathQuestions: Question[] = [
  { code: "M1", status: "correct", topic: "Daraja xossalarini moslashtirish", skill: "Algebraik fikrlash", difficulty: "Boshlang‘ich" },
  { code: "M2", status: "correct", topic: "Bir xil asosli darajalarni ko‘paytirish", skill: "Algebraik fikrlash", difficulty: "Boshlang‘ich" },
  { code: "M3", status: "wrong", topic: "Yig‘indi kvadratini yoyish", skill: "Algebraik fikrlash", difficulty: "O‘rta" },
  { code: "M4", status: "correct", topic: "Ifodalarni ajratilgan ko‘rinish bilan moslashtirish", skill: "Algebraik fikrlash", difficulty: "O‘rta" },
  { code: "M5", status: "correct", topic: "Funksiya qiymatini hisoblash", skill: "Algebraik fikrlash", difficulty: "Boshlang‘ich" },
  { code: "M6", status: "wrong", topic: "Qisqa ko‘paytirishdagi xatoni ilg‘ash", skill: "Konseptual tushunish", difficulty: "O‘rta" },
  { code: "M7", status: "wrong", topic: "Daraja qiymatlarini tartiblash", skill: "Hisoblash aniqligi", difficulty: "O‘rta" },
  { code: "M8", status: "wrong", topic: "Vertikal burchaklar tengligi", skill: "Geometrik-fazoviy tafakkur", difficulty: "Boshlang‘ich" },
  { code: "M9", status: "wrong", topic: "Koeffitsiyent va darajani ko‘paytirish", skill: "Algebraik fikrlash", difficulty: "O‘rta" },
  { code: "M10", status: "correct", topic: "Ichki burchaklar yig‘indisi", skill: "Geometrik-fazoviy tafakkur", difficulty: "O‘rta" },
  { code: "M11", status: "wrong", topic: "Qavslarni ochish va ixchamlash", skill: "Algebraik fikrlash", difficulty: "O‘rta" },
  { code: "M12", status: "wrong", topic: "Kvadratlar ayirmasi", skill: "Algebraik fikrlash", difficulty: "Yuqori" },
  { code: "M13", status: "wrong", topic: "Ikki tomonda noma’lum qatnashgan tenglama", skill: "Algebraik fikrlash", difficulty: "Yuqori" },
  { code: "M14", status: "wrong", topic: "Darajali ifodalarni bo‘lish", skill: "Konseptual tushunish", difficulty: "O‘rta" },
  { code: "M15", status: "wrong", topic: "Inkorga asoslangan mantiqiy xulosa", skill: "Mantiqiy mulohaza", difficulty: "Yuqori" },
];

const englishQuestions: Question[] = [
  { code: "E1", status: "correct", topic: "Main idea", skill: "Faktik o‘qish", difficulty: "Boshlang‘ich" },
  { code: "E2", status: "correct", topic: "Context vocabulary", skill: "Leksik tahlil", difficulty: "O‘rta" },
  { code: "E3", status: "wrong", topic: "Author’s purpose", skill: "Inferensial o‘qish", difficulty: "O‘rta" },
  { code: "E4", status: "correct", topic: "Reference words", skill: "Matn bog‘lanishi", difficulty: "Boshlang‘ich" },
  { code: "E5", status: "wrong", topic: "Implied conclusion", skill: "Inferensial o‘qish", difficulty: "Yuqori" },
  { code: "E6", status: "correct", topic: "Sentence completion", skill: "Grammatik aniqlik", difficulty: "O‘rta" },
  { code: "E7", status: "wrong", topic: "Tone and attitude", skill: "Tanqidiy o‘qish", difficulty: "Yuqori" },
  { code: "E8", status: "correct", topic: "Specific information", skill: "Faktik o‘qish", difficulty: "O‘rta" },
  { code: "E9", status: "wrong", topic: "Paragraph function", skill: "Matn strukturasi", difficulty: "O‘rta" },
  { code: "E10", status: "correct", topic: "Grammar in context", skill: "Grammatik aniqlik", difficulty: "Boshlang‘ich" },
];

const criticalQuestions: Question[] = [
  { code: "T1", status: "correct", topic: "Oddiy ketma-ketlik", skill: "Qonuniyatni topish", difficulty: "Boshlang‘ich" },
  { code: "T2", status: "wrong", topic: "Shartli mulohaza", skill: "Mantiqiy xulosa", difficulty: "O‘rta" },
  { code: "T3", status: "correct", topic: "Ortiqcha element", skill: "Tasniflash", difficulty: "Boshlang‘ich" },
  { code: "T4", status: "wrong", topic: "Ikki bosqichli qonuniyat", skill: "Qonuniyatni topish", difficulty: "Yuqori" },
  { code: "T5", status: "correct", topic: "Analogiya", skill: "Mantiqiy bog‘lanish", difficulty: "O‘rta" },
  { code: "T6", status: "wrong", topic: "Zarur va yetarli shart", skill: "Mantiqiy xulosa", difficulty: "Yuqori" },
  { code: "T7", status: "correct", topic: "Vizual matritsa", skill: "Fazoviy qonuniyat", difficulty: "O‘rta" },
  { code: "T8", status: "wrong", topic: "Dalilni baholash", skill: "Tanqidiy baholash", difficulty: "Yuqori" },
  { code: "T9", status: "correct", topic: "Sonli bog‘lanish", skill: "Qonuniyatni topish", difficulty: "O‘rta" },
  { code: "T10", status: "wrong", topic: "Xulosaga qarshi misol", skill: "Mantiqiy xulosa", difficulty: "Yuqori" },
];

const subjects: Subject[] = [
  {
    id: "math",
    title: "Matematika",
    score: 15,
    rank: "42 / 53",
    percentile: 23,
    potential: 10,
    accent: RBIS_COLORS.primary,
    pale: RBIS_COLORS.cream,
    icon: BarChart3,
    strong: ["Algebraik fikrlash"],
    weak: ["Konseptual tushunish", "Hisoblash aniqligi", "Mantiqiy mulohaza", "Modellashtirish"],
    skills: [29, 17, 0, 8, 0, 0, 0],
    questions: mathQuestions,
    focus: "Qisqa ko‘paytirish formulalari",
    nextFocus: "Ko‘paytuvchilarga ajratish",
  },
  {
    id: "english",
    title: "Ingliz tili",
    score: 56,
    rank: "29 / 34",
    percentile: 38,
    potential: 62,
    accent: RBIS_COLORS.hover,
    pale: RBIS_COLORS.surface,
    icon: Languages,
    strong: ["Faktik o‘qish", "Grammatik aniqlik"],
    weak: ["Inferensial o‘qish", "Muallif pozitsiyasi"],
    skills: [58, 44, 49, 62, 53, 66, 41],
    questions: englishQuestions,
    focus: "Inferensial o‘qish",
    nextFocus: "Academic vocabulary",
  },
  {
    id: "critical",
    title: "IQ",
    score: 54,
    rank: "31 / 53",
    percentile: 41,
    potential: 60,
    accent: RBIS_COLORS.deep,
    pale: RBIS_COLORS.cream,
    icon: BrainCircuit,
    strong: ["Tasniflash", "Vizual analogiya"],
    weak: ["Shartli mulohaza", "Dalilni baholash"],
    skills: [54, 61, 47, 57, 52, 48, 39],
    questions: criticalQuestions,
    focus: "Shartli mulohaza",
    nextFocus: "Ko‘p bosqichli ketma-ketlik",
  },
];

const roadmapCopy: Record<Exclude<SubjectId, "overall">, { stages: { period: string; title: string; from: number; to: number; hours: string }[]; weeks: { title: string; task: string }[] }> = {
  math: {
    stages: [
      { period: "0–3 oy", title: "Qisqa ko‘paytirish formulalari", from: 15, to: 44, hours: "4–5 soat/hafta" },
      { period: "3–6 oy", title: "Daraja xossalari", from: 44, to: 67, hours: "3–4 soat/hafta" },
      { period: "6–12 oy", title: "Ko‘paytuvchilarga ajratish", from: 67, to: 85, hours: "3–4 soat/hafta" },
    ],
    weeks: [
      { title: "Qisqa ko‘paytirish formulalari", task: "Asosiy tushuncha — 1 video + 15 ta boshlang‘ich mashq" },
      { title: "Qisqa ko‘paytirish formulalari", task: "Chuqurlashtirish — real masalalar + 2 ta ko‘p bosqichli topshiriq" },
      { title: "Qisqa ko‘paytirish formulalari", task: "Mustahkamlash — 20 ta aralash mashq + mini-test" },
      { title: "Ko‘paytuvchilarga ajratish", task: "Asosiy tushuncha — 1 video + 15 ta boshlang‘ich mashq" },
      { title: "Umumiy takror", task: "Oldingi mavzular aralash mashqi + xato daftari" },
      { title: "Mini-diagnostika", task: "25 daqiqalik nazorat va yangi natijani o‘lchash" },
    ],
  },
  english: {
    stages: [
      { period: "0–3 oy", title: "Inferensial o‘qish", from: 56, to: 68, hours: "3–4 soat/hafta" },
      { period: "3–6 oy", title: "Academic vocabulary", from: 68, to: 78, hours: "3 soat/hafta" },
      { period: "6–12 oy", title: "Timed reading", from: 78, to: 88, hours: "3–4 soat/hafta" },
    ],
    weeks: [
      { title: "Yashirin ma’noni topish", task: "2 ta qisqa matn + dalillarni belgilash" },
      { title: "Muallif maqsadi", task: "Tone va purpose bo‘yicha 18 ta savol" },
      { title: "Xulosa chiqarish", task: "Inference drill + xato javoblar tahlili" },
      { title: "Academic vocabulary", task: "40 ta so‘z + context practice" },
      { title: "Aralash reading", task: "2 ta timed passage" },
      { title: "Mini-diagnostika", task: "30 daqiqalik reading nazorati" },
    ],
  },
  critical: {
    stages: [
      { period: "0–3 oy", title: "Shartli mulohaza", from: 54, to: 66, hours: "3–4 soat/hafta" },
      { period: "3–6 oy", title: "Ko‘p bosqichli ketma-ketlik", from: 66, to: 78, hours: "3–4 soat/hafta" },
      { period: "6–12 oy", title: "Dalilni baholash", from: 78, to: 88, hours: "3 soat/hafta" },
    ],
    weeks: [
      { title: "Agar–unda modeli", task: "Qoidani o‘rganish + 12 ta asosiy savol" },
      { title: "Zarur va yetarli shart", task: "Diagramma + 15 ta mashq" },
      { title: "Qarshi misol", task: "Dalilni buzuvchi misollar bilan ishlash" },
      { title: "Ketma-ketlik", task: "3 qadamli qonuniyatlar" },
      { title: "Aralash reasoning", task: "Ikki fokusdan 20 ta savol" },
      { title: "Mini-diagnostika", task: "Vaqtli nazorat + xatolar tahlili" },
    ],
  },
};

const levels = [
  { label: "Sayoz", min: 0, max: 35, color: RBIS_COLORS.error },
  { label: "Zaif", min: 35, max: 50, color: RBIS_COLORS.hover },
  { label: "O‘rtacha", min: 50, max: 67, color: RBIS_COLORS.warning },
  { label: "Yaxshi", min: 67, max: 84, color: RBIS_COLORS.primary },
  { label: "Juda yaxshi", min: 84, max: 100, color: RBIS_COLORS.success },
];


function buildMiniExamSubjects(result: MiniExamResult): Subject[] {
  const hydrated = hydrateMiniExamResult(result);
  const answers = hydrated.answers ?? {};
  const scores = hydrated.subjectScores ?? { math: 0, english: 0, logic: 0 };

  const subjectConfig = [
    {
      id: "math" as const,
      miniId: "math" as const,
      prefix: "M",
      skill: "Hisoblash va algebraik fikrlash",
      strong: "Hisoblash aniqligi",
      weak: "Algebraik fikrlash",
      focus: "Asosiy arifmetika va sodda tenglamalar",
      nextFocus: "Masalani bosqichma-bosqich yechish",
    },
    {
      id: "english" as const,
      miniId: "english" as const,
      prefix: "E",
      skill: "Lug‘at va grammatika",
      strong: "Leksik tushunish",
      weak: "Grammatik aniqlik",
      focus: "Asosiy lug‘at va gap tuzilishi",
      nextFocus: "Matnni tushunish va grammar",
    },
    {
      id: "critical" as const,
      miniId: "logic" as const,
      prefix: "I",
      skill: "Mantiqiy xulosa",
      strong: "Qonuniyatni topish",
      weak: "Shartli mulohaza",
      focus: "Ketma-ketlik va mantiqiy bog‘lanish",
      nextFocus: "Ko‘p bosqichli mantiqiy masalalar",
    },
  ];

  return subjectConfig.map((config) => {
    const base = subjects.find((subject) => subject.id === config.id)!;
    const miniQuestions = miniExamQuestions.filter((question) => question.subjectId === config.miniId);
    const score = scores[config.miniId];
    const correctCount = miniQuestions.filter((question) => answers[question.id] === question.correct).length;
    const questions: Question[] = miniQuestions.map((question, index) => ({
      code: `${config.prefix}${index + 1}`,
      status: answers[question.id] === question.correct ? "correct" : "wrong",
      topic: question.text,
      skill: config.skill,
      difficulty: index === miniQuestions.length - 1 ? "O‘rta" : "Boshlang‘ich",
    }));

    return {
      ...base,
      score,
      rank: `${correctCount} / ${miniQuestions.length}`,
      percentile: score,
      potential: Math.min(score + 20, 100),
      strong: score >= 60 ? [config.strong] : ["Boshlang‘ich bilimlar"],
      weak: score >= 60 ? [config.weak] : [config.weak, config.focus],
      skills: [
        score,
        Math.max(score - 8, 0),
        Math.min(score + 5, 100),
        Math.max(score - 14, 0),
        Math.min(score + 10, 100),
        Math.max(score - 5, 0),
        Math.max(score - 12, 0),
      ],
      questions,
      focus: config.focus,
      nextFocus: config.nextFocus,
    };
  });
}

const roleOptions: { id: UserRole; label: string; description: string; icon: LucideIcon }[] = [
  { id: "student", label: "O‘quvchi", description: "Test va shaxsiy roadmap", icon: UserRound },
  { id: "parent", label: "Ota-ona", description: "Farzand nazorati", icon: UsersRound },
  { id: "teacher", label: "O‘qituvchi", description: "Sinf diagnostikasi", icon: BookOpenCheck },
  { id: "admin", label: "Admin", description: "Imtihon boshqaruvi", icon: ShieldCheck },
];

function Login({ onEnter }: { onEnter: (session: WorkspaceSession) => void }) {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState<UserRole>("student");
  const [username, setUsername] = useState(demoCredentials.student.username);
  const [password, setPassword] = useState(demoCredentials.student.password);

  const chooseRole = (nextRole: UserRole) => {
    setRole(nextRole);
    setUsername(demoCredentials[nextRole].username);
    setPassword(demoCredentials[nextRole].password);
    setError("");
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanUsername = username.trim();
    const cleanPassword = password.trim();
    if (!cleanUsername || !cleanPassword) {
      setError("Login va parolni kiriting.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      if (hasLiveApi()) {
        onEnter(await loginWorkspace(cleanUsername, cleanPassword));
      } else {
        if (!hasDemoMode()) throw new Error("API manzili sozlanmagan. Demo rejimi productionda o‘chirilgan.");
        onEnter(createDemoWorkspace(role));
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Kirishda xatolik yuz berdi.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-screen">
      <div className="login-orb orb-one" />
      <div className="login-orb orb-two" />
      <section className="login-wrap">
        <RbisBrand />
        <div className="login-card">
          <div className="secure-badge"><ShieldCheck size={15} /> Himoyalangan platforma</div>
          <h1>Kabinetga kirish</h1>
          <p>Rolingizni tanlang — tizim sizga kerakli ish maydonini avtomatik ochadi.</p>
          <div className="role-login-grid" aria-label="Rolni tanlang">{roleOptions.map((option) => { const Icon = option.icon; return <button type="button" key={option.id} className={role === option.id ? "active" : ""} onClick={() => chooseRole(option.id)}><span><Icon size={18} /></span><strong>{option.label}</strong><small>{option.description}</small>{role === option.id && <Check size={14} />}</button>; })}</div>
          <form onSubmit={submit}>
            <label>Login yoki kirish kodi<input name="code" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" /></label>
            <label>Parol<div className="password-field"><input name="password" type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" /><button type="button" onClick={() => setShowPassword(!showPassword)} aria-label="Parolni ko‘rsatish">{showPassword ? <EyeOff size={19} /> : <Eye size={19} />}</button></div></label>
            {error && <div className="form-error"><CircleHelp size={16} /> {error}</div>}
            <button className="login-button" type="submit" disabled={loading}><LockKeyhole size={17} /> {loading ? "Kabinet yuklanmoqda..." : `${demoCredentials[role].label} kabinetiga kirish`} <ArrowRight size={18} /></button>
          </form>
          {hasDemoMode() && <div className="demo-hint"><Sparkles size={16} /><span><strong>Mahalliy demo rejimi:</strong> test login bilan rol kabinetini ochishingiz mumkin.</span></div>}
        </div>
        <span className="login-foot">Prezident maktabiga tayyorgarlik · Demo 2026</span>
      </section>
    </main>
  );
}

function CircularScore({ value, color, size = 160 }: { value: number; color: string; size?: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const dash = (value / 100) * circumference;
  return (
    <div className="circular-score" style={{ width: size, height: size }}>
      <svg viewBox="0 0 132 132" aria-label={`${value} foiz`}>
        <circle cx="66" cy="66" r={radius} className="score-track" />
        <circle cx="66" cy="66" r={radius} className="score-value" style={{ stroke: color, strokeDasharray: `${dash} ${circumference}` }} />
      </svg>
      <div><strong style={{ color }}>{value}%</strong><span>{value}/100 to‘g‘ri</span></div>
    </div>
  );
}

function LevelBand({ score = 41 }: { score?: number }) {
  return (
    <div className="level-band-wrap">
      <div className="level-pointer" style={{ left: `${score}%` }}><span>{score}</span><i /></div>
      <div className="level-band">{levels.map((level) => <div key={level.label} style={{ background: level.color, width: `${level.max - level.min}%` }} />)}</div>
      <div className="level-ticks">{levels.map((level, index) => <div key={level.label} style={{ width: `${level.max - level.min}%` }}><span>{index === 0 ? 0 : level.min}</span><strong style={{ color: level.color }}>{level.label}</strong></div>)}<span className="last-tick">100</span></div>
    </div>
  );
}

function SubjectCard({ subject, onOpen }: { subject: Subject; onOpen: () => void }) {
  const Icon = subject.icon;
  const level = levels.find((item) => subject.score >= item.min && subject.score < item.max) ?? levels[4];
  return (
    <article className="subject-card" style={{ borderTopColor: subject.accent }}>
      <div className="subject-card-head"><span>Fan 0{subjects.findIndex((item) => item.id === subject.id) + 1}</span><div className="level-pill" style={{ color: level.color, background: `${level.color}12`, borderColor: `${level.color}38` }}>{level.label}</div></div>
      <div className="subject-title"><Icon size={21} style={{ color: subject.accent }} /><h3>{subject.title}</h3></div>
      <CircularScore value={subject.score} color={subject.accent} size={150} />
      <dl className="subject-facts"><div><dt>Salohiyat</dt><dd>{subject.potential}</dd></div><div><dt>Kuchli</dt><dd className="good-text">{subject.strong.join(", ")}</dd></div><div><dt>Zaif</dt><dd className="weak-text">{subject.weak.slice(0, 2).join(", ")}</dd></div></dl>
      <button className="text-link" onClick={onOpen}>To‘liq hisobot <ArrowRight size={16} /></button>
    </article>
  );
}

function Overview({
  onSelect,
  subjectList,
  liveReport,
  miniExamResult = null,
}: {
  onSelect: (id: SubjectId) => void;
  subjectList: Subject[];
  liveReport: LiveDiagnosticReport | null;
  miniExamResult?: MiniExamResult | null;
}) {
  const miniResult = miniExamResult ? hydrateMiniExamResult(miniExamResult) : null;
  const overallScore = miniResult
    ? miniResult.score
    : liveReport
      ? Math.round(Number(liveReport.overall_score))
      : 41;
  const candidateName = miniResult?.candidate ?? liveReport?.student.full_name ?? "Bobur Xasanboyev";
  const candidateGrade = miniResult?.grade ?? "8-sinfga nomzod";
  const readiness = miniResult ? (miniResult.passed ? "ready" : "not_ready") : (liveReport?.readiness ?? "not_ready");
  const correctAnswers = miniResult?.correctAnswers ?? Math.round(overallScore / 10);
  const createdAt = miniResult?.createdAt ?? "18-iyul · 14:10";
  const bestSubject = [...subjectList].sort((a, b) => b.score - a.score)[0];
  const weakestSubject = [...subjectList].sort((a, b) => a.score - b.score)[0];
  const englishOnly = Boolean(
    liveReport
    && subjectList.length === 1
    && subjectList[0]?.id === "english",
  );
  const levelText = overallScore < 35 ? "sayoz" : overallScore < 50 ? "zaif" : overallScore < 67 ? "o‘rtacha" : overallScore < 84 ? "yaxshi" : "juda yaxshi";
  const scoreRangeLow = miniResult ? Math.max(overallScore - 3, 0) : liveReport ? Math.round(Number(liveReport.range_low)) : 38;
  const scoreRangeHigh = miniResult ? Math.min(overallScore + 3, 100) : liveReport ? Math.round(Number(liveReport.range_high)) : 44;
  const expectedScore = miniResult ? overallScore : liveReport ? Math.round(Number(liveReport.expected_score)) : 42;

  const subjectWeight = (subject: Subject) => {
    if (englishOnly) return 100;
    if (!miniResult) return subject.id === "critical" ? 30 : 35;
    return subject.id === "math" ? 40 : 30;
  };

  return (
    <>
      <section className="report-hero" id="report-top">
        <div className="hero-art hero-art-one">S</div><div className="hero-art hero-art-two">1</div>
        <div className="report-hero-content">
          <div className="hero-brand"><RbisBrand inverse /><span /> <em>Biz ilmga sodiqmiz</em></div>
          <span className="hero-kicker">{miniResult ? "Administrator o‘tkazgan qabul mini-imtihoni" : englishOnly ? "English placement diagnostikasi" : "Prezident maktabiga kirish diagnostikasi"}</span>
          <h1>Umumiy diagnostik<br />xulosa</h1>
          <p>{englishOnly ? "English darajasi, mavzular va ko‘nikmalar — bir qarashda." : "IQ, matematika va ingliz tili — bir qarashda."}</p>
          <div className="candidate-meta">
            <span><small>Nomzod</small>{candidateName}</span>
            <span><small>Sinf</small>{candidateGrade}</span>
            <span><small>Imtihon</small>{miniResult ? "3 fan · jami 10 savol" : englishOnly ? "English · 100 ball" : "3 fan · har biri 100 ball"}</span>
          </div>
          <div className="hero-score-card">
            <div className="hero-score"><strong>{overallScore}</strong><span>/100</span><em>{miniResult ? "10 savollik mini-imtihon" : englishOnly ? "English natijasi" : "3 fan o‘rtachasi"}</em></div>
            <div className="hero-subject-scores">{subjectList.map((subject) => <span key={subject.id}><strong>{subject.score}</strong>{subject.title}</span>)}</div>
            <div className="hero-mini-facts">
              {miniResult ? (
                <>
                  <span><strong>{correctAnswers}/10</strong>to‘g‘ri javob</span>
                  <span><strong>60 ball</strong>o‘tish chegarasi</span>
                  <span><strong>3 fan</strong>umumiy tahlil</span>
                </>
              ) : (
                <>
                  <span><strong>{liveReport?.answer_summary ? `${liveReport.answer_summary.correct}/${liveReport.answer_summary.total}` : "—"}</strong>to‘g‘ri javob</span>
                  <span><strong>{liveReport?.subject_results[0]?.level ?? "—"}</strong>English daraja</span>
                  <span><strong>{subjectList.length}</strong>faol fan</span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className={`readiness-card ${readiness === "ready" ? "ready" : ""}`}>
          <CheckCircle2 size={38} />
          <strong>{readiness === "ready" ? "Tayyor" : "Tayyor emas"}</strong>
          <span>{readiness === "ready" ? <>Umumiy natija<br />o‘tish chegarasidan yuqori</> : <>Umumiy natija<br />o‘tish chegarasidan past</>}</span>
        </div>
      </section>

      <section className="section-block glance-section">
        <div className="section-number">01</div><h2>Bir qarashda</h2>
        <p>
          {candidateName} kirish imtihonida <strong>{overallScore}/100</strong> ball oldi — {levelText} daraja.
          Eng yaxshi yo‘nalish {bestSubject.title.toLowerCase()}, eng katta o‘sish imkoniyati esa {weakestSubject.title.toLowerCase()} fanida.
        </p>
        <div className="insight-strip">
          <Lightbulb size={20} />
          <span><strong>Asosiy xulosa:</strong> {weakestSubject.title} bo‘yicha poydevor kuchaytirilsa, umumiy natijaga eng katta ta’sir beradi.</span>
          <button onClick={() => onSelect(weakestSubject.id)}>{weakestSubject.title} tahlili <ArrowRight size={15} /></button>
        </div>
      </section>

      <section className="section-block level-section">
        <div className="section-heading">
          <div><div className="section-number">02</div><h2>Umumiy daraja</h2><p>Natija {levelText} toifada, keyingi o‘sish uchun fanlar kesimidagi yo‘nalishlar ko‘rsatildi.</p></div>
          <div className="report-stamp"><FileCheck2 size={20} /><span>Hisobot yaratildi<strong>{createdAt}</strong></span></div>
        </div>
        <div className="level-metrics">
          <div><span>Umumiy ball</span><strong className="gold-text">{overallScore}<small>/100</small></strong><em>{miniResult ? "10 ta savol natijasi" : englishOnly ? "English testi natijasi" : "Uch fan o‘rtachasi"}</em></div>
          <div><span>Taxminiy oraliq</span><strong>{scoreRangeLow}–{scoreRangeHigh}</strong><em>Hisoblashdagi aniqlik</em></div>
          <div><span>Kutilayotgan ball</span><strong className="gold-text">~{expectedScore}</strong><em>Bir xil sharoit saqlansa</em></div>
        </div>
        <LevelBand score={overallScore} />
        <div className="formula-block">
          <div>
            <h3>Umumiy ball qanday hisoblandi?</h3>
            <p>{miniResult ? "10 savollik mini-imtihondagi fanlar ulushi" : englishOnly ? "English testi 100% og‘irlik bilan hisoblanadi" : "8-sinf imtihoni uchun tasdiqlangan fanlar og‘irligi"}</p>
          </div>
          <div className="formula-table">
            {subjectList.map((subject) => {
              const weight = subjectWeight(subject);
              return (
                <div key={subject.id}>
                  <span>{subject.title}</span>
                  <strong>{subject.score}/100</strong>
                  <em>× {weight}%</em>
                  <b>= {(subject.score * (weight / 100)).toFixed(1)}</b>
                </div>
              );
            })}
            <div className="formula-total"><span>Umumiy ball</span><strong>{overallScore}/100</strong></div>
          </div>
          <p className="formula-note">
            {miniResult
              ? "Formula: Matematika 4 savol (40%) + Ingliz tili 3 savol (30%) + IQ 3 savol (30%)."
              : englishOnly
                ? "Formula: English natijasi × 100%."
                : "Formula: Matematika × 35% + Ingliz tili × 35% + IQ × 30%."}
          </p>
        </div>
      </section>

      <section className="section-block subjects-section">
        <div className="section-number">03</div><h2>{englishOnly ? "English natijasi" : "Uch fan bo‘yicha"}</h2><p>{englishOnly ? "Daraja, ball va asosiy o‘sish yo‘nalishlari." : "Har bir fan — ball, salohiyat va asosiy o‘sish yo‘nalishlari bilan."}</p>
        <div className="subject-grid">{subjectList.map((subject) => <SubjectCard key={subject.id} subject={subject} onOpen={() => onSelect(subject.id)} />)}</div>
      </section>
    </>
  );
}

function SubjectHero({
  subject,
  candidateName = "Bobur Xasanboyev",
  grade = "8-sinfga nomzod",
}: {
  subject: Subject;
  candidateName?: string;
  grade?: string;
}) {
  const level = levels.find((item) => subject.score >= item.min && subject.score < item.max) ?? levels[4];
  return (
    <section className="subject-hero" style={{ "--subject-accent": subject.accent, "--subject-pale": subject.pale } as React.CSSProperties}>
      <div className="subject-hero-content">
        <span className="hero-kicker">Fan diagnostikasi · {subject.questions.length} ta savol</span>
        <h1>{subject.title} imtihoni<br />diagnostikasi</h1>
        <p>Natija savol, mavzu va asosiy ko‘nikmalar kesimida tahlil qilindi.</p>
        <div className="candidate-meta dark">
          <span><small>Nomzod</small>{candidateName}</span>
          <span><small>Sinf</small>{grade}</span>
          <span><small>Natija</small>{subject.score}/100 · {level.label}</span>
        </div>
      </div>
      <div className="subject-hero-score">
        <span>Fan natijasi</span><strong>{subject.score}<small>/100</small></strong><em>{level.label} daraja</em>
        <div className="mini-scale"><i style={{ width: `${subject.score}%`, background: subject.accent }} /></div>
        <div><span>0</span><span>35</span><span>50</span><span>67</span><span>84</span><span>100</span></div>
      </div>
    </section>
  );
}

function QuestionTable({ subject }: { subject: Subject }) {
  const [filter, setFilter] = useState<"all" | QuestionStatus>("all");
  const [query, setQuery] = useState("");
  const visible = subject.questions.filter((question) => (filter === "all" || question.status === filter) && question.topic.toLowerCase().includes(query.toLowerCase()));
  const correct = subject.questions.filter((question) => question.status === "correct").length;
  return (
    <section className="section-block questions-section">
      <div className="section-heading"><div><div className="section-number">04</div><h2>Har bir savol</h2><p>Har bir javob qaysi mavzu va ko‘nikmani tekshirganini ko‘ring.</p></div><div className="question-stats"><span><CheckCircle2 size={17} /> {correct} to‘g‘ri</span><span><XCircle size={17} /> {subject.questions.length - correct} xato</span></div></div>
      <div className="table-tools"><div className="segmented"><button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>Barchasi</button><button className={filter === "correct" ? "active" : ""} onClick={() => setFilter("correct")}>To‘g‘ri</button><button className={filter === "wrong" ? "active" : ""} onClick={() => setFilter("wrong")}>Xato</button></div><label className="search-field"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Mavzu bo‘yicha izlash" /></label></div>
      <div className="question-table-wrap"><table className="question-table"><thead><tr><th>#</th><th>Natija</th><th>Kichik mavzu</th><th>Ko‘nikma</th><th>Daraja</th></tr></thead><tbody>{visible.map((question) => <tr key={question.code}><td><strong>{question.code}</strong></td><td>{question.status === "correct" ? <span className="status-icon correct"><Check size={17} /></span> : <span className="status-icon wrong"><X size={17} /></span>}</td><td>{question.topic}</td><td><span className="skill-chip">{question.skill}</span></td><td><span className={`difficulty ${question.difficulty === "Yuqori" ? "hard" : question.difficulty === "O‘rta" ? "medium" : "easy"}`}>{question.difficulty}</span></td></tr>)}</tbody></table>{visible.length === 0 && <div className="empty-state"><Search size={23} /> Mos mavzu topilmadi</div>}</div>
    </section>
  );
}

function RadarChart({ values, accent }: { values: number[]; accent: string }) {
  const centerX = 290;
  const centerY = 225;
  const radius = 145;
  const count = values.length;
  const point = (value: number, index: number, r = radius) => {
    const angle = -Math.PI / 2 + (index * Math.PI * 2) / count;
    const usedRadius = r * (value / 100);
    return [centerX + Math.cos(angle) * usedRadius, centerY + Math.sin(angle) * usedRadius];
  };
  const polygon = (value: number) => Array.from({ length: count }, (_, index) => point(value, index).join(",")).join(" ");
  const valuePolygon = values.map((value, index) => point(value, index).join(",")).join(" ");
  return (
    <svg className="radar-chart" viewBox="0 0 580 470" role="img" aria-label="Ko‘nikmalar radar xaritasi">
      {[20, 40, 60, 80, 100].map((value) => <polygon key={value} points={polygon(value)} className="radar-grid" />)}
      {values.map((_, index) => { const [x, y] = point(100, index); return <line key={index} x1={centerX} y1={centerY} x2={x} y2={y} className="radar-axis" />; })}
      <polygon points={valuePolygon} fill={`${accent}22`} stroke={accent} strokeWidth="3" />
      {values.map((value, index) => { const [x, y] = point(value, index); return <circle key={index} cx={x} cy={y} r="5" fill={accent} stroke="white" strokeWidth="2" />; })}
      {values.map((value, index) => { const [x, y] = point(112, index); const label = skillLabels[index]; const parts = label.split(" "); const split = parts.length > 2 ? Math.ceil(parts.length / 2) : parts.length; return <text key={label} x={x} y={y - 7} textAnchor={x < centerX - 12 ? "end" : x > centerX + 12 ? "start" : "middle"} className="radar-label"><tspan x={x}>{parts.slice(0, split).join(" ")}</tspan>{parts.length > split && <tspan x={x} dy="16">{parts.slice(split).join(" ")}</tspan>}<tspan x={x} dy="18" className="radar-value">{value}%</tspan></text>; })}
    </svg>
  );
}

function SkillsProfile({ subject }: { subject: Subject }) {
  return (
    <section className="section-block skills-section">
      <div className="section-number">05</div><h2>Ko‘nikmalar profili <span className="info-dot">i</span></h2><p>Yetti asosiy ko‘nikma bo‘yicha kuch-quvvat xaritasi.</p>
      <div className="skills-layout"><div className="radar-panel"><RadarChart values={subject.skills} accent={subject.accent} /><p>Shakl qanchalik tekis bo‘lsa, ko‘nikmalar shunchalik muvozanatli. Bir tomonga cho‘zilgan bo‘lsa — o‘sha ko‘nikma ustun.</p></div><aside className="skills-aside"><div className="skill-summary good"><span><TrendingUp size={18} /> Kuchli yo‘nalish</span><strong>{subject.strong[0]}</strong><p>Ushbu yo‘nalish keyingi bosqich uchun tayanch bo‘la oladi.</p></div><div className="skill-summary weak"><span><Target size={18} /> Eng katta bo‘shliq</span><strong>{subject.weak[0]}</strong><p>Roadmapning birinchi bosqichi aynan shu ko‘nikmaga qaratiladi.</p></div><div className="confidence-note"><ShieldCheck size={18} /><span><strong>Ishonchlilik: o‘rta</strong>Natija {subject.questions.length} ta savolga asoslangan.</span></div></aside></div>
    </section>
  );
}

function GrowthChart({ subject }: { subject: Subject }) {
  const start = subject.score;
  const values = [start, Math.min(start + 14, 100), Math.min(start + 31, 100), Math.min(start + 49, 100)];
  return (
    <section className="section-block growth-section">
      <div className="section-number">06</div><h2>O‘sish imkoniyati</h2><p>Reja muntazam bajarilsa, 3–12 oy ichida kutilayotgan o‘sish.</p>
      <div className="growth-card"><div className="growth-legend"><span><i className="now" /> Hozir</span><span><i className="m3" /> 3 oy</span><span><i className="m6" /> 6 oy</span><span><i className="m12" /> 12 oy</span></div><div className="growth-rows">{["Umumiy ball", subject.focus, subject.nextFocus, "Aralash sinov"].map((label, row) => <div className="growth-row" key={label}><strong>{label}</strong><div className="growth-track"><span className="growth-dot initial" style={{ left: `${Math.max(values[0] - row * 3, 2)}%` }}>{Math.max(values[0] - row * 3, 0)}</span><i className="growth-line l1" style={{ left: `${Math.max(values[0] - row * 3, 2)}%`, width: `${values[1] - values[0] + row * 2}%` }} /><i className="growth-line l2" style={{ left: `${values[1]}%`, width: `${values[2] - values[1]}%` }} /><i className="growth-line l3" style={{ left: `${values[2]}%`, width: `${values[3] - values[2]}%` }} /><span className="growth-dot final" style={{ left: `${Math.min(values[3] + row, 96)}%` }}>{Math.min(values[3] + row, 100)}</span></div></div>)}</div><div className="projection-note"><Sparkles size={18} /><p><strong>Bu kafolat emas, yo‘nalish.</strong> Prognoz haftalik yuklama, mavzu murakkabligi va qayta diagnostika natijalariga qarab yangilanadi.</p></div></div>
    </section>
  );
}

function Roadmap({ subject }: { subject: Subject }) {
  const [activeStage, setActiveStage] = useState(0);
  const plan = roadmapCopy[subject.id];
  const active = plan.stages[activeStage];
  return (
    <section className="roadmap-section" id="roadmap">
      <div className="roadmap-intro"><div className="section-number">07</div><h2>Shaxsiy o‘sish yo‘li</h2><p>Maqsad sari uch bosqichli yo‘l — har biri oldingisining davomi.</p></div>
      <div className="roadmap-map">
        <div className="roadmap-now">Hozir · {subject.score} ball</div>
        <svg viewBox="0 0 820 780" preserveAspectRatio="none" aria-hidden="true"><path d="M410 30 C330 120 180 150 210 260 C240 370 660 350 620 470 C580 590 250 560 300 690 C320 735 390 740 410 755" className="road-shadow" /><path d="M410 30 C330 120 180 150 210 260 C240 370 660 350 620 470 C580 590 250 560 300 690 C320 735 390 740 410 755" className="road-dash" /></svg>
        {plan.stages.map((stage, index) => <button key={stage.title} className={`road-stage stage-${index + 1} ${activeStage === index ? "active" : ""}`} onClick={() => setActiveStage(index)}><span className="stage-node">{index + 1}</span><div><small>{stage.period}</small><strong>{stage.title}</strong><span><b>{stage.from}</b> → <b>{stage.to}</b> ball</span><em>{stage.hours}</em></div></button>)}
        <div className="road-goal"><Check size={20} /><strong>Maqsad</strong><span>85+ ball</span></div>
      </div>
      <div className="stage-selector">{plan.stages.map((stage, index) => <button key={stage.period} className={activeStage === index ? "active" : ""} onClick={() => setActiveStage(index)}><span>{index + 1}</span><strong>{index + 1}-bosqich</strong><em>{stage.period}</em></button>)}</div>

      <div className="stage-detail">
        <div className="stage-detail-head"><span className="stage-seal">{activeStage + 1}</span><div><small>{activeStage + 1}-bosqich · {active.period}</small><h3>{activeStage + 1}-bosqich · poydevor: {active.title}</h3><p>Eng katta bilim bo‘shlig‘ini yopib, keyingi mavzular uchun mustahkam poydevor quramiz.</p></div><div className="stage-effort"><span>Haftalik yuklama</span><strong>{active.hours}</strong><em>{active.from} → {active.to} ball</em></div></div>
        <div className="focus-reason"><h4>Nima uchun bu diqqat markazida?</h4><div><strong>{active.title}</strong><p>Diagnostikada bu yo‘nalish {Math.max(subject.score - 15, 0)}/100 — sog‘lom 75 dan past; imtihonda bir nechta savol shu bilim bilan bog‘liq holda o‘tkazib yuborilgan.</p></div><div><strong>{subject.weak[0]}</strong><p>Bu ko‘nikma keyingi murakkab mavzularning prerequisite’i. Avval poydevorni tiklash eng katta o‘sishni beradi.</p></div></div>
        <details className="detail-accordion"><summary><span>Bu bosqichda nima qilamiz</span><ChevronDown size={19} /></summary><div className="accordion-body"><div><CheckCircle2 size={18} /><span>Asosiy tushunchani qisqa video va misollar orqali o‘rganish</span></div><div><CheckCircle2 size={18} /><span>Boshlang‘ichdan murakkabgacha adaptiv mashqlar</span></div><div><CheckCircle2 size={18} /><span>Xato daftari va har ikki haftada mini-diagnostika</span></div></div></details>
        <details className="detail-accordion" open><summary><span>Haftama-hafta reja</span><ChevronDown size={19} /></summary><div className="week-list">{plan.weeks.map((week, index) => <div className="week-row" key={`${week.title}-${index}`}><span>{index + 1}-hafta</span><div><strong>{week.title}</strong><p>{week.task}</p></div><button aria-label={`${index + 1}-hafta tafsiloti`}><ChevronRight size={18} /></button></div>)}</div></details>
        <div className="stakeholder-grid"><div><span className="role-icon parent"><UsersRound size={19} /></span><h4>Ota-ona</h4><p>Kunlik 20–30 daqiqa mashqni kalendarga kiriting va haftasiga bir marta xato daftarini ko‘rib chiqing.</p></div><div><span className="role-icon teacher"><BookOpenCheck size={19} /></span><h4>O‘qituvchi</h4><p>Darsda fokus mavzuga 10 daqiqa ajrating va har ikki haftada mini-diagnostika o‘tkazing.</p></div><div><span className="role-icon student"><UserRound size={19} /></span><h4>O‘quvchi</h4><p>Haftalik vazifalarni muddatida bajaring, xatolarni belgilang va mini-testni kamida 75% bilan yoping.</p></div></div>
        <div className="stage-result"><Target size={20} /><div><strong>Bosqich natijasi</strong><p>{active.title} va unga bog‘liq ko‘nikmalar mustahkamlanadi; fan natijasi taxminan {active.to} ballga chiqadi.</p></div><span><ShieldCheck size={15} /> Ishonch: o‘rta</span></div>
      </div>
    </section>
  );
}

function SubjectReport({
  subject,
  candidateName,
  grade,
}: {
  subject: Subject;
  candidateName?: string;
  grade?: string;
}) {
  return (
    <>
      <SubjectHero subject={subject} candidateName={candidateName} grade={grade} />
      {subject.questions.length > 0 && <QuestionTable subject={subject} />}
      <SkillsProfile subject={subject} />
      <GrowthChart subject={subject} />
      <Roadmap subject={subject} />
    </>
  );
}

function ReportApp({
  onLogout,
  liveReport,
  session,
  exitLabel = "Chiqish",
  forcedMiniExamResult = null,
  resultOnly = false,
}: {
  onLogout: () => void;
  liveReport: LiveDiagnosticReport | null;
  session: WorkspaceSession;
  exitLabel?: string;
  forcedMiniExamResult?: MiniExamResult | null;
  resultOnly?: boolean;
}) {
  const [active, setActive] = useState<ReportTab>("overall");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [storedMiniExamResult, setStoredMiniExamResult] = useState<MiniExamResult | null>(null);
  const miniExamResult = useMemo(
    () => forcedMiniExamResult ? hydrateMiniExamResult(forcedMiniExamResult) : storedMiniExamResult,
    [forcedMiniExamResult, storedMiniExamResult],
  );

  useEffect(() => {
    if (forcedMiniExamResult) return;

    const loadMiniExamResult = () => {
      try {
        const saved = window.localStorage.getItem(MINI_EXAM_STUDENT_RESULTS_KEY)
          ?? window.localStorage.getItem(MINI_EXAM_STORAGE_KEY);
        const history = saved ? JSON.parse(saved) as MiniExamResult[] : [];
        const studentKey = normalizeCandidate(session.user.full_name);
        const matching = history.find((result) => (result.candidateKey ?? normalizeCandidate(result.candidate)) === studentKey) ?? null;
        setStoredMiniExamResult(matching ? hydrateMiniExamResult(matching) : null);
        if (matching && session.role === "student") setActive("overall");
      } catch {
        setStoredMiniExamResult(null);
      }
    };
    loadMiniExamResult();
    window.addEventListener("storage", loadMiniExamResult);
    window.addEventListener("bilimyol-mini-exam-result", loadMiniExamResult);
    return () => {
      window.removeEventListener("storage", loadMiniExamResult);
      window.removeEventListener("bilimyol-mini-exam-result", loadMiniExamResult);
    };
  }, [forcedMiniExamResult, session.role, session.user.full_name]);

  const displaySubjects = useMemo(() => {
    if (miniExamResult) return buildMiniExamSubjects(miniExamResult);

    if (!liveReport) return subjects;

    return liveReport.subject_results.map((live) => {
      const subjectId = live.subject.slug === "iq" ? "critical" : live.subject.slug;
      const template = subjects.find((subject) => subject.id === subjectId) ?? subjects[1];
      const skillRows = (liveReport.skill_results ?? [])
        .filter((item) => !live.subject.id || !item.skill?.subject || item.skill.subject === live.subject.id)
        .sort((a, b) => Number(b.score) - Number(a.score));
      const skillScores = skillRows.map((item) => Math.round(Number(item.score)));
      const paddedSkills = [...skillScores, ...Array(7).fill(Math.round(Number(live.score)))].slice(0, 7);
      return {
        ...template,
        score: Math.round(Number(live.score)),
        percentile: live.percentile,
        potential: live.potential,
        accent: rbisChartColor(live.subject.slug),
        strong: skillRows.length
          ? skillRows.slice(0, 2).map((item) => item.skill?.title ?? "English")
          : ["English natijasi"],
        weak: skillRows.length
          ? [...skillRows].reverse().slice(0, 2).map((item) => item.skill?.title ?? "English")
          : ["English ko‘nikmalari"],
        skills: paddedSkills,
        questions: [],
      };
    });
  }, [liveReport, miniExamResult]);

  const activeSubject = useMemo(() => displaySubjects.find((subject) => subject.id === active), [active, displaySubjects]);
  const hideUniversity = resultOnly || Boolean(miniExamResult);
  const reportCandidateName = miniExamResult?.candidate ?? liveReport?.student.full_name ?? "Bobur Xasanboyev";
  const reportGrade = miniExamResult?.grade
    ?? (liveReport?.grade || liveReport?.exam?.grade ? `${liveReport?.grade ?? liveReport?.exam?.grade}-sinf` : "Sinf belgilanmagan");

  const selectTab = (id: ReportTab) => {
    setActive(id);
    setMobileOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <main className="report-app">
      <header className="report-header">
        <RbisBrand />
        <nav className={mobileOpen ? "open" : ""} aria-label="Hisobot bo‘limlari">
          <button className={active === "overall" ? "active" : ""} onClick={() => selectTab("overall")}>Umumiy</button>
          {displaySubjects.map((subject) => (
            <button key={subject.id} className={active === subject.id ? "active" : ""} onClick={() => selectTab(subject.id)}>
              {subject.title}
            </button>
          ))}
          {!hideUniversity && (
            <button className={active === "university" ? "active" : ""} onClick={() => selectTab("university")}>Dream University</button>
          )}
        </nav>
        <div className="header-actions">
          <button className="header-icon" onClick={() => window.print()} aria-label="Hisobotni chop etish"><Printer size={18} /></button>
          <button className="download-button" onClick={() => window.print()}><Download size={17} /> PDF yuklash</button>
          <button className="logout-button" onClick={onLogout}><LogOut size={17} /> {exitLabel}</button>
          <button className="menu-button" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Menyuni ochish">{mobileOpen ? <X size={22} /> : <Menu size={22} />}</button>
        </div>
      </header>

      {active === "overall" ? (
        <Overview
          onSelect={selectTab}
          subjectList={displaySubjects}
          liveReport={miniExamResult ? null : liveReport}
          miniExamResult={miniExamResult}
        />
      ) : active === "university" && !hideUniversity ? (
        <div className="report-university-wrap"><UniversityJourney session={session} title="Mening Dream University yo‘lim" /></div>
      ) : activeSubject ? (
        <SubjectReport subject={activeSubject} candidateName={reportCandidateName} grade={reportGrade} />
      ) : null}

      <footer className="report-footer"><RbisBrand inverse /><p>Har bir natijadan aniq o‘quv yo‘ligacha.</p><span>RBIS · 2026</span></footer>
    </main>
  );
}

export default function Home() {
  const [session, setSession] = useState<WorkspaceSession | null>(null);
  const [restoringSession, setRestoringSession] = useState(true);
  const [viewingReport, setViewingReport] = useState(false);
  const [adminDiagnosticReport, setAdminDiagnosticReport] = useState<LiveDiagnosticReport | null>(null);
  const [studentDiagnosticReport, setStudentDiagnosticReport] = useState<LiveDiagnosticReport | null>(null);

  useEffect(() => {
    let active = true;
    restoreWorkspaceSession()
      .then((restored) => {
        if (active && restored) setSession(restored);
      })
      .finally(() => {
        if (active) setRestoringSession(false);
      });
    return () => { active = false; };
  }, []);

  const logout = () => {
    clearApiSession();
    setSession(null);
    setViewingReport(false);
    setAdminDiagnosticReport(null);
    setStudentDiagnosticReport(null);
  };
  if (restoringSession) return <main className="session-restore-screen"><span className="session-restore-spinner" /><strong>Kabinet tiklanmoqda...</strong></main>;
  if (!session) return <Login onEnter={setSession} />;
  if (session.role === "student" && studentDiagnosticReport) {
    return <ReportApp onLogout={() => setStudentDiagnosticReport(null)} liveReport={studentDiagnosticReport} session={session} exitLabel="Kabinetga qaytish" resultOnly />;
  }
  if (session.role === "student") {
    return <StudentWorkspace session={session} onLogout={logout} onOpenReport={setStudentDiagnosticReport} />;
  }
  if (adminDiagnosticReport) return <ReportApp onLogout={() => setAdminDiagnosticReport(null)} liveReport={adminDiagnosticReport} session={session} exitLabel="Admin kabinetiga qaytish" resultOnly />;
  if (viewingReport) return <ReportApp onLogout={() => setViewingReport(false)} liveReport={session.report} session={session} exitLabel="Kabinetga qaytish" />;
  if (session.role === "parent") return <ParentWorkspace session={session} onLogout={logout} onOpenReport={() => setViewingReport(true)} />;
  if (session.role === "teacher") return <TeacherWorkspace session={session} onLogout={logout} onOpenReport={() => setViewingReport(true)} />;
  return <AdminWorkspace session={session} onLogout={logout} onOpenReport={() => setViewingReport(true)} onOpenExamResult={setAdminDiagnosticReport} />;
}
