"use client";

import {
  CheckCircle2,
  ClipboardList,
  Clock3,
  GraduationCap,
  LoaderCircle,
  Play,
  RotateCcw,
  Save,
  UserRound,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiRequest, hasLiveApi, type LiveDiagnosticReport, type PaginatedResponse } from "../lib/api";
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
};

type AttemptResponse = {
  id: number;
  remaining_seconds: number;
};

const statusLabel: Record<string, string> = {
  interview_completed: "Suhbat yakunlangan",
  test_recommended: "Test tavsiya qilingan",
  test_assigned: "Test biriktirilgan",
  diagnosed: "Diagnostika yakunlangan",
  roadmap_draft: "Roadmap draft",
  active: "Faol",
};

export function AdminTestsPanel({ selectedProfileId: initialSelectedProfileId = null, onComplete }: Props) {
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(initialSelectedProfileId);
  const [recommendedExams, setRecommendedExams] = useState<Exam[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<number | null>(null);
  const [activeExam, setActiveExam] = useState<Exam | null>(null);
  const [assignmentId, setAssignmentId] = useState<number | null>(null);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [history, setHistory] = useState<LiveDiagnosticReport[]>([]);
  const [historyError, setHistoryError] = useState("");
  const [loading, setLoading] = useState(false);
  const [savingQuestion, setSavingQuestion] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

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

    apiRequest<PaginatedResponse<LiveDiagnosticReport> | LiveDiagnosticReport[]>("/reports/?page_size=10")
      .then((reportPayload) => {
        setHistory(Array.isArray(reportPayload) ? reportPayload : reportPayload.results ?? []);
        setHistoryError("");
      })
      .catch(() => {
        setHistory([]);
        setHistoryError("So‘nggi natijalarni hozir yuklab bo‘lmadi.");
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedProfile = useMemo(
    () => profiles.find((item) => item.id === selectedProfileId) ?? null,
    [profiles, selectedProfileId],
  );
  const selectedExam = useMemo(
    () => recommendedExams.find((item) => item.id === selectedExamId) ?? null,
    [recommendedExams, selectedExamId],
  );
  const answeredCount = Object.keys(answers).length;
  const totalQuestions = activeExam?.exam_questions.length ?? 0;

  const resetFlow = () => {
    setRecommendedExams([]);
    setSelectedExamId(null);
    setActiveExam(null);
    setAssignmentId(null);
    setAttemptId(null);
    setAnswers({});
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
      setRecommendedExams(payload.tests);
      setSelectedExamId(payload.tests[0]?.id ?? null);
      if (payload.tests.length === 0) {
        setError("Bu profilga mos faol test topilmadi. Testning grade, purpose va kategoriyalarini tekshiring.");
      } else {
        setNotice(`${payload.tests.length} ta mos test topildi.`);
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
          delivery_mode: "administered",
        }),
      });
      setAssignmentId(assignment.assignment);
      setActiveExam(selectedExam);
      setError("");
      setNotice(`${selectedProfile.student.full_name} uchun test biriktirildi.`);
    } catch (requestError) {
      setNotice("");
      setError(requestError instanceof Error ? requestError.message : "Testni biriktirishda xatolik.");
    } finally {
      setLoading(false);
    }
  };

  const startExam = async () => {
    if (!assignmentId || !activeExam) return;
    setLoading(true);
    setError("");
    try {
      const attempt = await apiRequest<AttemptResponse>(`/assignments/${assignmentId}/start/`, { method: "POST" });
      setAttemptId(attempt.id);
      setAnswers({});
      setError("");
      setNotice("Imtihon boshlandi. Har bir tanlov backendga darhol saqlanadi.");
      window.dispatchEvent(new Event("bilimyol-exam-start"));
    } catch (requestError) {
      setNotice("");
      setError(requestError instanceof Error ? requestError.message : "Testni boshlashda xatolik.");
    } finally {
      setLoading(false);
    }
  };

  const saveAnswer = async (examQuestionId: number, optionId: number) => {
    if (!attemptId) return;
    setAnswers((current) => ({ ...current, [examQuestionId]: optionId }));
    setSavingQuestion(examQuestionId);
    setError("");
    try {
      await apiRequest(`/attempts/${attemptId}/answer/`, {
        method: "POST",
        body: JSON.stringify({
          exam_question: examQuestionId,
          selected_option: optionId,
          is_flagged: false,
        }),
      });
    } catch (requestError) {
      setAnswers((current) => {
        const next = { ...current };
        delete next[examQuestionId];
        return next;
      });
      setError(requestError instanceof Error ? requestError.message : "Javob saqlanmadi.");
    } finally {
      setSavingQuestion(null);
    }
  };

  const submitExam = async () => {
    if (!attemptId || !activeExam) return;
    if (answeredCount !== totalQuestions) {
      setError(`Yana ${totalQuestions - answeredCount} ta savolga javob berilmagan.`);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const report = await apiRequest<LiveDiagnosticReport>(`/attempts/${attemptId}/submit/`, { method: "POST" });
      setHistory((current) => [report, ...current.filter((item) => item.id !== report.id)].slice(0, 10));
      onComplete(report);
    } catch (requestError) {
      setNotice("");
      setError(requestError instanceof Error ? requestError.message : "Imtihonni yakunlashda xatolik.");
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

  return (
    <div className="admin-exam-page">
      <div className="admin-exam-heading">
        <div>
          <span>Qabul diagnostikasi</span>
          <h1>Admin bilan test o‘tkazish</h1>
          <p>Profil → tavsiya → biriktirish → javoblar → hisobot → individual roadmap.</p>
        </div>
        {(assignmentId || attemptId) && (
          <button className="portal-secondary" onClick={resetFlow}>
            <RotateCcw size={16} /> Yangidan boshlash
          </button>
        )}
      </div>

      {error && <div className="admin-flow-message error"><XCircle size={17} />{error}</div>}
      {notice && <div className="admin-flow-message success"><CheckCircle2 size={17} />{notice}</div>}

      {!attemptId && (
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
            <div className="admin-flow-step"><span>2</span><div><strong>Testni tanlang</strong><small>Grade va kategoriyalar bo‘yicha backend tavsiyasi.</small></div></div>
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
                  <button className="portal-primary" onClick={assignExam} disabled={loading || !selectedExamId}>
                    {loading ? <LoaderCircle className="spin" size={17} /> : <Save size={17} />}
                    Testni biriktirish
                  </button>
                ) : (
                  <button className="portal-primary" onClick={startExam} disabled={loading}>
                    {loading ? <LoaderCircle className="spin" size={17} /> : <Play size={17} />}
                    Testni boshlash
                  </button>
                )}
              </>
            )}
          </article>
        </div>
      )}

      {attemptId && activeExam && (
        <section className="admin-live-exam">
          <div className="admin-live-exam-head portal-card">
            <div><span>Test jarayoni</span><h2>{activeExam.title}</h2><p>{selectedProfile?.student.full_name}</p></div>
            <div className="exam-progress-box">
              <Clock3 size={18} />
              <strong>{answeredCount}/{totalQuestions}</strong>
              <small>javob saqlandi</small>
            </div>
          </div>

          <div className="admin-question-stack">
            {activeExam.exam_questions.map((examQuestion, index) => {
              const question = examQuestion.question_detail;
              return (
                <article className="portal-card mini-question-card" key={examQuestion.id}>
                  <div className="mini-question-head">
                    <span>{index + 1}</span>
                    <div><small>{question.subject_title}</small><h3>{question.prompt}</h3></div>
                    {savingQuestion === examQuestion.id && <LoaderCircle className="spin" size={18} />}
                  </div>
                  <div className="mini-question-options">
                    {question.options.map((option) => (
                      <button
                        type="button"
                        key={option.id}
                        className={answers[examQuestion.id] === option.id ? "selected" : ""}
                        onClick={() => saveAnswer(examQuestion.id, option.id)}
                        disabled={savingQuestion === examQuestion.id}
                      >
                        <i>{option.label}</i><span>{option.text}</span>
                      </button>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>

          <div className="admin-submit-bar portal-card">
            <div><strong>{answeredCount}/{totalQuestions} savol</strong><p>Barcha javoblar backendda saqlanadi.</p></div>
            <button className="portal-primary" onClick={submitExam} disabled={loading || answeredCount !== totalQuestions}>
              {loading ? <LoaderCircle className="spin" size={17} /> : <CheckCircle2 size={17} />}
              Imtihonni yakunlash
            </button>
          </div>
        </section>
      )}

      {!attemptId && historyError && history.length === 0 && (
        <div className="admin-history-note">{historyError} Test biriktirish va topshirish jarayoni ishlashda davom etadi.</div>
      )}

      {!attemptId && history.length > 0 && (
        <article className="portal-card admin-exam-history">
          <div className="portal-card-head"><div><span>So‘nggi natijalar</span><h2>Backendda saqlangan diagnostikalar</h2></div></div>
          <div className="portal-table-wrap">
            <table className="portal-table">
              <thead><tr><th>O‘quvchi</th><th>Test</th><th>Natija</th><th>Tayyorlik</th><th>Roadmap</th></tr></thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id}>
                    <td><strong>{item.student.full_name}</strong></td>
                    <td>{item.exam?.title ?? "Diagnostika"}</td>
                    <td><strong>{Math.round(Number(item.overall_score))}/100</strong></td>
                    <td><em className={`table-status ${item.readiness === "ready" ? "ready" : "risk"}`}>{item.readiness === "ready" ? "Tayyor" : "Tayyor emas"}</em></td>
                    <td>{item.roadmap ? <span className="role-label">{item.roadmap.status}</span> : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      )}
    </div>
  );
}
