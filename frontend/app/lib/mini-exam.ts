export type MiniExamSubject = "math" | "english" | "logic";

export type MiniExamQuestion = {
  id: number;
  subject: "Matematika" | "Ingliz tili" | "Mantiq";
  subjectId: MiniExamSubject;
  text: string;
  options: string[];
  correct: number;
};

export type MiniExamSubjectScores = Record<MiniExamSubject, number>;

export type MiniExamResult = {
  id: string;
  candidate: string;
  candidateKey?: string;
  grade: string;
  score: number;
  passed: boolean;
  createdAt: string;
  createdAtIso?: string;
  correctAnswers?: number;
  totalQuestions?: number;
  subjectScores?: MiniExamSubjectScores;
  answers?: Record<number, number>;
};

export const MINI_EXAM_STORAGE_KEY = "bilimyol_admin_mini_exam_results";
export const MINI_EXAM_STUDENT_RESULTS_KEY = "bilimyol_student_mini_exam_results";

export const miniExamQuestions: MiniExamQuestion[] = [
  { id: 1, subject: "Matematika", subjectId: "math", text: "12 + 8 nechaga teng?", options: ["18", "20", "22", "24"], correct: 1 },
  { id: 2, subject: "Matematika", subjectId: "math", text: "5 × 6 nechaga teng?", options: ["25", "28", "30", "35"], correct: 2 },
  { id: 3, subject: "Mantiq", subjectId: "logic", text: "Qaysi son toq son?", options: ["12", "16", "17", "20"], correct: 2 },
  { id: 4, subject: "Mantiq", subjectId: "logic", text: "Ketma-ketlikni davom ettiring: 2, 4, 8, 16, ...", options: ["18", "24", "30", "32"], correct: 3 },
  { id: 5, subject: "Ingliz tili", subjectId: "english", text: '"Book" so‘zining o‘zbekcha tarjimasi qaysi?', options: ["Daftar", "Kitob", "Qalam", "Maktab"], correct: 1 },
  { id: 6, subject: "Ingliz tili", subjectId: "english", text: "To‘g‘ri gapni tanlang.", options: ["She go to school.", "She goes to school.", "She going school.", "She gone to school."], correct: 1 },
  { id: 7, subject: "Ingliz tili", subjectId: "english", text: '"Difficult" so‘zining antonimi qaysi?', options: ["Hard", "Easy", "Long", "Fast"], correct: 1 },
  { id: 8, subject: "Mantiq", subjectId: "logic", text: "Barcha qalamlar yozuv quroli. Ko‘k buyum qalam bo‘lsa, u nima?", options: ["Kitob", "Yozuv quroli", "Daftar", "Aniqlab bo‘lmaydi"], correct: 1 },
  { id: 9, subject: "Matematika", subjectId: "math", text: "3x + 2 = 11 bo‘lsa, x nechaga teng?", options: ["2", "3", "4", "5"], correct: 1 },
  { id: 10, subject: "Matematika", subjectId: "math", text: "1 soat 30 daqiqa jami necha daqiqa?", options: ["60", "80", "90", "100"], correct: 2 },
];

export function normalizeCandidate(value: string) {
  return value
    .trim()
    .toLocaleLowerCase("uz-UZ")
    .replace(/[ʻ’`']/g, "'")
    .replace(/\s+/g, " ");
}

export function calculateMiniExamSubjectScores(answers: Record<number, number>): MiniExamSubjectScores {
  const subjects: MiniExamSubject[] = ["math", "english", "logic"];
  return subjects.reduce<MiniExamSubjectScores>((scores, subjectId) => {
    const subjectQuestions = miniExamQuestions.filter((question) => question.subjectId === subjectId);
    const correct = subjectQuestions.filter((question) => answers[question.id] === question.correct).length;
    scores[subjectId] = Math.round((correct / subjectQuestions.length) * 100);
    return scores;
  }, { math: 0, english: 0, logic: 0 });
}

export function hydrateMiniExamResult(result: MiniExamResult): MiniExamResult {
  if (result.subjectScores && result.answers) return result;
  const answers = result.answers ?? {};
  return {
    ...result,
    candidateKey: result.candidateKey ?? normalizeCandidate(result.candidate),
    correctAnswers: result.correctAnswers ?? Math.round(result.score / 10),
    totalQuestions: result.totalQuestions ?? miniExamQuestions.length,
    subjectScores: result.subjectScores ?? calculateMiniExamSubjectScores(answers),
    answers,
  };
}
