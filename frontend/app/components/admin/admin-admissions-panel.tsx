"use client";

import { ArrowLeft, CalendarClock, Plus, Search, Target, UserCheck } from "lucide-react";
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

const statusLabels: Partial<Record<ProfileStatus, string>> = {
  new: "Yangi",
  interview_draft: "Suhbat jarayonida",
  interview_completed: "Test kutilmoqda",
  test_recommended: "Test tavsiya qilindi",
  test_assigned: "Test biriktirildi",
  diagnosed: "Diagnostika yakunlandi",
  roadmap_draft: "Roadmap draft",
  active: "Faol",
  paused: "To‘xtatilgan",
};

export function AdminAdmissionsPanel({
  selectedProfileId,
  onSelectProfile,
  onOpenTests,
}: {
  selectedProfileId: number | null;
  onSelectProfile: (id: number | null) => void;
  onOpenTests: () => void;
}) {
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

  const filtered = useMemo(
    () =>
      profiles.filter((profile) => {
        const tabMatch = activeTab === "all" || profile.status === activeTab;
        const term = search.trim().toLowerCase();
        const searchMatch =
          !term ||
          profile.student.full_name.toLowerCase().includes(term) ||
          profile.admission_code.toLowerCase().includes(term);
        return tabMatch && searchMatch;
      }),
    [profiles, activeTab, search],
  );

  const selected = profiles.find((item) => item.id === selectedProfileId) ?? null;

  if (selected) {
    return (
      <div className="admin-detail-page">
        <button className="portal-back-button" onClick={() => onSelectProfile(null)}>
          <ArrowLeft size={18} /> Qabul ro‘yxatiga qaytish
        </button>
        <StudentProfilePanel profile={selected} onOpenTests={onOpenTests} />
      </div>
    );
  }

  return (
    <div className="admin-admissions-page">
      <div className="admin-page-heading">
        <div>
          <span>Qabul va profiling</span>
          <h1>O‘quvchi suhbatlari</h1>
          <p>Qabul holatini kuzating, suhbatni yakunlang va keyingi bosqichga o‘tkazing.</p>
        </div>
        <button className="portal-primary" onClick={() => setShowWizard(true)}>
          <Plus size={18} /> Yangi o‘quvchi
        </button>
      </div>

      {error && <div className="admin-flow-message error">{error}</div>}

      <div className="admission-toolbar portal-card">
        <div className="admission-tabs">
          {tabs.map((tab) => (
            <button
              type="button"
              key={tab.id}
              className={activeTab === tab.id ? "active" : ""}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
              <span>
                {tab.id === "all"
                  ? profiles.length
                  : profiles.filter((profile) => profile.status === tab.id).length}
              </span>
            </button>
          ))}
        </div>
        <label className="mini-search admin-list-search">
          <Search size={17} />
          <input
            placeholder="Ism yoki qabul kodi"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
      </div>

      <div className="admission-card-grid">
        {filtered.map((profile) => {
          const primaryGoal = profile.goals.find((goal) => goal.is_primary) ?? profile.goals[0];
          return (
            <button
              type="button"
              className="portal-card admission-student-card"
              key={profile.id}
              onClick={() => onSelectProfile(profile.id)}
            >
              <div className="admission-card-top">
                <span className="admission-avatar"><UserCheck size={23} /></span>
                <div>
                  <strong>{profile.student.full_name}</strong>
                  <small>{profile.admission_code} · {profile.grade ?? "—"}-sinf</small>
                </div>
                <em data-status={profile.status}>{statusLabels[profile.status] ?? profile.status}</em>
              </div>
              <div className="admission-card-goal">
                <Target size={17} />
                <div>
                  <small>Asosiy maqsad</small>
                  <strong>{primaryGoal?.title ?? "Maqsad kiritilmagan"}</strong>
                </div>
              </div>
              <div className="admission-card-meta">
                <span><CalendarClock size={15} /> {profile.weekly_study_hours} soat/hafta</span>
                <span>{profile.school_name || "Maktab kiritilmagan"}</span>
              </div>
            </button>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <article className="portal-card admin-empty-state">
          <UserCheck size={30} />
          <h3>O‘quvchi topilmadi</h3>
          <p>Filtrni o‘zgartiring yoki yangi o‘quvchi qo‘shing.</p>
        </article>
      )}

      {showWizard && (
        <StudentOnboardingWizard
          onClose={() => setShowWizard(false)}
          onCreated={(profile) => {
            setProfiles((current) => [profile, ...current]);
            onSelectProfile(profile.id);
          }}
        />
      )}
    </div>
  );
}
