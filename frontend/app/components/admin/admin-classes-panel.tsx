"use client";

import { BookOpenCheck, LoaderCircle, RefreshCw, School, UserRound, UsersRound } from "lucide-react";
import { useEffect, useState } from "react";
import { apiRequest, type PaginatedResponse } from "../../lib/api";

type Classroom = {
  id: number;
  name: string;
  grade: number;
  program: string;
  is_active: boolean;
  student_count: number;
  teacher_detail?: { full_name: string } | null;
  enrollments?: { id: number; student: number }[];
};

export function AdminClassesPanel() {
  const [classes, setClasses] = useState<Classroom[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refreshClasses = async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<PaginatedResponse<Classroom> | Classroom[]>(
        "/classrooms/?page_size=100&ordering=grade,name",
      );
      setClasses(Array.isArray(payload) ? payload : payload.results ?? []);
    } catch (requestError) {
      setClasses([]);
      setError(requestError instanceof Error ? requestError.message : "Sinflarni yuklab bo‘lmadi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    apiRequest<PaginatedResponse<Classroom> | Classroom[]>("/classrooms/?page_size=100&ordering=grade,name")
      .then((payload) => {
        if (!active) return;
        setClasses(Array.isArray(payload) ? payload : payload.results ?? []);
        setError("");
      })
      .catch((requestError: Error) => {
        if (!active) return;
        setClasses([]);
        setError(requestError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="admin-classes-page">
      <div className="admin-page-heading">
        <div>
          <span>Sinflar</span>
          <h1>Real dars guruhlari</h1>
          <p>O‘quvchilarning amaldagi dars guruhi, ustoz va dastur ma’lumotlarini boshqaring.</p>
        </div>
        <button className="portal-secondary" type="button" onClick={refreshClasses} disabled={loading}>
          {loading ? <LoaderCircle className="spin" size={17} /> : <RefreshCw size={17} />}
          Yangilash
        </button>
      </div>

      {error && <div className="admin-flow-message error">{error}</div>}

      {loading && classes.length === 0 ? (
        <article className="portal-card admin-empty-state class-loading-state">
          <LoaderCircle className="spin" size={30} />
          <h3>Sinflar yuklanmoqda</h3>
          <p>Ma’lumotlar yangilanmoqda.</p>
        </article>
      ) : (
        <div className="class-api-grid">
          {classes.map((item) => {
            const studentCount = Number.isFinite(item.student_count)
              ? item.student_count
              : item.enrollments?.length ?? 0;

            return (
              <article className="portal-card class-api-card" key={item.id}>
                <div className="class-api-card-head">
                  <span><School size={24} /></span>
                  <div>
                    <small>{item.grade}-sinf guruhi</small>
                    <h2>{item.name}</h2>
                  </div>
                  <em aria-label={`${studentCount} o‘quvchi`}>{studentCount}</em>
                </div>
                <div className="class-api-program">
                  <BookOpenCheck size={17} />
                  <span>{item.program || "Dastur belgilanmagan"}</span>
                </div>
                <div className="class-api-footer">
                  <span><UserRound size={17} /> {item.teacher_detail?.full_name ?? "O‘qituvchi biriktirilmagan"}</span>
                  <span><UsersRound size={17} /> {studentCount} o‘quvchi</span>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {!loading && classes.length === 0 && !error && (
        <article className="portal-card admin-empty-state">
          <School size={30} />
          <h3>Hozircha sinf yaratilmagan</h3>
          <p>Yangi dars guruhi yaratilgach, u shu sahifada ko‘rinadi.</p>
        </article>
      )}
    </div>
  );
}
