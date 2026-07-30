"use client";

import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Goal,
  LoaderCircle,
  MessageSquareText,
  Plus,
  Tags,
  UserRound,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

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
import { rbisChartColor } from "../../lib/rbis-theme";

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

const steps = [
  {
    title: "O‘quvchi",
    description: "Shaxsiy va ota-ona ma’lumotlari",
    icon: UserRound,
  },
  {
    title: "Maqsad",
    description: "Natija, muddat va imkoniyat",
    icon: Goal,
  },
  {
    title: "Suhbat",
    description: "Admin kuzatuvi va xulosasi",
    icon: MessageSquareText,
  },
  {
    title: "Kategoriya",
    description: "Profiling teglarini tanlash",
    icon: Tags,
  },
] as const;

export function StudentOnboardingWizard({ onClose, onCreated }: Props) {
  const [form, setForm] = useState(initialForm);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<number[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
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

  const stepProgress = useMemo(
    () => `${Math.round(((currentStep + 1) / steps.length) * 100)}%`,
    [currentStep],
  );

  const validateCurrentStep = () => {
    if (currentStep === 0) {
      if (!form.full_name.trim() || !form.username.trim() || form.password.length < 8) {
        setError("Ism, login va kamida 8 belgili vaqtinchalik parolni kiriting.");
        return false;
      }
      if (!form.guardian_name.trim() || !form.guardian_phone.trim()) {
        setError("Ota-ona ismi va telefon raqamini kiriting.");
        return false;
      }
    }

    if (currentStep === 1) {
      if (!form.goal_title.trim()) {
        setError("O‘quvchining asosiy maqsadini kiriting.");
        return false;
      }

      const weeklyHours = Number(form.weekly_study_hours);
      if (!Number.isFinite(weeklyHours) || weeklyHours < 1 || weeklyHours > 50) {
        setError("Haftalik vaqt 1 dan 50 soatgacha bo‘lishi kerak.");
        return false;
      }

      const targetScore = Number(form.target_score);
      if (form.target_score && (!Number.isFinite(targetScore) || targetScore < 0 || targetScore > 100)) {
        setError("Maqsad balli 0 dan 100 gacha bo‘lishi kerak.");
        return false;
      }
    }

    if (currentStep === 2 && !form.admin_summary.trim()) {
      setError("Suhbat bo‘yicha admin xulosasini kiriting.");
      return false;
    }

    if (currentStep === 3 && selectedCategories.length === 0) {
      setError("Kamida bitta kategoriya tanlang.");
      return false;
    }

    setError("");
    return true;
  };

  const goNext = () => {
    if (!validateCurrentStep()) return;
    setCurrentStep((step) => Math.min(step + 1, steps.length - 1));
  };

  const goBack = () => {
    setError("");
    setCurrentStep((step) => Math.max(step - 1, 0));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (currentStep !== steps.length - 1) {
      goNext();
      return;
    }
    if (!validateCurrentStep()) return;

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
        weekly_study_hours: Math.min(50, Math.max(1, Number(form.weekly_study_hours))),
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

      await Promise.all(
        selectedCategories.map((category) =>
          assignStudentCategory({
            profile: profile.id,
            category,
            source: "interview",
            confidence: 90,
            note: "Qabul suhbati asosida",
            is_active: true,
          }),
        ),
      );

      const completed = await completeStudentInterview(profile.id);
      onCreated(completed);
      onClose();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "O‘quvchini yaratishda xatolik.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-modal-backdrop" role="dialog" aria-modal="true">
      <form className="admin-onboarding-modal" onSubmit={submit}>
        <header className="admin-modal-head">
          <div>
            <span>Yangi qabul</span>
            <h2>O‘quvchi profilingi</h2>
            <p>Ma’lumotlarni to‘rt qisqa bosqichda kiriting.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Yopish">
            <X size={20} />
          </button>
        </header>

        <div className="onboarding-stepper" aria-label="Profiling bosqichlari">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const state = index < currentStep ? "done" : index === currentStep ? "active" : "";
            return (
              <button
                type="button"
                key={step.title}
                className={state}
                onClick={() => index <= currentStep && setCurrentStep(index)}
                disabled={index > currentStep}
              >
                <i>{index < currentStep ? <CheckCircle2 size={18} /> : <Icon size={18} />}</i>
                <span>
                  <strong>{step.title}</strong>
                  <small>{step.description}</small>
                </span>
              </button>
            );
          })}
          <div className="onboarding-progress"><i style={{ width: stepProgress }} /></div>
        </div>

        <div className="admin-modal-body">
          {error && <div className="admin-flow-message error">{error}</div>}

          {currentStep === 0 && (
            <section className="onboarding-panel">
              <div className="onboarding-panel-heading">
                <span>01</span>
                <div>
                  <h3>O‘quvchi va ota-ona</h3>
                  <p>Akkaunt va asosiy aloqa ma’lumotlarini kiriting.</p>
                </div>
              </div>
              <div className="onboarding-form-grid">
                <label><span>Ism-familiya *</span><input autoFocus required value={form.full_name} onChange={(e) => update("full_name", e.target.value)} /></label>
                <label><span>Login *</span><input required value={form.username} onChange={(e) => update("username", e.target.value)} /></label>
                <label><span>Vaqtinchalik parol *</span><input type="password" required minLength={8} value={form.password} onChange={(e) => update("password", e.target.value)} /></label>
                <label><span>Telefon</span><input value={form.phone} onChange={(e) => update("phone", e.target.value)} /></label>
                <label><span>Email</span><input type="email" value={form.email} onChange={(e) => update("email", e.target.value)} /></label>
                <label><span>Tug‘ilgan sana</span><input type="date" value={form.birth_date} onChange={(e) => update("birth_date", e.target.value)} /></label>
                <label><span>Sinf *</span><select value={form.grade} onChange={(e) => update("grade", e.target.value)}>{Array.from({ length: 11 }, (_, i) => i + 1).map((grade) => <option key={grade} value={grade}>{grade}-sinf</option>)}</select></label>
                <label><span>Maktab</span><input value={form.school_name} onChange={(e) => update("school_name", e.target.value)} /></label>
                <label><span>Hudud</span><input value={form.region} onChange={(e) => update("region", e.target.value)} /></label>
                <label><span>Tuman / shahar</span><input value={form.district} onChange={(e) => update("district", e.target.value)} /></label>
                <label><span>Ota-ona ismi *</span><input required value={form.guardian_name} onChange={(e) => update("guardian_name", e.target.value)} /></label>
                <label><span>Ota-ona telefoni *</span><input required value={form.guardian_phone} onChange={(e) => update("guardian_phone", e.target.value)} /></label>
              </div>
            </section>
          )}

          {currentStep === 1 && (
            <section className="onboarding-panel">
              <div className="onboarding-panel-heading">
                <span>02</span>
                <div>
                  <h3>Maqsad va imkoniyat</h3>
                  <p>Roadmap nimaga va qachongacha olib borishini belgilang.</p>
                </div>
              </div>
              <div className="onboarding-form-grid">
                <label><span>Maqsad turi</span><select value={form.goal_type} onChange={(e) => update("goal_type", e.target.value)}><option value="presidential_school">Prezident maktabi</option><option value="ielts">IELTS</option><option value="sat">SAT</option><option value="university">Universitet</option><option value="olympiad">Olimpiada</option><option value="school_improvement">Maktab natijasi</option><option value="other">Boshqa</option></select></label>
                <label><span>Asosiy maqsad *</span><input required value={form.goal_title} onChange={(e) => update("goal_title", e.target.value)} /></label>
                <label><span>Hozirgi holati</span><input value={form.current_value} onChange={(e) => update("current_value", e.target.value)} /></label>
                <label><span>Maqsad natijasi</span><input value={form.target_value} onChange={(e) => update("target_value", e.target.value)} /></label>
                <label><span>Maqsad balli</span><input type="number" min="0" max="100" value={form.target_score} onChange={(e) => update("target_score", e.target.value)} /></label>
                <label><span>Maqsad sanasi</span><input type="date" value={form.target_date} onChange={(e) => update("target_date", e.target.value)} /></label>
                <label><span>Haftalik vaqt</span><input type="number" min="1" max="50" step="1" inputMode="numeric" value={form.weekly_study_hours} onChange={(e) => update("weekly_study_hours", e.target.value)} onBlur={() => { const value = Number(form.weekly_study_hours); if (Number.isFinite(value)) update("weekly_study_hours", String(Math.min(50, Math.max(1, value)))); }} /></label>
                <label className="full"><span>Maqsad izohi</span><textarea value={form.goal_description} onChange={(e) => update("goal_description", e.target.value)} placeholder="Nega bu maqsad muhim va qanday natija kutilmoqda?" /></label>
              </div>
            </section>
          )}

          {currentStep === 2 && (
            <section className="onboarding-panel">
              <div className="onboarding-panel-heading">
                <span>03</span>
                <div>
                  <h3>Suhbat xulosasi</h3>
                  <p>O‘quvchining kuchi, muammosi va nazorat ehtiyojini yozing.</p>
                </div>
              </div>
              <div className="onboarding-form-grid">
                <label><span>Kuchli tomonlari</span><textarea value={form.strengths} onChange={(e) => update("strengths", e.target.value)} /></label>
                <label><span>Zaif tomonlari</span><textarea value={form.weaknesses} onChange={(e) => update("weaknesses", e.target.value)} /></label>
                <label><span>Qiziqishlari</span><textarea value={form.interests} onChange={(e) => update("interests", e.target.value)} /></label>
                <label><span>Asosiy muammo</span><textarea value={form.main_problem} onChange={(e) => update("main_problem", e.target.value)} /></label>
                <label><span>Motivatsiya</span><select value={form.motivation_level} onChange={(e) => update("motivation_level", e.target.value)}><option value="high">Yuqori</option><option value="medium">O‘rta</option><option value="low">Past</option></select></label>
                <label><span>Mustaqillik</span><select value={form.independence_level} onChange={(e) => update("independence_level", e.target.value)}><option value="high">Yuqori</option><option value="medium">O‘rta</option><option value="low">Past</option></select></label>
                <label><span>Ota-ona qo‘llovi</span><select value={form.parent_support_level} onChange={(e) => update("parent_support_level", e.target.value)}><option value="high">Yuqori</option><option value="medium">O‘rta</option><option value="low">Past</option></select></label>
                <label><span>Keyingi qadam</span><input value={form.next_step} onChange={(e) => update("next_step", e.target.value)} /></label>
                <label className="full"><span>Admin xulosasi *</span><textarea required value={form.admin_summary} onChange={(e) => update("admin_summary", e.target.value)} placeholder="Professional yakuniy xulosani yozing..." /></label>
                <label className="full"><span>Tavsiya</span><textarea value={form.recommendation} onChange={(e) => update("recommendation", e.target.value)} /></label>
              </div>
            </section>
          )}

          {currentStep === 3 && (
            <section className="onboarding-panel">
              <div className="onboarding-panel-heading">
                <span>04</span>
                <div>
                  <h3>Kategoriyalar</h3>
                  <p>Mos test va roadmap tavsiyasi uchun teglarni tanlang.</p>
                </div>
              </div>
              <div className="category-checkbox-grid">
                {categories.map((category, index) => (
                  <label key={category.id} className={selectedCategories.includes(category.id) ? "selected" : ""}>
                    <input type="checkbox" checked={selectedCategories.includes(category.id)} onChange={() => setSelectedCategories((current) => current.includes(category.id) ? current.filter((id) => id !== category.id) : [...current, category.id])} />
                    <span style={{ background: rbisChartColor(category.code, index) }} />
                    <div><strong>{category.title}</strong><small>{category.kind.replaceAll("_", " ")}</small></div>
                    {selectedCategories.includes(category.id) && <CheckCircle2 size={19} />}
                  </label>
                ))}
              </div>
              {categories.length === 0 && <p className="empty-inline">Avval “Kategoriyalar” sahifasida kategoriya yarating.</p>}
            </section>
          )}
        </div>

        <footer className="admin-modal-actions">
          <div className="modal-step-copy">
            <strong>{currentStep + 1}/{steps.length}</strong>
            <span>{steps[currentStep].title}</span>
          </div>
          <div className="modal-action-buttons">
            {currentStep > 0 && (
              <button type="button" className="portal-secondary" onClick={goBack}>
                <ChevronLeft size={18} /> Orqaga
              </button>
            )}
            {currentStep === 0 && (
              <button type="button" className="portal-secondary" onClick={onClose}>
                Bekor qilish
              </button>
            )}
            {currentStep < steps.length - 1 ? (
              <button type="button" className="portal-primary" onClick={goNext}>
                Davom etish <ChevronRight size={18} />
              </button>
            ) : (
              <button className="portal-primary" disabled={loading || categories.length === 0}>
                {loading ? <LoaderCircle className="spin" size={18} /> : <Plus size={18} />}
                Profilni yaratish
              </button>
            )}
          </div>
        </footer>
      </form>
    </div>
  );
}
