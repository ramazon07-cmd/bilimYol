"use client";

import { ClipboardList, Clock3, Goal, Phone, Tags, UserRound, UsersRound } from "lucide-react";
import type { StudentProfile } from "../../lib/profiling-api";

const statusLabel: Record<string, string> = {
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

export function StudentProfilePanel({
  profile,
  onOpenTests,
}: {
  profile: StudentProfile;
  onOpenTests?: () => void;
}) {
  const interview = profile.interviews[0];
  const primaryGoal = profile.goals.find((item) => item.is_primary) ?? profile.goals[0];
  const guardian = profile.guardian_contacts[0];

  return (
    <div className="student-profile-detail">
      <article className="portal-card student-profile-hero">
        <span className="student-profile-avatar"><UserRound size={31} /></span>
        <div className="student-profile-main-copy">
          <small>{profile.admission_code}</small>
          <h2>{profile.student.full_name}</h2>
          <p>{profile.school_name || "Maktab ko‘rsatilmagan"} · {profile.grade ?? "—"}-sinf</p>
          <div className="student-profile-meta-row">
            <span><Clock3 size={15} /> {profile.weekly_study_hours} soat/hafta</span>
            {profile.student.phone && <span><Phone size={15} /> {profile.student.phone}</span>}
          </div>
        </div>
        <div className="student-profile-actions">
          <em>{statusLabel[profile.status] ?? profile.status}</em>
          {onOpenTests && (
            <button className="portal-primary" onClick={onOpenTests}>
              <ClipboardList size={18} /> Diagnostikaga o‘tish
            </button>
          )}
        </div>
      </article>

      <div className="student-profile-info-grid">
        <article className="portal-card profile-info-card">
          <span><Goal size={21} /></span>
          <small>Asosiy maqsad</small>
          <h3>{primaryGoal?.title ?? "Kiritilmagan"}</h3>
          <p>{primaryGoal?.description || primaryGoal?.target_value || "Maqsad izohi kiritilmagan."}</p>
          {primaryGoal?.target_score != null && <strong>Maqsad: {primaryGoal.target_score}/100</strong>}
        </article>

        <article className="portal-card profile-info-card">
          <span><Tags size={21} /></span>
          <small>Profiling</small>
          <h3>Kategoriyalar</h3>
          <div className="profile-tag-list">
            {profile.category_links.length > 0
              ? profile.category_links.map((item) => <em key={item.id}>{item.category_detail.title}</em>)
              : <p>Kategoriya biriktirilmagan.</p>}
          </div>
        </article>

        <article className="portal-card profile-info-card">
          <span><UsersRound size={21} /></span>
          <small>Aloqa</small>
          <h3>{guardian?.full_name ?? "Ota-ona kiritilmagan"}</h3>
          <p>{guardian?.relationship ?? "—"}</p>
          <strong>{guardian?.phone ?? "Telefon kiritilmagan"}</strong>
        </article>
      </div>

      {interview && (
        <article className="portal-card interview-summary-card">
          <div className="interview-summary-head">
            <div><span>Suhbat xulosasi</span><h3>{interview.admin_summary || "Xulosa kiritilmagan"}</h3></div>
            <MessageSummaryStatus motivation={interview.motivation_level} />
          </div>
          <div className="interview-summary-grid">
            <div><small>Kuchli tomonlari</small><p>{interview.strengths || "—"}</p></div>
            <div><small>Zaif tomonlari</small><p>{interview.weaknesses || "—"}</p></div>
            <div><small>Asosiy muammo</small><p>{interview.main_problem || "—"}</p></div>
            <div><small>Keyingi qadam</small><p>{interview.next_step || "—"}</p></div>
          </div>
        </article>
      )}
    </div>
  );
}

function MessageSummaryStatus({ motivation }: { motivation?: string }) {
  const label = motivation === "high" ? "Yuqori motivatsiya" : motivation === "low" ? "Past motivatsiya" : "O‘rta motivatsiya";
  return <em className="interview-motivation">{label}</em>;
}
