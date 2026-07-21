"use client";

import { School } from "lucide-react";
import { useEffect, useState } from "react";
import { apiRequest, type PaginatedResponse } from "../../lib/api";

type Classroom = { id: number; name: string; grade: number; program: string; teacher_detail?: { full_name: string } | null; students?: { id: number }[] };

export function AdminClassesPanel() {
  const [classes, setClasses] = useState<Classroom[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { apiRequest<PaginatedResponse<Classroom>>("/classrooms/?page_size=100").then((payload) => setClasses(payload.results)).catch((requestError: Error) => setError(requestError.message)); }, []);
  return <div><div className="admin-page-heading"><div><span>Sinflar</span><h1>Real dars guruhlari</h1><p>Sinf profiling emas — u faqat o‘quvchining real dars guruhini bildiradi.</p></div></div>{error && <div className="admin-flow-message error">{error}</div>}<div className="class-summary-grid">{classes.map((item) => <article className="portal-card class-api-card" key={item.id}><span><School size={21} /></span><div><strong>{item.name}</strong><small>{item.grade}-sinf · {item.program}</small><p>{item.teacher_detail?.full_name ?? "O‘qituvchi biriktirilmagan"}</p></div><em>{item.students?.length ?? 0}<small>o‘quvchi</small></em></article>)}</div>{classes.length === 0 && !error && <article className="portal-card admin-empty-state"><School size={28} /><h3>Sinflar topilmadi</h3><p>Swagger yoki Django admin orqali sinf yarating.</p></article>}</div>;
}
