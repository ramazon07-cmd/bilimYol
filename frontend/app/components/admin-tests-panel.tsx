"use client";

import {
  CheckCircle2,
  ClipboardCopy,
  ClipboardList,
  Eye,
  GraduationCap,
  KeyRound,
  LoaderCircle,
  RotateCcw,
  Save,
  Search,
  SlidersHorizontal,
  UserRound,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  apiRequest,
  hasLiveApi,
  type LiveDiagnosticReport,
  type LiveDiagnosticReportDetail,
  type PaginatedResponse,
} from "../lib/api";
import { AdminDiagnosticDetail } from "./admin-diagnostic-detail";
import {
  getStudentProfiles,
  recommendStudentTests,
  type Exam,
  type StudentProfile,
} from "../lib/profiling-api";

type Props = {
  selectedProfileId?: number | null;
  onComplete: (report: LiveDiagnosticReport) => void;
};

type AssignmentResponse = {
  assignment: number;
  created: boolean;
  student: string;
  delivery_mode: string;
  credentials: {
    username: string;
    temporary_password: string;
  };
};

const statusLabel: Record<string, string> = {
  interview_completed: "Suhbat yakunlangan",
  test_recommended: "Test tavsiya qilingan",
  test_assigned: "Test biriktirilgan",
  diagnosed: "Diagnostika yakunlangan",
  roadmap_draft: "Roadmap draft",
  active: "Faol",
};

const initialFilters = {
  search: "",
  grade: "",
  subject: "",
  readiness: "",
  scoreMin: "",
  scoreMax: "",
  dateFrom: "",
  dateTo: "",
};

export function AdminTestsPanel({ selectedProfileId: initialSelectedProfileId = null, onComplete }: Props) {
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(initialSelectedProfileId);
  const [recommendedExams, setRecommendedExams] = useState<Exam[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<number | null>(null);
  const [assignmentId, setAssignmentId] = useState<number | null>(null);
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const [credentials, setCredentials] = useState<AssignmentResponse["credentials"] | null>(null);
  const [history, setHistory] = useState<LiveDiagnosticReport[]>([]);
  const [historyError, setHistoryError] = useState("");
  const [historyLoading, setHistoryLoading] = useState(false);
  const [filters, setFilters] = useState(initialFilters);
  const [selectedReport, setSelectedReport] = useState<LiveDiagnosticReportDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadHistory = async (nextFilters = filters) => {
    setHistoryLoading(true);
    const query = new URLSearchParams({ page_size: "100", ordering: "-generated_at" });
    if (nextFilters.search) query.set("search", nextFilters.search);
    if (nextFilters.grade) query.set("grade", nextFilters.grade);
    if (nextFilters.subject) query.set("subject", nextFilters.subject);
    if (nextFilters.readiness) query.set("readiness", nextFilters.readiness);
    if (nextFilters.scoreMin) query.set("score_min", nextFilters.scoreMin);
    if (nextFilters.scoreMax) query.set("score_max", nextFilters.scoreMax);
    if (nextFilters.dateFrom) query.set("date_from", nextFilters.dateFrom);
    if (nextFilters.dateTo) query.set("date_to", nextFilters.dateTo);
    try {
      const reportPayload = await apiRequest<PaginatedResponse<LiveDiagnosticReport> | LiveDiagnosticReport[]>(
        `/reports/?${query.toString()}`,
      );
      setHistory(Array.isArray(reportPayload) ? reportPayload : reportPayload.results ?? []);
      setHistoryError("");
    } catch {
      setHistory([]);
      setHistoryError("Diagnostika tarixini hozir yuklab bo‘lmadi.");
    } finally {
      setHistoryLoading(false);
    }
  };

  const openReportDetail = async (reportId: number) => {
    setDetailLoading(true);
    setError("");
    try {
      const detail = await apiRequest<LiveDiagnosticReportDetail>(`/reports/${reportId}/`);
      setSelectedReport(detail);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Diagnostika tafsilotlarini ochib bo‘lmadi.");
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    if (!hasLiveApi()) return;

    getStudentProfiles("ordering=-created_at&page_size=100")
      .then((profilePayload) => {
        setProfiles(profilePayload.results);
        if (!selectedProfileId && profilePayload.results.length > 0) {
          const preferred = profilePayload.results.find((item) =>
            ["interview_completed", "test_recommended", "test_assigned"].includes(item.status),
          );
          setSelectedProfileId(preferred?.id ?? profilePayload.results[0].id);
        }
      })
      .catch((requestError: Error) => setError(requestError.message));

    const historyTimer = window.setTimeout(() => void loadHistory(initialFilters), 0);
    return () => window.clearTimeout(historyTimer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedProfile = useMemo(
    () => profiles.find((item) => item.id === selectedProfileId) ?? null,
    [profiles, selectedProfileId],
  );
  const selectedExam = useMemo(
    () => recommendedExams.find((item) => item.id === selectedExamId) ?? null,
    [recommendedExams, selectedExamId],
  );

  const resetFlow = () => {
    setRecommendedExams([]);
    setSelectedExamId(null);
    setAssignmentId(null);
    setTemporaryPassword("");
    setCredentials(null);
    setError("");
    setNotice("");
  };

  const loadRecommendations = async () => {
    if (!selectedProfileId) {
      setError("Avval o‘quvchini tanlang.");
      return;
    }
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const payload = await recommendStudentTests(selectedProfileId);
      let tests = payload.tests;

      if (tests.length === 0 && selectedProfile?.grade) {
        const directPayload = await apiRequest<PaginatedResponse<Exam> | Exam[]>(
          `/exams/?status=active&grade=${selectedProfile.grade}&page_size=100`,
        );
        tests = Array.isArray(directPayload) ? directPayload : directPayload.results ?? [];
      }

      if (tests.length === 0) {
        const generalPayload = await apiRequest<PaginatedResponse<Exam> | Exam[]>(
          "/exams/?status=active&page_size=100",
        );
        const allActive = Array.isArray(generalPayload) ? generalPayload : generalPayload.results ?? [];
        tests = allActive.filter((exam) => exam.grade == null);
      }

      setRecommendedExams(tests);
      setSelectedExamId(tests[0]?.id ?? null);
      if (tests.length === 0) {
        setError(`${selectedProfile?.grade ?? "Bu"}-sinf uchun faol English testi hali yaratilmagan. Backendda seed_english_diagnostics buyrug‘ini ishga tushiring.`);
      } else {
        setNotice(`${tests.length} ta mos test topildi.`);
      }
    } catch (requestError) {
      setNotice("");
      setError(requestError instanceof Error ? requestError.message : "Test tavsiyalarini olishda xatolik.");
    } finally {
      setLoading(false);
    }
  };

  const assignExam = async () => {
    if (!selectedProfile || !selectedExam) {
      setError("O‘quvchi va testni tanlang.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const assignment = await apiRequest<AssignmentResponse>(`/exams/${selectedExam.id}/assign-student/`, {
        method: "POST",
        body: JSON.stringify({
          student: selectedProfile.student.id,
          classroom: null,
          delivery_mode: "self",
          temporary_password: temporaryPassword.trim() || undefined,
        }),
      });
      setAssignmentId(assignment.assignment);
      setCredentials(assignment.credentials);
      setError("");
      setNotice(`${selectedProfile.student.full_name} uchun English testi biriktirildi.`);
    } catch (requestError) {
      setNotice("");
      setError(requestError instanceof Error ? requestError.message : "Testni biriktirishda xatolik.");
    } finally {
      setLoading(false);
    }
  };

  if (!hasLiveApi()) {
    return (
      <article className="portal-card admin-exam-empty">
        <ClipboardList size={28} />
        <h2>Real diagnostika uchun API kerak</h2>
        <p><code>NEXT_PUBLIC_API_BASE_URL</code> ni backend manziliga sozlang.</p>
      </article>
    );
  }

  if (selectedReport) {
    return (
      <AdminDiagnosticDetail
        report={selectedReport}
        onBack={() => setSelectedReport(null)}
        onOpenStudentView={onComplete}
        onOpenAttempt={openReportDetail}
        onReassigned={() => void loadHistory()}
      />
    );
  }

  return (
    <div className="admin-exam-page">
      <div className="admin-exam-heading">
        <div>
          <span>Qabul diagnostikasi</span>
          <h1>English testini biriktirish</h1>
          <p>Admin testni biriktiradi va credential beradi. O‘quvchi o‘z kabinetida mustaqil ishlaydi.</p>
        </div>
        {assignmentId && (
          <button className="portal-secondary" onClick={resetFlow}>
            <RotateCcw size={16} /> Boshqa test biriktirish
          </button>
        )}
      </div>

      {error && <div className="admin-flow-message error"><XCircle size={17} />{error}</div>}
      {notice && <div className="admin-flow-message success"><CheckCircle2 size={17} />{notice}</div>}

      <div className="admin-exam-setup-grid">
          <article className="portal-card admin-exam-setup">
            <div className="admin-flow-step"><span>1</span><div><strong>O‘quvchini tanlang</strong><small>Suhbat va kategoriya profili tayyor bo‘lishi kerak.</small></div></div>
            <label className="admin-field">
              <span>O‘quvchi profili</span>
              <select
                value={selectedProfileId ?? ""}
                onChange={(event) => {
                  setSelectedProfileId(Number(event.target.value) || null);
                  resetFlow();
                }}
              >
                <option value="">Tanlang</option>
                {profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.student.full_name} · {profile.grade ?? "?"}-sinf · {statusLabel[profile.status] ?? profile.status}
                  </option>
                ))}
              </select>
            </label>

            {selectedProfile && (
              <div className="selected-student-card">
                <span><UserRound size={20} /></span>
                <div>
                  <strong>{selectedProfile.student.full_name}</strong>
                  <small>{selectedProfile.admission_code} · {selectedProfile.school_name || "Maktab kiritilmagan"}</small>
                </div>
                <em>{selectedProfile.grade ?? "—"}-sinf</em>
              </div>
            )}

            <button className="portal-primary" onClick={loadRecommendations} disabled={loading || !selectedProfileId}>
              {loading ? <LoaderCircle className="spin" size={17} /> : <GraduationCap size={17} />}
              Mos testlarni topish
            </button>
          </article>

          <article className="portal-card admin-exam-setup">
            <div className="admin-flow-step"><span>2</span><div><strong>English testini tanlang</strong><small>Sinfga mos faol English diagnostikasi.</small></div></div>
            {recommendedExams.length === 0 ? (
              <div className="admin-exam-placeholder"><ClipboardList size={25} /><p>Avval o‘quvchi uchun tavsiyalarni oling.</p></div>
            ) : (
              <>
                <div className="recommended-exam-list">
                  {recommendedExams.map((exam) => (
                    <button
                      key={exam.id}
                      className={selectedExamId === exam.id ? "active" : ""}
                      onClick={() => setSelectedExamId(exam.id)}
                    >
                      <span><ClipboardList size={18} /></span>
                      <div><strong>{exam.title}</strong><small>{exam.grade ? `${exam.grade}-sinf` : "Barcha sinflar"} · {exam.duration_minutes} daqiqa</small></div>
                      <em>{exam.exam_questions.length} savol</em>
                    </button>
                  ))}
                </div>
                {!assignmentId ? (
                  <>
                    <label className="admin-field">
                      <span>Vaqtinchalik parol</span>
                      <input
                        type="text"
                        minLength={8}
                        value={temporaryPassword}
                        onChange={(event) => setTemporaryPassword(event.target.value)}
                        placeholder="Bo‘sh qoldirilsa avtomatik yaratiladi"
                      />
                      <small>Kamida 8 belgi. Parol faqat biriktirishdan keyin bir marta ko‘rsatiladi.</small>
                    </label>
                  <button className="portal-primary" onClick={assignExam} disabled={loading || !selectedExamId}>
                    {loading ? <LoaderCircle className="spin" size={17} /> : <Save size={17} />}
                    Testni biriktirish
                  </button>
                  </>
                ) : (
                  credentials && (
                    <div className="admin-credential-card">
                      <div><KeyRound size={20} /><span><strong>O‘quvchiga beriladigan ma’lumot</strong><small>Parol backendda ochiq saqlanmaydi.</small></span></div>
                      <label><span>Login</span><strong>{credentials.username}</strong></label>
                      <label><span>Vaqtinchalik parol</span><strong>{credentials.temporary_password}</strong></label>
                      <button
                        type="button"
                        className="portal-secondary"
                        onClick={() => void navigator.clipboard.writeText(
                          `Login: ${credentials.username}\nParol: ${credentials.temporary_password}`,
                        )}
                      >
                        <ClipboardCopy size={16} /> Login va parolni nusxalash
                      </button>
                    </div>
                  )
                )}
              </>
            )}
          </article>
        </div>

      <article className="portal-card admin-exam-history">
          <div className="portal-card-head"><div><span>Diagnostika tarixi</span><h2>Backendda saqlangan natijalar</h2></div><em>{history.length} ta natija</em></div>
          <form
            className="admin-diagnostic-filters"
            onSubmit={(event) => {
              event.preventDefault();
              void loadHistory();
            }}
          >
            <label className="wide"><span>Student yoki test</span><div><Search size={15} /><input value={filters.search} onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder="Ism, login yoki test nomi" /></div></label>
            <label><span>Sinf</span><select value={filters.grade} onChange={(event) => setFilters((current) => ({ ...current, grade: event.target.value }))}><option value="">Barchasi</option>{[5, 6, 7, 8, 9, 10, 11].map((grade) => <option key={grade} value={grade}>{grade}-sinf</option>)}</select></label>
            <label><span>Fan</span><select value={filters.subject} onChange={(event) => setFilters((current) => ({ ...current, subject: event.target.value }))}><option value="">Barcha fanlar</option><option value="english">English</option><option value="math">Mathematics</option><option value="iq">IQ/Critical Thinking</option></select></label>
            <label><span>Natija</span><select value={filters.readiness} onChange={(event) => setFilters((current) => ({ ...current, readiness: event.target.value }))}><option value="">Barchasi</option><option value="ready">Tayyor</option><option value="not_ready">Tayyor emas</option></select></label>
            <label><span>Min. ball</span><input type="number" min="0" max="100" value={filters.scoreMin} onChange={(event) => setFilters((current) => ({ ...current, scoreMin: event.target.value }))} /></label>
            <label><span>Max. ball</span><input type="number" min="0" max="100" value={filters.scoreMax} onChange={(event) => setFilters((current) => ({ ...current, scoreMax: event.target.value }))} /></label>
            <label><span>Boshlanish sana</span><input type="date" value={filters.dateFrom} onChange={(event) => setFilters((current) => ({ ...current, dateFrom: event.target.value }))} /></label>
            <label><span>Tugash sana</span><input type="date" value={filters.dateTo} onChange={(event) => setFilters((current) => ({ ...current, dateTo: event.target.value }))} /></label>
            <button type="submit" className="portal-primary" disabled={historyLoading}>{historyLoading ? <LoaderCircle className="spin" size={16} /> : <SlidersHorizontal size={16} />} Filterlash</button>
            <button type="button" className="portal-secondary" onClick={() => { setFilters(initialFilters); void loadHistory(initialFilters); }}>Tozalash</button>
          </form>

          {historyError && <div className="admin-history-note">{historyError}</div>}
          {!historyError && !historyLoading && history.length === 0 && <div className="admin-history-note">Tanlangan filterlar bo‘yicha diagnostika topilmadi.</div>}
          <div className="portal-table-wrap">
            <table className="portal-table">
              <thead><tr><th>O‘quvchi</th><th>Sinf</th><th>Test va fanlar</th><th>Sana</th><th>Natija</th><th>Javoblar</th><th>Holat</th><th>Amal</th></tr></thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id}>
                    <td><strong>{item.student.full_name}</strong><small>@{item.student.username}</small></td>
                    <td><strong>{item.grade ?? item.exam?.grade ?? "—"}-sinf</strong><small>{item.classroom?.name ?? "—"}</small></td>
                    <td><strong>{item.exam?.title ?? "Diagnostika"}</strong><small>{item.subject_results.map((result) => result.subject.title).join(", ")}</small></td>
                    <td>{item.generated_at ? new Date(item.generated_at).toLocaleDateString("uz-UZ") : "—"}</td>
                    <td><strong>{Math.round(Number(item.overall_score))}/100</strong></td>
                    <td>{item.answer_summary ? <><strong>{item.answer_summary.correct} / {item.answer_summary.total}</strong><small>{item.answer_summary.incorrect} noto‘g‘ri · {item.answer_summary.unanswered} javobsiz</small></> : "—"}</td>
                    <td><em className={`table-status ${item.readiness === "ready" ? "ready" : "risk"}`}>{item.readiness === "ready" ? "Tayyor" : "Tayyor emas"}</em></td>
                    <td><button type="button" className="admin-detail-button" onClick={() => void openReportDetail(item.id)} disabled={detailLoading}>{detailLoading ? <LoaderCircle className="spin" size={15} /> : <Eye size={15} />} Batafsil</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
      </article>
    </div>
  );
}
