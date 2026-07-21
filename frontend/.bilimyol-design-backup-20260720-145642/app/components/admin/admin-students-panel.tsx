"use client";

import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getStudentProfiles, type StudentProfile } from "../../lib/profiling-api";
import { StudentProfilePanel } from "./student-profile-panel";

export function AdminStudentsPanel({ selectedProfileId, onSelectProfile }: { selectedProfileId: number | null; onSelectProfile: (id: number | null) => void }) {
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { getStudentProfiles("ordering=-created_at&page_size=100").then((payload) => setProfiles(payload.results)).catch((requestError: Error) => setError(requestError.message)); }, []);
  const selected = profiles.find((item) => item.id === selectedProfileId) ?? null;
  const filtered = useMemo(() => profiles.filter((item) => `${item.student.full_name} ${item.admission_code} ${item.school_name}`.toLowerCase().includes(search.toLowerCase())), [profiles, search]);
  if (selected) return <><button className="portal-text-button" onClick={() => onSelectProfile(null)}>← O‘quvchilar ro‘yxatiga qaytish</button><StudentProfilePanel profile={selected} /></>;
  return <div><div className="admin-page-heading"><div><span>O‘quvchilar</span><h1>Individual profillar</h1><p>Suhbat, maqsad, kategoriyalar va status bo‘yicha yagona ro‘yxat.</p></div><label className="mini-search"><Search size={15} /><input placeholder="Qidirish" value={search} onChange={(e) => setSearch(e.target.value)} /></label></div>{error && <div className="admin-flow-message error">{error}</div>}<article className="portal-card"><div className="portal-table-wrap"><table className="portal-table"><thead><tr><th>O‘quvchi</th><th>Kod</th><th>Sinf</th><th>Maqsad</th><th>Status</th></tr></thead><tbody>{filtered.map((profile) => <tr key={profile.id} onClick={() => onSelectProfile(profile.id)} className="clickable-row"><td><strong>{profile.student.full_name}</strong><small>{profile.school_name}</small></td><td>{profile.admission_code}</td><td>{profile.grade ?? "—"}</td><td>{profile.goals.find((goal) => goal.is_primary)?.title ?? "—"}</td><td><em className="table-status watch">{profile.status.replaceAll("_", " ")}</em></td></tr>)}</tbody></table></div></article></div>;
}
