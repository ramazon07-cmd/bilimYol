"use client";

import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock3,
  Download,
  Eye,
  History,
  LoaderCircle,
  RefreshCcw,
  Target,
  UserRound,
  XCircle,
} from "lucide-react";
import { useMemo, useState } from "react";

import {
  apiRequest,
  type LiveDiagnosticReportDetail,
  type LiveReportComparison,
} from "../lib/api";
import { rbisChartColor } from "../lib/rbis-theme";

type Props = {
  report: LiveDiagnosticReportDetail;
  onBack: () => void;
  onOpenStudentView: (report: LiveDiagnosticReportDetail) => void;
  onOpenAttempt: (reportId: number) => void;
  onReassigned: () => void;
};

const dateFormatter = new Intl.DateTimeFormat("uz-UZ", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

function score(value: string | number) {
  return Math.round(Number(value) || 0);
}

export function AdminDiagnosticDetail({
  report,
  onBack,
  onOpenStudentView,
  onOpenAttempt,
  onReassigned,
}: Props) {
  const [comparison, setComparison] = useState<LiveReportComparison | null>(null);
  const [loadingComparison, setLoadingComparison] = useState<number | null>(null);
  const [reassigning, setReassigning] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const summary = report.answer_summary ?? { total: 0, correct: 0, incorrect: 0, unanswered: 0 };

  const breakdownRows = useMemo(() => [
    ...(report.topic_results ?? []).map((item) => ({
      id: `topic-${item.id}`,
      kind: "Mavzu",
      title: item.topic?.title ?? "Mavzu",
      score: score(item.score),
      questions: item.question_count,
      confidence: item.confidence,
    })),
    ...(report.skill_results ?? []).map((item) => ({
      id: `skill-${item.id}`,
      kind: "Ko‘nikma",
      title: item.skill?.title ?? "Ko‘nikma",
      score: score(item.score),
      questions: item.question_count,
      confidence: item.confidence,
    })),
  ], [report.skill_results, report.topic_results]);

  const compareWith = async (otherId: number) => {
    setLoadingComparison(otherId);
    setError("");
    try {
      const payload = await apiRequest<LiveReportComparison>(`/reports/${report.id}/compare/?other=${otherId}`);
      setComparison(payload);
      window.setTimeout(() => document.getElementById("attempt-comparison")?.scrollIntoView({ behavior: "smooth" }), 0);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Urinishlarni taqqoslab bo‘lmadi.");
    } finally {
      setLoadingComparison(null);
    }
  };

  const reassign = async () => {
    if (!window.confirm(`${report.student.full_name} uchun shu testni qayta tayinlaysizmi?`)) return;
    setReassigning(true);
    setError("");
    setNotice("");
    try {
      await apiRequest(`/reports/${report.id}/reassign/`, { method: "POST", body: JSON.stringify({}) });
      setNotice("Test qayta tayinlandi. Eski natija o‘zgarmadi.");
      onReassigned();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Testni qayta tayinlab bo‘lmadi.");
    } finally {
      setReassigning(false);
    }
  };

  return (
    <div className="admin-diagnostic-detail">
      <div className="admin-detail-toolbar">
        <button type="button" className="portal-secondary" onClick={onBack}><ArrowLeft size={16} /> Diagnostikalarga qaytish</button>
        <div>
          <button type="button" className="portal-secondary" onClick={() => onOpenStudentView(report)}><Eye size={16} /> Student ko‘rinishida ochish</button>
          <button type="button" className="portal-secondary" onClick={() => window.print()}><Download size={16} /> PDF yuklash</button>
          <button type="button" className="portal-primary" onClick={reassign} disabled={reassigning}>
            {reassigning ? <LoaderCircle className="spin" size={16} /> : <RefreshCcw size={16} />} Testni qayta tayinlash
          </button>
        </div>
      </div>

      {error && <div className="admin-flow-message error"><XCircle size={17} />{error}</div>}
      {notice && <div className="admin-flow-message success"><CheckCircle2 size={17} />{notice}</div>}

      <section className="portal-card admin-detail-hero">
        <div className="admin-detail-student">
          <span><UserRound size={25} /></span>
          <div>
            <small>Student profili</small>
            <h1>{report.student.full_name}</h1>
            <p>@{report.student.username} · {report.grade ?? report.exam?.grade ?? "—"}-sinf · {report.classroom?.name ?? "Sinf biriktirilmagan"}</p>
          </div>
        </div>
        <div className="admin-detail-exam">
          <small>Diagnostika</small>
          <strong>{report.exam?.title ?? "Diagnostik test"}</strong>
          <span><Clock3 size={14} /> {formatDate(report.generated_at ?? report.attempt_detail.submitted_at)}</span>
        </div>
      </section>

      <div className="admin-detail-metrics">
        <article className="portal-card"><span><BarChart3 size={19} /></span><small>Umumiy ball</small><strong>{score(report.overall_score)}/100</strong></article>
        <article className="portal-card success"><span><CheckCircle2 size={19} /></span><small>To‘g‘ri</small><strong>{summary.correct}</strong></article>
        <article className="portal-card danger"><span><XCircle size={19} /></span><small>Noto‘g‘ri</small><strong>{summary.incorrect}</strong></article>
        <article className="portal-card neutral"><span><Target size={19} /></span><small>Javobsiz</small><strong>{summary.unanswered}</strong></article>
      </div>

      <div className="admin-detail-two-column">
        <article className="portal-card admin-detail-section">
          <div className="portal-card-head"><div><span>Fanlar bo‘yicha</span><h2>Natijalar</h2></div><em>{report.subject_results.length} fan</em></div>
          <div className="admin-subject-result-list">
            {report.subject_results.map((item, index) => (
              <div key={item.subject.slug}>
                <span style={{ background: rbisChartColor(item.subject.slug, index) }} />
                <div><strong>{item.subject.title}</strong><small>{score(item.earned_points ?? 0)} / {score(item.possible_points ?? 0)} ball</small></div>
                <em>{score(item.score)}/100</em>
              </div>
            ))}
          </div>
        </article>

        <article className="portal-card admin-detail-section">
          <div className="portal-card-head"><div><span>Tahlil</span><h2>Kuchli va zaif tomonlar</h2></div><Target size={20} /></div>
          <div className="admin-strength-grid">
            <div><strong>Kuchli tomonlar</strong>{report.strengths.length ? report.strengths.map((item) => <span key={`${item.kind}-${item.title}`}><CheckCircle2 size={14} /> {item.title} <em>{score(item.score)}</em></span>) : <small>67 balldan yuqori yo‘nalish topilmadi.</small>}</div>
            <div><strong>Rivojlantirish kerak</strong>{report.weaknesses.length ? report.weaknesses.map((item) => <span key={`${item.kind}-${item.title}`}><Target size={14} /> {item.title} <em>{score(item.score)}</em></span>) : <small>Zaif yo‘nalish topilmadi.</small>}</div>
          </div>
        </article>
      </div>

      <article className="portal-card admin-detail-section">
        <div className="portal-card-head"><div><span>Mavzu va skill</span><h2>Kesim bo‘yicha natija</h2></div></div>
        <div className="portal-table-wrap">
          <table className="portal-table admin-breakdown-table">
            <thead><tr><th>Turi</th><th>Nomi</th><th>Savollar</th><th>Ishonchlilik</th><th>Natija</th></tr></thead>
            <tbody>{breakdownRows.map((item) => <tr key={item.id}><td><span className="role-label">{item.kind}</span></td><td><strong>{item.title}</strong></td><td>{item.questions}</td><td>{item.confidence}</td><td><strong>{item.score}/100</strong></td></tr>)}</tbody>
          </table>
        </div>
      </article>

      <article className="portal-card admin-detail-section">
        <div className="portal-card-head"><div><span>Tavsiya</span><h2>Roadmap</h2></div><span className="role-label">{report.roadmap?.status ?? "Yaratilmagan"}</span></div>
        {report.roadmap?.stages?.length ? (
          <div className="admin-roadmap-stages">
            {report.roadmap.stages.map((stage) => (
              <div key={stage.id}><i>{stage.order}</i><div><strong>{stage.title}</strong><small>{stage.start_month}–{stage.end_month} oy · haftasiga {stage.weekly_hours} soat</small><p>{stage.rationale}</p></div><em>{stage.start_score} → {stage.target_score}</em></div>
            ))}
          </div>
        ) : <p className="admin-detail-empty">Bu natija uchun roadmap bosqichlari hali yaratilmagan.</p>}
      </article>

      <article className="portal-card admin-detail-section">
        <div className="portal-card-head"><div><span>Tarix</span><h2>Oldingi test urinishlari</h2></div><History size={20} /></div>
        {report.previous_attempts.length ? (
          <div className="admin-attempt-history">
            {report.previous_attempts.map((item) => (
              <div key={item.id}>
                <div><strong>{item.exam_title}</strong><small>{formatDate(item.generated_at)} {item.same_exam ? "· Shu test" : ""}</small></div>
                <em>{score(item.overall_score)}/100</em>
                <button type="button" className="portal-secondary" onClick={() => compareWith(item.id)} disabled={loadingComparison === item.id}>
                  {loadingComparison === item.id ? <LoaderCircle className="spin" size={15} /> : <BarChart3 size={15} />} Taqqoslash
                </button>
                <button type="button" className="portal-secondary" onClick={() => onOpenAttempt(item.id)}>Batafsil <ArrowRight size={14} /></button>
              </div>
            ))}
          </div>
        ) : <p className="admin-detail-empty">Bu studentning boshqa saqlangan diagnostikasi yo‘q.</p>}
      </article>

      {comparison && (
        <article className="portal-card admin-detail-section admin-comparison" id="attempt-comparison">
          <div className="portal-card-head"><div><span>Taqqoslash</span><h2>Urinishlar o‘rtasidagi farq</h2></div><strong className={comparison.overall_delta >= 0 ? "positive" : "negative"}>{comparison.overall_delta >= 0 ? "+" : ""}{comparison.overall_delta} ball</strong></div>
          <div className="comparison-head"><span>{formatDate(comparison.previous.generated_at)} · {score(comparison.previous.overall_score)}</span><ArrowRight size={18} /><span>{formatDate(comparison.current.generated_at)} · {score(comparison.current.overall_score)}</span></div>
          <div className="comparison-rows">
            {comparison.subjects.map((item) => (
              <div key={item.id}><strong>{item.title}</strong><span>{score(item.previous_score)} → {score(item.current_score)}</span><em className={item.delta >= 0 ? "positive" : "negative"}>{item.delta >= 0 ? "+" : ""}{item.delta}</em></div>
            ))}
          </div>
        </article>
      )}
    </div>
  );
}
