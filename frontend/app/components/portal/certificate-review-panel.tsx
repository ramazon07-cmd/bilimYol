"use client";

import { Award, CheckCircle2, ExternalLink, LoaderCircle, RefreshCw, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import {
  apiRequest,
  type LiveCertificate,
  type PaginatedResponse,
  unpackList,
} from "../../lib/api";
import { EmptyState, ErrorState, LoadingState, PageTitle } from "./portal-ui";

export function CertificateReviewPanel() {
  const [certificates, setCertificates] = useState<LiveCertificate[]>([]);
  const [loading, setLoading] = useState(true);
  const [workingId, setWorkingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notes, setNotes] = useState<Record<number, string>>({});

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await apiRequest<PaginatedResponse<LiveCertificate> | LiveCertificate[]>(
        "/certificates/?verification_status=pending&page_size=100",
      );
      setCertificates(unpackList(payload).filter((item) => item.verification_status === "pending"));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Sertifikatlar yuklanmadi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, []);

  const review = async (certificate: LiveCertificate, decision: "verify" | "reject") => {
    const note = notes[certificate.id]?.trim() ?? "";
    if (decision === "reject" && !note) {
      setError("Rad etish sababini kiriting.");
      return;
    }
    setWorkingId(certificate.id);
    setError("");
    try {
      await apiRequest(`/certificates/${certificate.id}/${decision}/`, {
        method: "POST",
        body: JSON.stringify({ note }),
      });
      setCertificates((current) => current.filter((item) => item.id !== certificate.id));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Sertifikat tekshiruvi saqlanmadi.");
    } finally {
      setWorkingId(null);
    }
  };

  return (
    <>
      <PageTitle eyebrow="Sertifikatlar" title="Tekshiruv navbati" description="O‘quvchilar yuborgan hujjatlarni tasdiqlang yoki aniq sabab bilan qaytaring." action={<button className="portal-secondary" onClick={() => void load()}><RefreshCw size={15} /> Yangilash</button>} />
      {error && <div className="admin-flow-message error">{error}</div>}
      {loading ? <LoadingState label="Sertifikatlar yuklanmoqda..." /> : certificates.length ? (
        <div className="certificate-review-grid">
          {certificates.map((certificate) => (
            <article className="portal-card certificate-review-card" key={certificate.id}>
              <div className="certificate-review-head">
                <span><Award size={22} /></span>
                <div><small>{certificate.kind.toUpperCase()}</small><h2>{certificate.title}</h2><p>{certificate.student_detail.full_name}</p></div>
                <strong>{Number(certificate.score)}</strong>
              </div>
              <dl>
                <div><dt>Berilgan sana</dt><dd>{new Date(certificate.issued_at).toLocaleDateString("uz-UZ")}</dd></div>
                <div><dt>Yuborilgan</dt><dd>{new Date(certificate.created_at).toLocaleString("uz-UZ")}</dd></div>
              </dl>
              {certificate.file_url && <a href={certificate.file_url} target="_blank" rel="noreferrer">Hujjatni ochish <ExternalLink size={14} /></a>}
              <label><span>Tekshiruv izohi</span><textarea value={notes[certificate.id] ?? ""} onChange={(event) => setNotes((current) => ({ ...current, [certificate.id]: event.target.value }))} placeholder="Rad etishda sabab majburiy" /></label>
              <div className="certificate-review-actions">
                <button className="reject" onClick={() => void review(certificate, "reject")} disabled={workingId === certificate.id}>{workingId === certificate.id ? <LoaderCircle className="spin" size={16} /> : <XCircle size={16} />} Rad etish</button>
                <button className="approve" onClick={() => void review(certificate, "verify")} disabled={workingId === certificate.id}>{workingId === certificate.id ? <LoaderCircle className="spin" size={16} /> : <CheckCircle2 size={16} />} Tasdiqlash</button>
              </div>
            </article>
          ))}
        </div>
      ) : error ? <ErrorState message={error} onRetry={() => void load()} /> : <EmptyState title="Tekshiruv navbati bo‘sh" description="Yangi sertifikat yuborilganda shu yerda paydo bo‘ladi." icon={Award} />}
    </>
  );
}
