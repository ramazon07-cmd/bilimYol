"use client";

import { CheckCircle2, LoaderCircle, Plus, X } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import {
  assignStudentCategory,
  completeStudentInterview,
  createStudentGoal,
  createStudentInterview,
  getCategories,
  onboardStudent,
  type Category,
  type StudentProfile,
} from "../../lib/profiling-api";

type Props = {
  onClose: () => void;
  onCreated: (profile: StudentProfile) => void;
};

const initialForm = {
  username: "",
  password: "",
  full_name: "",
  phone: "",
  email: "",
  birth_date: "",
  school_name: "",
  grade: "8",
  region: "Sirdaryo",
  district: "",
  weekly_study_hours: "7",
  guardian_name: "",
  guardian_phone: "",
  guardian_relationship: "Ota-ona",
  goal_type: "presidential_school",
  goal_title: "Prezident maktabiga kirish",
  goal_description: "",
  current_value: "",
  target_value: "",
  target_score: "85",
  target_date: "",
  strengths: "",
  weaknesses: "",
  interests: "",
  main_problem: "",
  motivation_level: "high",
  independence_level: "medium",
  parent_support_level: "high",
  admin_summary: "",
  recommendation: "",
  next_step: "Diagnostik test biriktirish",
};

export function StudentOnboardingWizard({ onClose, onCreated }: Props) {
  const [form, setForm] = useState(initialForm);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getCategories("is_active=true&page_size=100")
      .then((payload) => setCategories(payload.results))
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  const update = (key: keyof typeof initialForm, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (selectedCategories.length === 0) {
      setError("Kamida bitta kategoriya tanlang.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const profile = await onboardStudent({
        username: form.username.trim(),
        password: form.password,
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
        birth_date: form.birth_date || null,
        school_name: form.school_name.trim(),
        grade: Number(form.grade),
        region: form.region.trim(),
        district: form.district.trim(),
        weekly_study_hours: Number(form.weekly_study_hours),
        guardian_name: form.guardian_name.trim(),
        guardian_phone: form.guardian_phone.trim(),
        guardian_relationship: form.guardian_relationship.trim(),
      });

      await createStudentInterview({
        profile: profile.id,
        strengths: form.strengths,
        weaknesses: form.weaknesses,
        interests: form.interests,
        main_problem: form.main_problem,
        motivation_level: form.motivation_level,
        independence_level: form.independence_level,
        parent_support_level: form.parent_support_level,
        admin_summary: form.admin_summary,
        recommendation: form.recommendation,
        next_step: form.next_step,
        answers: [
          { question_key: "main_goal", question_text: "Asosiy maqsading nima?", answer_text: form.goal_title, order: 1 },
          { question_key: "study_time", question_text: "Haftasiga qancha vaqt ajrata oladi?", answer_text: `${form.weekly_study_hours} soat`, order: 2 },
          { question_key: "main_problem", question_text: "Asosiy qiyinchilik nima?", answer_text: form.main_problem, order: 3 },
        ],
      });

      await createStudentGoal({
        profile: profile.id,
        goal_type: form.goal_type,
        title: form.goal_title,
        description: form.goal_description,
        current_value: form.current_value,
        target_value: form.target_value,
        target_score: form.target_score ? Number(form.target_score) : null,
        target_date: form.target_date || null,
        priority: 1,
        is_primary: true,
        is_active: true,
      });

      await Promise.all(selectedCategories.map((category) => assignStudentCategory({
        profile: profile.id,
        category,
        source: "interview",
        confidence: 90,
        note: "Qabul suhbati asosida",
        is_active: true,
      })));

      const completed = await completeStudentInterview(profile.id);
      onCreated(completed);
      onClose();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "O‘quvchini yaratishda xatolik.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-modal-backdrop" role="dialog" aria-modal="true">
      <form className="admin-onboarding-modal" onSubmit={submit}>
        <div className="admin-modal-head">
          <div><span>Yangi qabul</span><h2>O‘quvchi profilingi</h2><p>Admin suhbatdagi barcha muhim ma’lumotlarni bir joyda kiritadi.</p></div>
          <button type="button" onClick={onClose} aria-label="Yopish"><X size={20} /></button>
        </div>

        {error && <div className="admin-flow-message error">{error}</div>}

        <section className="onboarding-section">
          <div className="onboarding-section-title"><span>1</span><div><strong>O‘quvchi va ota-ona</strong><small>Login ham shu yerda yaratiladi.</small></div></div>
          <div className="onboarding-form-grid">
            <label><span>Ism-familiya *</span><input required value={form.full_name} onChange={(e) => update("full_name", e.target.value)} /></label>
            <label><span>Login *</span><input required value={form.username} onChange={(e) => update("username", e.target.value)} /></label>
            <label><span>Vaqtinchalik parol *</span><input required minLength={8} value={form.password} onChange={(e) => update("password", e.target.value)} /></label>
            <label><span>Telefon</span><input value={form.phone} onChange={(e) => update("phone", e.target.value)} /></label>
            <label><span>Tug‘ilgan sana</span><input type="date" value={form.birth_date} onChange={(e) => update("birth_date", e.target.value)} /></label>
            <label><span>Sinf *</span><select value={form.grade} onChange={(e) => update("grade", e.target.value)}>{Array.from({ length: 11 }, (_, i) => i + 1).map((grade) => <option key={grade} value={grade}>{grade}-sinf</option>)}</select></label>
            <label><span>Maktab</span><input value={form.school_name} onChange={(e) => update("school_name", e.target.value)} /></label>
            <label><span>Hudud</span><input value={form.region} onChange={(e) => update("region", e.target.value)} /></label>
            <label><span>Ota-ona ismi *</span><input required value={form.guardian_name} onChange={(e) => update("guardian_name", e.target.value)} /></label>
            <label><span>Ota-ona telefoni *</span><input required value={form.guardian_phone} onChange={(e) => update("guardian_phone", e.target.value)} /></label>
          </div>
        </section>

        <section className="onboarding-section">
          <div className="onboarding-section-title"><span>2</span><div><strong>Maqsad va imkoniyat</strong><small>Roadmap yaratishda ishlatiladi.</small></div></div>
          <div className="onboarding-form-grid">
            <label><span>Maqsad turi</span><select value={form.goal_type} onChange={(e) => update("goal_type", e.target.value)}><option value="presidential_school">Prezident maktabi</option><option value="ielts">IELTS</option><option value="sat">SAT</option><option value="university">Universitet</option><option value="olympiad">Olimpiada</option><option value="school_improvement">Maktab natijasi</option><option value="other">Boshqa</option></select></label>
            <label><span>Asosiy maqsad *</span><input required value={form.goal_title} onChange={(e) => update("goal_title", e.target.value)} /></label>
            <label><span>Hozirgi holati</span><input value={form.current_value} onChange={(e) => update("current_value", e.target.value)} /></label>
            <label><span>Maqsad natijasi</span><input value={form.target_value} onChange={(e) => update("target_value", e.target.value)} /></label>
            <label><span>Maqsad balli</span><input type="number" min="0" max="100" value={form.target_score} onChange={(e) => update("target_score", e.target.value)} /></label>
            <label><span>Maqsad sanasi</span><input type="date" value={form.target_date} onChange={(e) => update("target_date", e.target.value)} /></label>
            <label><span>Haftalik vaqt</span><input type="number" min="1" max="50" value={form.weekly_study_hours} onChange={(e) => update("weekly_study_hours", e.target.value)} /></label>
            <label className="full"><span>Maqsad izohi</span><textarea value={form.goal_description} onChange={(e) => update("goal_description", e.target.value)} /></label>
          </div>
        </section>

        <section className="onboarding-section">
          <div className="onboarding-section-title"><span>3</span><div><strong>Suhbat xulosasi</strong><small>Adminning professional kuzatuvi.</small></div></div>
          <div className="onboarding-form-grid">
            <label><span>Kuchli tomonlari</span><textarea value={form.strengths} onChange={(e) => update("strengths", e.target.value)} /></label>
            <label><span>Zaif tomonlari</span><textarea value={form.weaknesses} onChange={(e) => update("weaknesses", e.target.value)} /></label>
            <label><span>Qiziqishlari</span><textarea value={form.interests} onChange={(e) => update("interests", e.target.value)} /></label>
            <label><span>Asosiy muammo</span><textarea value={form.main_problem} onChange={(e) => update("main_problem", e.target.value)} /></label>
            <label><span>Motivatsiya</span><select value={form.motivation_level} onChange={(e) => update("motivation_level", e.target.value)}><option value="high">Yuqori</option><option value="medium">O‘rta</option><option value="low">Past</option></select></label>
            <label><span>Mustaqillik</span><select value={form.independence_level} onChange={(e) => update("independence_level", e.target.value)}><option value="high">Yuqori</option><option value="medium">O‘rta</option><option value="low">Past</option></select></label>
            <label className="full"><span>Admin xulosasi *</span><textarea required value={form.admin_summary} onChange={(e) => update("admin_summary", e.target.value)} /></label>
            <label><span>Tavsiya</span><textarea value={form.recommendation} onChange={(e) => update("recommendation", e.target.value)} /></label>
            <label><span>Keyingi qadam</span><textarea value={form.next_step} onChange={(e) => update("next_step", e.target.value)} /></label>
          </div>
        </section>

        <section className="onboarding-section">
          <div className="onboarding-section-title"><span>4</span><div><strong>Kategoriyalar</strong><small>Bir o‘quvchiga bir nechta kategoriya biriktiring.</small></div></div>
          <div className="category-checkbox-grid">
            {categories.map((category) => (
              <label key={category.id} className={selectedCategories.includes(category.id) ? "selected" : ""}>
                <input type="checkbox" checked={selectedCategories.includes(category.id)} onChange={() => setSelectedCategories((current) => current.includes(category.id) ? current.filter((id) => id !== category.id) : [...current, category.id])} />
                <span style={{ background: category.color }} />
                <div><strong>{category.title}</strong><small>{category.kind}</small></div>
                {selectedCategories.includes(category.id) && <CheckCircle2 size={17} />}
              </label>
            ))}
          </div>
          {categories.length === 0 && <p className="empty-inline">Avval “Kategoriyalar” sahifasida kategoriya yarating.</p>}
        </section>

        <div className="admin-modal-actions">
          <button type="button" className="portal-secondary" onClick={onClose}>Bekor qilish</button>
          <button className="portal-primary" disabled={loading || categories.length === 0}>
            {loading ? <LoaderCircle className="spin" size={17} /> : <Plus size={17} />}
            Profilni yaratish va suhbatni yakunlash
          </button>
        </div>
      </form>
    </div>
  );
}
