"use client";

import { ArrowLeft, Search, UserRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getStudentProfiles, type StudentProfile } from "../../lib/profiling-api";
import { StudentProfilePanel } from "./student-profile-panel";

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

export function AdminStudentsPanel({
  selectedProfileId,
  onSelectProfile,
}: {
  selectedProfileId: number | null;
  onSelectProfile: (id: number | null) => void;
}) {
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getStudentProfiles("ordering=-created_at&page_size=100")
      .then((payload) => setProfiles(payload.results))
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  const selected = profiles.find((item) => item.id === selectedProfileId) ?? null;
  const filtered = useMemo(
    () =>
      profiles.filter((item) =>
        `${item.student.full_name} ${item.admission_code} ${item.school_name}`
          .toLowerCase()
          .includes(search.toLowerCase()),
      ),
    [profiles, search],
  );

  if (selected) {
    return (
      <div className="admin-detail-page">
        <button className="portal-back-button" onClick={() => onSelectProfile(null)}>
          <ArrowLeft size={18} /> O‘quvchilar ro‘yxatiga qaytish
        </button>
        <StudentProfilePanel profile={selected} />
      </div>
    );
  }

  return (
    <div className="admin-students-page">
      <div className="admin-page-heading">
        <div>
          <span>O‘quvchilar</span>
          <h1>Individual profillar</h1>
          <p>Har bir o‘quvchining maqsadi, sinfi va profiling statusini bir joydan boshqaring.</p>
        </div>
        <label className="mini-search admin-list-search">
          <Search size={17} />
          <input
            placeholder="Ism, kod yoki maktab"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
      </div>

      {error && <div className="admin-flow-message error">{error}</div>}

      <article className="portal-card students-directory-card">
        <div className="students-directory-head">
          <div>
            <strong>{filtered.length} ta profil</strong>
            <span>API orqali yuklangan o‘quvchilar</span>
          </div>
        </div>
        <div className="portal-table-wrap">
          <table className="portal-table admin-students-table">
            <thead>
              <tr>
                <th>O‘quvchi</th>
                <th>Qabul kodi</th>
                <th>Sinf</th>
                <th>Asosiy maqsad</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((profile) => (
                <tr
                  key={profile.id}
                  onClick={() => onSelectProfile(profile.id)}
                  className="clickable-row"
                >
                  <td>
                    <div className="student-table-person">
                      <span><UserRound size={20} /></span>
                      <div>
                        <strong>{profile.student.full_name}</strong>
                        <small>{profile.school_name || "Maktab kiritilmagan"}</small>
                      </div>
                    </div>
                  </td>
                  <td><strong>{profile.admission_code}</strong></td>
                  <td><span className="grade-badge">{profile.grade ?? "—"}-sinf</span></td>
                  <td>{profile.goals.find((goal) => goal.is_primary)?.title ?? "—"}</td>
                  <td><em className="table-status watch">{statusLabel[profile.status] ?? profile.status}</em></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </div>
  );
}
