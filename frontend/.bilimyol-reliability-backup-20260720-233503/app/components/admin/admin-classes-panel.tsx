"use client";

import { BookOpenCheck, School, UserRound, UsersRound } from "lucide-react";
import { useEffect, useState } from "react";
import { apiRequest, type PaginatedResponse } from "../../lib/api";

type Classroom = {
  id: number;
  name: string;
  grade: number;
  program: string;
  teacher_detail?: { full_name: string } | null;
  students?: { id: number }[];
};

export function AdminClassesPanel() {
  const [classes, setClasses] = useState<Classroom[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<PaginatedResponse<Classroom>>("/classrooms/?page_size=100")
      .then((payload) => setClasses(payload.results))
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  return (
    <div className="admin-classes-page">
      <div className="admin-page-heading">
        <div>
          <span>Sinflar</span>
          <h1>Real dars guruhlari</h1>
          <p>Sinf profiling emas. Bu bo‘lim o‘quvchining haqiqiy dars guruhi va ustozini ko‘rsatadi.</p>
        </div>
      </div>

      {error && <div className="admin-flow-message error">{error}</div>}

      <div className="class-api-grid">
        {classes.map((item) => (
          <article className="portal-card class-api-card" key={item.id}>
            <div className="class-api-card-head">
              <span><School size={24} /></span>
              <div>
                <small>{item.grade}-sinf guruhi</small>
                <h2>{item.name}</h2>
              </div>
              <em>{item.students?.length ?? 0}</em>
            </div>
            <div className="class-api-program">
              <BookOpenCheck size={17} />
              <span>{item.program || "Dastur belgilanmagan"}</span>
            </div>
            <div className="class-api-footer">
              <span><UserRound size={17} /> {item.teacher_detail?.full_name ?? "O‘qituvchi biriktirilmagan"}</span>
              <span><UsersRound size={17} /> {item.students?.length ?? 0} o‘quvchi</span>
            </div>
          </article>
        ))}
      </div>

      {classes.length === 0 && !error && (
        <article className="portal-card admin-empty-state">
          <School size={30} />
          <h3>Sinflar topilmadi</h3>
          <p>Swagger yoki Django admin orqali sinf yarating.</p>
        </article>
      )}
    </div>
  );
}
