"use client";

import { Award, Building2, Check, CheckCircle2, FileCheck2, GraduationCap, Sparkles, Target, Upload } from "lucide-react";
import { useMemo, useState } from "react";
import type { LiveUniversityGoal, WorkspaceSession } from "../lib/api";

const universityOptions = [
  { id: 1, name: "Stanford University", country: "AQSh", short: "SU", targets: { math: 90, english: 85, iq: 85, ielts: 7, sat: 1500 } },
  { id: 2, name: "National University of Singapore", country: "Singapur", short: "NUS", targets: { math: 88, english: 82, iq: 82, ielts: 6.5, sat: 1450 } },
  { id: 3, name: "KAIST", country: "Janubiy Koreya", short: "K", targets: { math: 90, english: 78, iq: 88, ielts: 6.5, sat: 1450 } },
];

type Requirement = { key: string; label: string; current: number; target: number; unit: string; source: "mock" | "certificate"; progress: number; complete: boolean };

function defaultRequirements(universityId: number): Requirement[] {
  const selected = universityOptions.find((item) => item.id === universityId) ?? universityOptions[0];
  const values = { math: 15, english: 56, iq: 54, ielts: 7, sat: 1490 };
  return [
    ["math", "Matematika mock", values.math, selected.targets.math, "ball", "mock"],
    ["english", "English mock", values.english, selected.targets.english, "ball", "mock"],
    ["iq", "IQ mock", values.iq, selected.targets.iq, "ball", "mock"],
    ["ielts", "IELTS Academic", values.ielts, selected.targets.ielts, "band", "certificate"],
    ["sat", "SAT", values.sat, selected.targets.sat, "ball", "certificate"],
  ].map(([key, label, current, target, unit, source]) => {
    const progress = Math.min(100, Math.round((Number(current) / Number(target)) * 100));
    return { key: String(key), label: String(label), current: Number(current), target: Number(target), unit: String(unit), source: source as "mock" | "certificate", progress, complete: progress >= 100 };
  });
}

export function UniversityJourney({ session, title = "Dream University yo‘li", description = "Ota-ona va o‘quvchi birgalikda maqsadni tanlaydi; progress oxirgi mock va tasdiqlangan sertifikatlardan hisoblanadi." }: { session?: WorkspaceSession; title?: string; description?: string }) {
  const liveGoal: LiveUniversityGoal | null = session?.university_goal ?? null;
  const initialId = liveGoal?.university_detail.id ?? 1;
  const [universityId, setUniversityId] = useState(initialId);
  const [saved, setSaved] = useState(false);
  const selected = universityOptions.find((item) => item.id === universityId) ?? universityOptions[0];
  const requirements = useMemo<Requirement[]>(() => {
    if (liveGoal && universityId === initialId) return liveGoal.progress.requirements.map((item) => ({ ...item, source: item.source as "mock" | "certificate" }));
    return defaultRequirements(universityId);
  }, [initialId, liveGoal, universityId]);
  const overall = Math.round(requirements.reduce((sum, item) => sum + item.progress, 0) / requirements.length);

  const save = () => {
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2600);
  };

  return (
    <section className="university-journey">
      <div className="university-title-row">
        <div><span className="university-eyebrow"><GraduationCap size={15} /> Qabul strategiyasi</span><h1>{title}</h1><p>{description}</p></div>
        <label className="university-picker"><small>Dream University</small><select value={universityId} onChange={(event) => setUniversityId(Number(event.target.value))}>{universityOptions.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
      </div>

      <div className="university-hero-card">
        <div className="university-mark">{selected.short}</div>
        <div className="university-name"><span><Building2 size={15} /> {selected.country}</span><h2>{selected.name}</h2><p>2029 qabul maqsadi · Academic track</p></div>
        <div className="university-overall"><div style={{ "--goal-progress": `${overall * 3.6}deg` } as React.CSSProperties}><strong>{overall}%</strong><small>tayyor</small></div><span>Oxirgi mock + sertifikatlar</span></div>
        <div className="university-next"><Sparkles size={18} /><p><strong>Keyingi eng kuchli qadam</strong>Matematika mock natijasini 15 dan kamida 45 ballga olib chiqish.</p></div>
      </div>

      <div className="university-grid">
        <article className="goal-progress-card">
          <div className="goal-card-head"><div><span>Qabul talablari</span><h3>5 ta asosiy indikator</h3></div><em>Yangilandi: oxirgi mock</em></div>
          <div className="goal-requirements">{requirements.map((item) => <div key={item.key} className={item.complete ? "complete" : ""}><span className="goal-source">{item.source === "certificate" ? <Award size={17} /> : <FileCheck2 size={17} />}</span><div><strong>{item.label}</strong><small>{item.source === "certificate" ? "Tasdiqlangan sertifikat" : "18-iyuldagi mock natijasi"}</small><i><b style={{ width: `${item.progress}%` }} /></i></div><p><strong>{item.current}</strong><span>/ {item.target} {item.unit}</span></p><em>{item.complete ? <><CheckCircle2 size={14} /> Tayyor</> : `${item.progress}%`}</em></div>)}</div>
        </article>

        <aside className="certificate-stack">
          <article><div className="certificate-head"><span><Award size={19} /></span><div><small>Tasdiqlangan sertifikat</small><h3>IELTS Academic</h3></div><em><Check size={13} /> Verified</em></div><strong>7.0 <small>band</small></strong><p>Talab: {selected.targets.ielts} · progress avtomatik 100%</p></article>
          <article><div className="certificate-head"><span><Award size={19} /></span><div><small>Tasdiqlangan sertifikat</small><h3>SAT</h3></div><em><Check size={13} /> Verified</em></div><strong>1490 <small>/1600</small></strong><p>Talab: {selected.targets.sat} · natija hisobga olindi</p></article>
          <button className="certificate-upload" onClick={save}><Upload size={17} /> Sertifikat qo‘shish</button>
        </aside>
      </div>

      <div className="university-actions"><div><Target size={19} /><p><strong>Maqsad oila bilan boshqariladi.</strong> Universitet o‘zgarsa, mezon va progress darhol qayta hisoblanadi.</p></div><button onClick={save}>{saved ? <><Check size={16} /> Saqlandi</> : "Maqsadni saqlash"}</button></div>
    </section>
  );
}
