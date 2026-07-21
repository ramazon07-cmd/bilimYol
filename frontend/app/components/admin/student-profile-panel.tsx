"use client";

import {
  CheckCircle2,
  ClipboardList,
  Clock3,
  Goal,
  Info,
  Phone,
  Tags,
  UserRound,
  UsersRound,
} from "lucide-react";
import { useState } from "react";

import type { StudentProfile } from "../../lib/profiling-api";

const statusLabels: Record<string, string> = {
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
  const [roadmapNotice, setRoadmapNotice] = useState(false);
  const interview = profile.interviews[0];
  const primaryGoal = profile.goals.find((item) => item.is_primary) ?? profile.goals[0];
  const guardian = profile.guardian_contacts[0];
  const isRoadmapDraft = profile.status === "roadmap_draft";

  return (
    <div className="student-profile-detail">
      <article className="portal-card student-profile-hero student-profile-hero-v5">
        <span className="student-profile-avatar"><UserRound size={34} /></span>

        <div className="student-profile-main">
          <div className="student-profile-kicker-row">
            <small>{profile.admission_code}</small>

            {isRoadmapDraft ? (
              <button
                type="button"
                className="student-profile-status status-roadmap_draft status-clickable"
                onClick={() => setRoadmapNotice(true)}
              >
                <i aria-hidden="true" /> Roadmap draft
              </button>
            ) : (
              <em className={`student-profile-status status-${profile.status}`}>
                <i aria-hidden="true" />
                {statusLabels[profile.status] ?? profile.status.replaceAll("_", " ")}
              </em>
            )}

            {onOpenTests && (
              <button type="button" className="student-profile-diagnostic-pill" onClick={onOpenTests}>
                <ClipboardList size={15} /> Diagnostika
              </button>
            )}
          </div>

          <h2>{profile.student.full_name}</h2>
          <p>{profile.school_name || "Maktab ko‘rsatilmagan"} · {profile.grade ?? "—"}-sinf</p>

          <div className="student-profile-meta">
            <span><Clock3 size={16} /> {profile.weekly_study_hours} soat/hafta</span>
            {profile.student.phone && <span><Phone size={16} /> {profile.student.phone}</span>}
          </div>
        </div>
      </article>

      {roadmapNotice && (
        <div className="roadmap-owner-notice" role="status">
          <Info size={19} />
          <div>
            <strong>Roadmap hali draft holatida</strong>
            <p>Roadmapni biriktirilgan ustoz ko‘rib chiqadi, kerakli o‘zgartirishlarni kiritadi va tasdiqlaydi.</p>
          </div>
          <button type="button" onClick={() => setRoadmapNotice(false)} aria-label="Xabarni yopish">×</button>
        </div>
      )}

      <div className="student-profile-info-grid">
        <article className="portal-card">
          <span><Goal size={21} /></span>
          <h3>Asosiy maqsad</h3>
          <strong>{primaryGoal?.title ?? "Kiritilmagan"}</strong>
          <p>{primaryGoal?.description || primaryGoal?.target_value || "—"}</p>
          {primaryGoal?.target_score != null && <b>Maqsad: {primaryGoal.target_score}/100</b>}
        </article>

        <article className="portal-card">
          <span><Tags size={21} /></span>
          <h3>Kategoriyalar</h3>
          <div className="profile-tag-list">
            {profile.category_links.length > 0
              ? profile.category_links.map((item) => <em key={item.id}>{item.category_detail.title}</em>)
              : <p>Kategoriya biriktirilmagan</p>}
          </div>
        </article>

        <article className="portal-card">
          <span><UsersRound size={21} /></span>
          <h3>Aloqa</h3>
          <strong>{guardian?.full_name ?? "Kiritilmagan"}</strong>
          <p>{guardian?.relationship ?? "Ota-ona"}</p>
          {guardian?.phone && <b>{guardian.phone}</b>}
        </article>
      </div>

      {interview && (
        <article className="portal-card interview-summary-card">
          <div className="interview-summary-title">
            <div>
              <span>Suhbat xulosasi</span>
              <h3>{interview.admin_summary || "Xulosa kiritilmagan"}</h3>
            </div>
            {interview.motivation_level && (
              <em><CheckCircle2 size={14} /> {interview.motivation_level}</em>
            )}
          </div>
          <div className="interview-summary-grid">
            <p><strong>Kuchli tomonlari</strong>{interview.strengths || "—"}</p>
            <p><strong>Zaif tomonlari</strong>{interview.weaknesses || "—"}</p>
            <p><strong>Asosiy muammo</strong>{interview.main_problem || "—"}</p>
            <p><strong>Keyingi qadam</strong>{interview.next_step || "—"}</p>
          </div>
        </article>
      )}
    </div>
  );
}
