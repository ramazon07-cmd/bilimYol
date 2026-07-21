"use client";

import { Plus, Search, UserCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getStudentProfiles, type ProfileStatus, type StudentProfile } from "../../lib/profiling-api";
import { StudentOnboardingWizard } from "./student-onboarding-wizard";
import { StudentProfilePanel } from "./student-profile-panel";

const tabs: { id: "all" | ProfileStatus; label: string }[] = [
  { id: "all", label: "Barchasi" },
  { id: "new", label: "Yangi" },
  { id: "interview_draft", label: "Suhbat" },
  { id: "interview_completed", label: "Test kutilmoqda" },
  { id: "roadmap_draft", label: "Roadmap" },
  { id: "active", label: "Faol" },
];

export function AdminAdmissionsPanel({ selectedProfileId, onSelectProfile, onOpenTests }: { selectedProfileId: number | null; onSelectProfile: (id: number | null) => void; onOpenTests: () => void }) {
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]["id"]>("all");
  const [search, setSearch] = useState("");
  const [showWizard, setShowWizard] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getStudentProfiles("ordering=-created_at&page_size=100")
      .then((payload) => setProfiles(payload.results))
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  const filtered = useMemo(() => profiles.filter((profile) => {
    const tabMatch = activeTab === "all" || profile.status === activeTab;
    const term = search.trim().toLowerCase();
    const searchMatch = !term || profile.student.full_name.toLowerCase().includes(term) || profile.admission_code.toLowerCase().includes(term);
    return tabMatch && searchMatch;
  }), [profiles, activeTab, search]);
  const selected = profiles.find((item) => item.id === selectedProfileId) ?? null;

  if (selected) {
    return <><button className="portal-text-button" onClick={() => onSelectProfile(null)}>← Qabul ro‘yxatiga qaytish</button><StudentProfilePanel profile={selected} onOpenTests={onOpenTests} /></>;
  }

  return (
    <div className="admin-admissions-page">
      <div className="admin-page-heading"><div><span>Qabul va profiling</span><h1>O‘quvchi suhbatlari</h1><p>Admin ma’lumot, maqsad, suhbat xulosasi va kategoriyalarni kiritadi.</p></div><button className="portal-primary" onClick={() => setShowWizard(true)}><Plus size={17} /> Yangi o‘quvchi</button></div>
      {error && <div className="admin-flow-message error">{error}</div>}
      <div className="admission-toolbar portal-card"><div className="admission-tabs">{tabs.map((tab) => <button key={tab.id} className={activeTab === tab.id ? "active" : ""} onClick={() => setActiveTab(tab.id)}>{tab.label}</button>)}</div><label className="mini-search"><Search size={15} /><input placeholder="Ism yoki kod" value={search} onChange={(e) => setSearch(e.target.value)} /></label></div>
      <div className="admission-card-grid">{filtered.map((profile) => <button className="portal-card admission-student-card" key={profile.id} onClick={() => onSelectProfile(profile.id)}><span><UserCheck size={21} /></span><div><strong>{profile.student.full_name}</strong><small>{profile.admission_code} · {profile.grade ?? "—"}-sinf</small><p>{profile.goals.find((goal) => goal.is_primary)?.title ?? "Maqsad kiritilmagan"}</p></div><em>{profile.status.replaceAll("_", " ")}</em></button>)}</div>
      {filtered.length === 0 && <article className="portal-card admin-empty-state"><UserCheck size={28} /><h3>O‘quvchi topilmadi</h3><p>Filtrni o‘zgartiring yoki yangi o‘quvchi qo‘shing.</p></article>}
      {showWizard && <StudentOnboardingWizard onClose={() => setShowWizard(false)} onCreated={(profile) => { setProfiles((current) => [profile, ...current]); onSelectProfile(profile.id); }} />}
    </div>
  );
}
