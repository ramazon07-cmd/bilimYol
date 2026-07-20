"use client";

import {
  CheckCircle2,
  ClipboardList,
  Clock3,
  GraduationCap,
  RotateCcw,
  Save,
  UserRound,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  MINI_EXAM_STORAGE_KEY,
  MINI_EXAM_STUDENT_RESULTS_KEY,
  calculateMiniExamSubjectScores,
  miniExamQuestions,
  normalizeCandidate,
  type MiniExamResult,
} from "../lib/mini-exam";

export function AdminTestsPanel({ onComplete }: { onComplete: (result: MiniExamResult) => void }) {
  const [candidate, setCandidate] = useState("");
  const [grade, setGrade] = useState("8-sinf");
  const [started, setStarted] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [error, setError] = useState("");
  const [history, setHistory] = useState<MiniExamResult[]>([]);

  useEffect(() => {
    let savedHistory: MiniExamResult[] = [];
    try {
      const saved = window.localStorage.getItem(MINI_EXAM_STORAGE_KEY);
      if (saved) savedHistory = JSON.parse(saved) as MiniExamResult[];
    } catch {
      savedHistory = [];
    }
    const timer = window.setTimeout(() => setHistory(savedHistory), 0);
    return () => window.clearTimeout(timer);
  }, []);

  const answeredCount = Object.keys(answers).length;
  const score = useMemo(
    () => miniExamQuestions.reduce((total, question) => total + (answers[question.id] === question.correct ? 10 : 0), 0),
    [answers],
  );

  const startExam = () => {
    if (!candidate.trim()) {
      setError("Avval o‘quvchining ism-familiyasini kiriting.");
      return;
    }
    setError("");
    setStarted(true);
    setSubmitted(false);
    setAnswers({});
    window.dispatchEvent(new Event("bilimyol-exam-start"));
  };

  const submitExam = () => {
    if (answeredCount !== miniExamQuestions.length) {
      setError(`Yana ${miniExamQuestions.length - answeredCount} ta savolga javob berilmagan.`);
      return;
    }

    const now = new Date();
    const result: MiniExamResult = {
      id: `${now.getTime()}`,
      candidate: candidate.trim(),
      candidateKey: normalizeCandidate(candidate),
      grade,
      score,
      passed: score >= 60,
      createdAt: new Intl.DateTimeFormat("uz-UZ", { dateStyle: "medium", timeStyle: "short" }).format(now),
      createdAtIso: now.toISOString(),
      correctAnswers: Math.round(score / 10),
      totalQuestions: miniExamQuestions.length,
      subjectScores: calculateMiniExamSubjectScores(answers),
      answers: { ...answers },
    };
    let autoSave = true;
    try {
      const savedSettings = window.localStorage.getItem("bilimyol_system_settings");
      if (savedSettings) autoSave = Boolean((JSON.parse(savedSettings) as { autoSave?: boolean }).autoSave);
    } catch {
      autoSave = true;
    }
    let studentResults: MiniExamResult[] = [];
    try {
      const savedStudentResults = window.localStorage.getItem(MINI_EXAM_STUDENT_RESULTS_KEY);
      if (savedStudentResults) studentResults = JSON.parse(savedStudentResults) as MiniExamResult[];
    } catch {
      studentResults = [];
    }
    const nextStudentResults = [
      result,
      ...studentResults.filter((item) => (item.candidateKey ?? normalizeCandidate(item.candidate)) !== result.candidateKey),
    ].slice(0, 50);
    window.localStorage.setItem(MINI_EXAM_STUDENT_RESULTS_KEY, JSON.stringify(nextStudentResults));

    if (autoSave) {
      const nextHistory = [result, ...history].slice(0, 8);
      setHistory(nextHistory);
      window.localStorage.setItem(MINI_EXAM_STORAGE_KEY, JSON.stringify(nextHistory));
    }
    window.dispatchEvent(new CustomEvent("bilimyol-mini-exam-result", { detail: result }));
    setSubmitted(true);
    setError("");
    onComplete(result);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const resetExam = () => {
    setStarted(false);
    setSubmitted(false);
    setAnswers({});
    setCandidate("");
    setError("");
  };

  if (submitted) {
    return (
      <>
        <div className="portal-page-title">
          <div><span>Qabul mini-imtihoni</span><h1>Imtihon yakunlandi</h1><p>Natija avtomatik hisoblandi va ushbu qurilmada saqlandi.</p></div>
          <button className="portal-primary" onClick={resetExam}><RotateCcw size={17} /> Yangi o‘quvchi</button>
        </div>
        <article className={`portal-card mini-exam-result ${score >= 60 ? "passed" : "failed"}`}>
          <span>{score >= 60 ? <CheckCircle2 size={34} /> : <XCircle size={34} />}</span>
          <div><small>{candidate} · {grade}</small><h2>{score}/100 ball</h2><p>{score >= 60 ? "O‘quvchi boshlang‘ich saralashdan o‘tdi." : "O‘quvchiga qo‘shimcha tayyorgarlik tavsiya qilinadi."}</p></div>
        </article>
        <div className="mini-exam-review">
          {miniExamQuestions.map((question, index) => {
            const isCorrect = answers[question.id] === question.correct;
            return <article className="portal-card" key={question.id}><span className={isCorrect ? "correct" : "wrong"}>{isCorrect ? <CheckCircle2 size={17} /> : <XCircle size={17} />}</span><div><small>{index + 1}-savol · {question.subject}</small><strong>{question.text}</strong><p>Sizning javobingiz: {question.options[answers[question.id]]}</p>{!isCorrect && <em>To‘g‘ri javob: {question.options[question.correct]}</em>}</div></article>;
          })}
        </div>
      </>
    );
  }

  return (
    <>
      <div className="portal-page-title">
        <div><span>Qabul mini-imtihoni</span><h1>O‘quvchini saytda tekshirish</h1><p>Admin kelgan o‘quvchiga shu yerning o‘zida 10 savollik qisqa matematika, ingliz tili va mantiq imtihonini o‘tkazadi.</p></div>
        {started && <div className="mini-exam-progress"><strong>{answeredCount}/10</strong><span>javob berildi</span></div>}
      </div>

      {!started ? (
        <div className="mini-exam-start-grid">
          <article className="portal-card mini-exam-intro">
            <span><ClipboardList size={26} /></span>
            <div><small>Tayyor imtihon</small><h2>BilimYo‘l qabul testi</h2><p>10 ta savol · har biri 10 ball · o‘tish chegarasi 60 ball.</p></div>
            <ul><li><Clock3 size={15} /> Taxminiy vaqt: 10–15 daqiqa</li><li><GraduationCap size={15} /> Natija darhol chiqadi</li><li><Save size={15} /> Oxirgi natijalar saqlanadi</li></ul>
          </article>
          <article className="portal-card mini-exam-candidate">
            <div><span>O‘quvchi ma’lumoti</span><h2>Imtihonni boshlash</h2></div>
            <label>Ism-familiya<input value={candidate} onChange={(event) => setCandidate(event.target.value)} placeholder="Masalan: Bobur Xasanboyev" /></label>
            <label>Sinf<select value={grade} onChange={(event) => setGrade(event.target.value)}><option>5-sinf</option><option>6-sinf</option><option>7-sinf</option><option>8-sinf</option><option>9-sinf</option><option>10-sinf</option></select></label>
            {error && <p className="mini-exam-error">{error}</p>}
            <button className="administer-button" onClick={startExam}><UserRound size={18} /> Imtihonni boshlash</button>
          </article>
        </div>
      ) : (
        <>
          <article className="portal-card mini-exam-candidate-bar"><div><UserRound size={19} /><span><small>O‘quvchi</small><strong>{candidate}</strong></span></div><div><small>Sinf</small><strong>{grade}</strong></div><div><small>O‘tish bali</small><strong>60/100</strong></div><button onClick={resetExam}>Bekor qilish</button></article>
          <div className="mini-exam-questions">
            {miniExamQuestions.map((question, index) => (
              <article className="portal-card mini-question-card" key={question.id}>
                <div className="mini-question-head"><span>{index + 1}</span><div><small>{question.subject}</small><h3>{question.text}</h3></div></div>
                <div className="mini-question-options">
                  {question.options.map((option, optionIndex) => <button key={option} className={answers[question.id] === optionIndex ? "selected" : ""} onClick={() => { setAnswers((current) => ({ ...current, [question.id]: optionIndex })); setError(""); }}><i>{String.fromCharCode(65 + optionIndex)}</i><span>{option}</span>{answers[question.id] === optionIndex && <CheckCircle2 size={17} />}</button>)}
                </div>
              </article>
            ))}
          </div>
          {error && <p className="mini-exam-error sticky-error">{error}</p>}
          <div className="mini-exam-submit"><div><strong>{answeredCount}/10 savol</strong><span>Javoblarning barchasini tekshirib, imtihonni yakunlang.</span></div><button className="portal-primary" onClick={submitExam}><CheckCircle2 size={17} /> Natijani hisoblash</button></div>
        </>
      )}

      {!started && history.length > 0 && <article className="portal-card mini-exam-history"><div className="portal-card-head"><div><span>Saqlangan natijalar</span><h2>Oxirgi mini-imtihonlar</h2></div></div><div>{history.map((result) => <article key={result.id}><span>{result.candidate.split(" ").map((part) => part[0]).slice(0, 2).join("")}</span><div><strong>{result.candidate}</strong><small>{result.grade} · {result.createdAt}</small></div><b>{result.score}/100</b><em className={result.passed ? "passed" : "failed"}>{result.passed ? "O‘tdi" : "O‘tmadi"}</em></article>)}</div></article>}
    </>
  );
}
