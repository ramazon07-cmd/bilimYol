"use client";

import {
  Award,
  Building2,
  Check,
  CheckCircle2,
  FileCheck2,
  GraduationCap,
  LoaderCircle,
  Plus,
  Sparkles,
  Target,
  Upload,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  apiRequest,
  type LiveCertificate,
  type LiveUniversity,
  type LiveUniversityGoal,
  type PaginatedResponse,
  type WorkspaceSession,
  unpackList,
} from "../lib/api";
import { EmptyState, ErrorState, LoadingState } from "./portal/portal-ui";

type CertificateForm = {
  kind: LiveCertificate["kind"];
  title: string;
  score: string;
  issued_at: string;
  expires_at: string;
  file_url: string;
};

const emptyCertificate: CertificateForm = {
  kind: "ielts",
  title: "IELTS Academic",
  score: "",
  issued_at: "",
  expires_at: "",
  file_url: "",
};

export function UniversityJourney({
  session,
  studentId,
  title = "Dream University yo‘li",
  description = "Maqsad, oxirgi diagnostika va tasdiqlangan sertifikatlar real ma’lumotlardan hisoblanadi.",
}: {
  session?: WorkspaceSession;
  studentId?: number;
  title?: string;
  description?: string;
}) {
  const ownerId = studentId ?? (session?.role === "student" ? session.user.id : session?.university_goal?.student);
  const [universities, setUniversities] = useState<LiveUniversity[]>([]);
  const [goal, setGoal] = useState<LiveUniversityGoal | null>(null);
  const [certificates, setCertificates] = useState<LiveCertificate[]>([]);
  const [universityId, setUniversityId] = useState<number | null>(null);
  const [targetYear, setTargetYear] = useState(new Date().getFullYear() + 4);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [showCertificateForm, setShowCertificateForm] = useState(false);
  const [certificateForm, setCertificateForm] = useState<CertificateForm>(emptyCertificate);

  const load = async () => {
    if (!ownerId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [universityPayload, goalPayload, certificatePayload] = await Promise.all([
        apiRequest<PaginatedResponse<LiveUniversity> | LiveUniversity[]>("/universities/?is_active=true&page_size=100"),
        apiRequest<PaginatedResponse<LiveUniversityGoal> | LiveUniversityGoal[]>(`/university-goals/?student=${ownerId}&page_size=20`),
        apiRequest<PaginatedResponse<LiveCertificate> | LiveCertificate[]>(`/certificates/?student=${ownerId}&page_size=100`),
      ]);
      const nextUniversities = unpackList(universityPayload);
      const nextGoal = unpackList(goalPayload).find((item) => item.student === ownerId) ?? null;
      setUniversities(nextUniversities);
      setGoal(nextGoal);
      setCertificates(unpackList(certificatePayload).filter((item) => item.student === ownerId));
      setUniversityId(nextGoal?.university ?? nextUniversities[0]?.id ?? null);
      setTargetYear(nextGoal?.target_year ?? new Date().getFullYear() + 4);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "University ma’lumotlari yuklanmadi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
    // ownerId is the only identity that requires a reload.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ownerId]);

  const selected = universities.find((item) => item.id === universityId) ?? null;
  const requirements = useMemo(
    () => goal?.university === universityId ? goal.progress.requirements : [],
    [goal, universityId],
  );
  const overall = goal?.university === universityId ? Math.round(goal.progress.overall) : 0;
  const nextStep = useMemo(
    () => [...requirements].filter((item) => !item.complete).sort((a, b) => a.progress - b.progress)[0] ?? null,
    [requirements],
  );

  const saveGoal = async () => {
    if (!ownerId || !universityId) return;
    setSaving(true);
    setError("");
    try {
      const updated = goal
        ? await apiRequest<LiveUniversityGoal>(`/university-goals/${goal.id}/`, {
            method: "PATCH",
            body: JSON.stringify({ university: universityId, target_year: targetYear }),
          })
        : await apiRequest<LiveUniversityGoal>("/university-goals/", {
            method: "POST",
            body: JSON.stringify({ student: ownerId, university: universityId, target_year: targetYear }),
          });
      setGoal(updated);
      setUniversityId(updated.university);
      setNotice("Maqsad database’da saqlandi.");
      window.setTimeout(() => setNotice(""), 2400);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Maqsad saqlanmadi.");
    } finally {
      setSaving(false);
    }
  };

  const addCertificate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!ownerId) return;
    setSaving(true);
    setError("");
    try {
      const created = await apiRequest<LiveCertificate>("/certificates/", {
        method: "POST",
        body: JSON.stringify({
          student: ownerId,
          ...certificateForm,
          expires_at: certificateForm.expires_at || null,
        }),
      });
      setCertificates((current) => [created, ...current]);
      setCertificateForm(emptyCertificate);
      setShowCertificateForm(false);
      setNotice("Sertifikat tekshiruvga yuborildi.");
      window.setTimeout(() => setNotice(""), 2400);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Sertifikat qo‘shilmadi.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingState label="Dream University ma’lumotlari yuklanmoqda..." />;
  if (error && !universities.length) return <ErrorState message={error} onRetry={() => void load()} />;
  if (!ownerId) return <EmptyState title="O‘quvchi tanlanmagan" description="University maqsadini ko‘rish uchun o‘quvchini tanlang." />;
  if (!universities.length) return <EmptyState title="Universitetlar hali kiritilmagan" description="Administrator universitet katalogini to‘ldirgach bu bo‘lim ishlaydi." icon={GraduationCap} />;

  return (
    <section className="university-journey">
      <div className="university-title-row">
        <div><span className="university-eyebrow"><GraduationCap size={15} /> Qabul strategiyasi</span><h1>{title}</h1><p>{description}</p></div>
        <div className="university-picker-group">
          <label className="university-picker"><small>Dream University</small><select value={universityId ?? ""} onChange={(event) => setUniversityId(Number(event.target.value))}>{universities.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
          <label className="university-picker year"><small>Maqsad yili</small><input type="number" min={new Date().getFullYear()} max={new Date().getFullYear() + 10} value={targetYear} onChange={(event) => setTargetYear(Number(event.target.value))} /></label>
        </div>
      </div>

      {error && <div className="admin-flow-message error">{error}</div>}
      {notice && <div className="admin-flow-message success"><CheckCircle2 size={16} /> {notice}</div>}

      {selected && (
        <div className="university-hero-card">
          <div className="university-mark">{selected.name.split(" ").map((part) => part[0]).slice(0, 3).join("")}</div>
          <div className="university-name"><span><Building2 size={15} /> {selected.country}{selected.city ? ` · ${selected.city}` : ""}</span><h2>{selected.name}</h2><p>{targetYear} qabul maqsadi</p></div>
          <div className="university-overall"><div style={{ "--goal-progress": `${overall * 3.6}deg` } as React.CSSProperties}><strong>{overall}%</strong><small>tayyor</small></div><span>Oxirgi mock + verified sertifikatlar</span></div>
          <div className="university-next"><Sparkles size={18} /><p><strong>Keyingi eng kuchli qadam</strong>{nextStep ? `${nextStep.label}: ${nextStep.current} → ${nextStep.target} ${nextStep.unit}` : goal ? "Barcha talablar bajarilgan." : "Maqsadni saqlang — progress backendda hisoblanadi."}</p></div>
        </div>
      )}

      <div className="university-grid">
        <article className="goal-progress-card">
          <div className="goal-card-head"><div><span>Qabul talablari</span><h3>{requirements.length ? `${requirements.length} ta indikator` : "Maqsadni saqlang"}</h3></div><em>{goal?.progress.latest_mock ? `Mock: ${new Date(goal.progress.latest_mock).toLocaleDateString("uz-UZ")}` : "Mock hali yo‘q"}</em></div>
          {requirements.length ? (
            <div className="goal-requirements">
              {requirements.map((item) => (
                <div key={item.key} className={item.complete ? "complete" : ""}>
                  <span className="goal-source">{item.source === "certificate" ? <Award size={17} /> : <FileCheck2 size={17} />}</span>
                  <div><strong>{item.label}</strong><small>{item.source === "certificate" ? (item.has_certificate ? "Tasdiqlangan sertifikat" : "Verified sertifikat kerak") : "Oxirgi diagnostika"}</small><i><b style={{ width: `${item.progress}%` }} /></i></div>
                  <p><strong>{item.current}</strong><span>/ {item.target} {item.unit}</span></p>
                  <em>{item.complete ? <><CheckCircle2 size={14} /> Tayyor</> : `${Math.round(item.progress)}%`}</em>
                </div>
              ))}
            </div>
          ) : <EmptyState title="Progress hali hisoblanmagan" description="Universitetni tanlab, maqsadni saqlang." icon={Target} />}
        </article>

        <aside className="certificate-stack">
          {certificates.map((certificate) => (
            <article key={certificate.id}>
              <div className="certificate-head"><span><Award size={19} /></span><div><small>{certificate.verification_status === "verified" ? "Tasdiqlangan" : certificate.verification_status === "rejected" ? "Qayta yuborish kerak" : "Tekshiruvda"}</small><h3>{certificate.title}</h3></div><em className={certificate.verification_status}><Check size={13} /> {certificate.verification_status}</em></div>
              <strong>{Number(certificate.score)} <small>{certificate.kind === "ielts" ? "band" : "ball"}</small></strong>
              <p>{new Date(certificate.issued_at).toLocaleDateString("uz-UZ")}{certificate.verification_note ? ` · ${certificate.verification_note}` : ""}</p>
            </article>
          ))}
          {!certificates.length && <EmptyState title="Sertifikat yo‘q" description="IELTS, SAT yoki CEFR natijasini qo‘shing." icon={Award} />}
          <button className="certificate-upload" onClick={() => setShowCertificateForm(true)}><Upload size={17} /> Sertifikat qo‘shish</button>
        </aside>
      </div>

      {showCertificateForm && (
        <div className="certificate-form-backdrop" role="dialog" aria-modal="true">
          <form className="certificate-form portal-card" onSubmit={addCertificate}>
            <div className="portal-card-head"><div><span>Yangi hujjat</span><h2>Sertifikat qo‘shish</h2></div><button type="button" onClick={() => setShowCertificateForm(false)} aria-label="Yopish"><X size={19} /></button></div>
            <div className="certificate-form-grid">
              <label><span>Turi</span><select value={certificateForm.kind} onChange={(event) => setCertificateForm((current) => ({ ...current, kind: event.target.value as LiveCertificate["kind"], title: event.target.value === "sat" ? "SAT" : event.target.value === "cefr" ? "CEFR" : event.target.value === "ielts" ? "IELTS Academic" : current.title }))}><option value="ielts">IELTS</option><option value="sat">SAT</option><option value="cefr">CEFR</option><option value="other">Boshqa</option></select></label>
              <label><span>Nomi</span><input required value={certificateForm.title} onChange={(event) => setCertificateForm((current) => ({ ...current, title: event.target.value }))} /></label>
              <label><span>Natija</span><input required type="number" step="0.01" value={certificateForm.score} onChange={(event) => setCertificateForm((current) => ({ ...current, score: event.target.value }))} /></label>
              <label><span>Berilgan sana</span><input required type="date" value={certificateForm.issued_at} onChange={(event) => setCertificateForm((current) => ({ ...current, issued_at: event.target.value }))} /></label>
              <label><span>Amal qilish sanasi</span><input type="date" value={certificateForm.expires_at} onChange={(event) => setCertificateForm((current) => ({ ...current, expires_at: event.target.value }))} /></label>
              <label><span>Hujjat havolasi</span><input type="url" placeholder="https://..." value={certificateForm.file_url} onChange={(event) => setCertificateForm((current) => ({ ...current, file_url: event.target.value }))} /></label>
            </div>
            <div className="certificate-form-actions"><button type="button" className="portal-secondary" onClick={() => setShowCertificateForm(false)}>Bekor qilish</button><button className="portal-primary" disabled={saving}>{saving ? <LoaderCircle className="spin" size={17} /> : <Plus size={17} />} Tekshiruvga yuborish</button></div>
          </form>
        </div>
      )}

      <div className="university-actions"><div><Target size={19} /><p><strong>Maqsad database’da saqlanadi.</strong> Universitet o‘zgarsa, barcha mezon va progress backendda qayta hisoblanadi.</p></div><button onClick={() => void saveGoal()} disabled={saving || !universityId}>{saving ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />} Maqsadni saqlash</button></div>
    </section>
  );
}
