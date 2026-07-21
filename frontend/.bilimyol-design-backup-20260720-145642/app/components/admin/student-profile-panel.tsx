"use client";

import { ClipboardList, Goal, Tags, UserRound, UsersRound } from "lucide-react";
import type { StudentProfile } from "../../lib/profiling-api";

export function StudentProfilePanel({ profile, onOpenTests }: { profile: StudentProfile; onOpenTests?: () => void }) {
  const interview = profile.interviews[0];
  const primaryGoal = profile.goals.find((item) => item.is_primary) ?? profile.goals[0];
  return (
    <div className="student-profile-detail">
      <article className="portal-card student-profile-hero">
        <span><UserRound size={28} /></span>
        <div><small>{profile.admission_code}</small><h2>{profile.student.full_name}</h2><p>{profile.school_name || "Maktab ko‘rsatilmagan"} · {profile.grade ?? "—"}-sinf</p></div>
        <em>{profile.status.replaceAll("_", " ")}</em>
        {onOpenTests && <button className="portal-primary" onClick={onOpenTests}><ClipboardList size={16} /> Diagnostikaga o‘tish</button>}
      </article>
      <div className="student-profile-info-grid">
        <article className="portal-card"><span><Goal size={20} /></span><h3>Asosiy maqsad</h3><strong>{primaryGoal?.title ?? "Kiritilmagan"}</strong><p>{primaryGoal?.description || primaryGoal?.target_value || "—"}</p></article>
        <article className="portal-card"><span><Tags size={20} /></span><h3>Kategoriyalar</h3><div className="profile-tag-list">{profile.category_links.map((item) => <em key={item.id}>{item.category_detail.title}</em>)}</div></article>
        <article className="portal-card"><span><UsersRound size={20} /></span><h3>Ota-ona</h3><strong>{profile.guardian_contacts[0]?.full_name ?? "Kiritilmagan"}</strong><p>{profile.guardian_contacts[0]?.phone ?? "—"}</p></article>
      </div>
      {interview && <article className="portal-card interview-summary-card"><span>Suhbat xulosasi</span><h3>{interview.admin_summary || "Xulosa kiritilmagan"}</h3><div><p><strong>Kuchli:</strong> {interview.strengths || "—"}</p><p><strong>Zaif:</strong> {interview.weaknesses || "—"}</p><p><strong>Muammo:</strong> {interview.main_problem || "—"}</p><p><strong>Keyingi qadam:</strong> {interview.next_step || "—"}</p></div></article>}
    </div>
  );
}
