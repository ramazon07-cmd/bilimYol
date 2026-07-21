"use client";

import { BookOpenCheck, GraduationCap, Search, ShieldCheck, UserRound, UsersRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiRequest, type PaginatedResponse } from "../../lib/api";

type UserRole = "student" | "parent" | "teacher" | "admin";

type AdminUser = {
  id: number;
  username: string;
  full_name: string;
  email?: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  date_joined?: string;
};

const roleLabels: Record<UserRole, string> = {
  student: "O‘quvchi",
  parent: "Ota-ona",
  teacher: "O‘qituvchi",
  admin: "Administrator",
};

export function AdminUsersPanel() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<PaginatedResponse<AdminUser> | AdminUser[]>("/users/?page_size=200&ordering=-date_joined")
      .then((payload) => setUsers(Array.isArray(payload) ? payload : payload.results ?? []))
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  const counts = useMemo(
    () => ({
      student: users.filter((user) => user.role === "student").length,
      parent: users.filter((user) => user.role === "parent").length,
      teacher: users.filter((user) => user.role === "teacher").length,
      admin: users.filter((user) => user.role === "admin").length,
    }),
    [users],
  );

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return users;
    return users.filter((user) =>
      `${user.full_name} ${user.username} ${user.email ?? ""} ${user.phone ?? ""}`
        .toLowerCase()
        .includes(term),
    );
  }, [search, users]);

  return (
    <div className="admin-users-page">
      <div className="admin-page-heading">
        <div>
          <span>Foydalanuvchilar</span>
          <h1>Rollar va kirishlar</h1>
          <p>Platformadagi akkauntlar, rollar va faollik holatini kuzating.</p>
        </div>
        <label className="mini-search admin-list-search">
          <Search size={17} />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Ism yoki login" />
        </label>
      </div>

      {error && <div className="admin-flow-message error">{error}</div>}

      <div className="portal-metrics-grid">
        <article className="portal-card admin-user-metric"><span><GraduationCap size={21} /></span><div><small>O‘quvchilar</small><strong>{counts.student}</strong><p>Faol profillar</p></div></article>
        <article className="portal-card admin-user-metric tone-gold"><span><UsersRound size={21} /></span><div><small>Ota-onalar</small><strong>{counts.parent}</strong><p>Bog‘langan akkauntlar</p></div></article>
        <article className="portal-card admin-user-metric tone-green"><span><BookOpenCheck size={21} /></span><div><small>O‘qituvchilar</small><strong>{counts.teacher}</strong><p>Ta’lim jamoasi</p></div></article>
        <article className="portal-card admin-user-metric tone-blue"><span><ShieldCheck size={21} /></span><div><small>Administratorlar</small><strong>{counts.admin}</strong><p>Boshqaruv huquqi</p></div></article>
      </div>

      <article className="portal-card admin-users-directory">
        <div className="students-directory-head">
          <div><strong>{filtered.length} ta akkaunt</strong><span>Platformadagi foydalanuvchilar</span></div>
        </div>
        <div className="portal-table-wrap">
          <table className="portal-table admin-users-table">
            <thead><tr><th>Foydalanuvchi</th><th>Login</th><th>Rol</th><th>Aloqa</th><th>Holat</th></tr></thead>
            <tbody>
              {filtered.map((user) => (
                <tr key={user.id}>
                  <td><div className="student-table-person"><span><UserRound size={19} /></span><div><strong>{user.full_name || user.username}</strong><small>{user.email || "Email kiritilmagan"}</small></div></div></td>
                  <td><strong>{user.username}</strong></td>
                  <td><span className={`user-role-chip role-${user.role}`}>{roleLabels[user.role]}</span></td>
                  <td>{user.phone || "—"}</td>
                  <td><em className={`table-status ${user.is_active ? "ready" : "risk"}`}>{user.is_active ? "Faol" : "O‘chirilgan"}</em></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </div>
  );
}
