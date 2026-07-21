"use client";

import { Layers3, Plus, Tags } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { createCategory, getCategories, type Category } from "../../lib/profiling-api";

const kindLabels: Record<string, string> = {
  direction: "Ta’lim yo‘nalishi",
  subject_level: "Fan darajasi",
  support: "Qo‘llab-quvvatlash",
  motivation: "Motivatsiya",
  learning_style: "O‘rganish usuli",
  special: "Maxsus holat",
};

export function AdminCategoriesPanel() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [title, setTitle] = useState("");
  const [code, setCode] = useState("");
  const [kind, setKind] = useState("direction");
  const [subjectSlug, setSubjectSlug] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getCategories("page_size=100")
      .then((payload) => setCategories(payload.results))
      .catch((requestError: Error) => setError(requestError.message));
  }, []);

  const groupedCount = useMemo(
    () => new Set(categories.map((category) => category.kind)).size,
    [categories],
  );

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      const item = await createCategory({
        title,
        code,
        kind,
        subject_slug: subjectSlug,
        description: "",
        color: "#071b3a",
        is_active: true,
        order: categories.length + 1,
      });
      setCategories((current) => [...current, item]);
      setTitle("");
      setCode("");
      setSubjectSlug("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Kategoriya yaratilmadi.");
    }
  };

  return (
    <div className="admin-categories-page">
      <div className="admin-page-heading">
        <div>
          <span>Kategoriyalar</span>
          <h1>Profiling teglarini boshqarish</h1>
          <p>Test va roadmap tavsiyalarini aniqlashtiradigan yo‘nalish va darajalarni yarating.</p>
        </div>
        <div className="category-summary-pill">
          <Layers3 size={19} />
          <div><strong>{categories.length}</strong><span>{groupedCount} tur</span></div>
        </div>
      </div>

      {error && <div className="admin-flow-message error">{error}</div>}

      <div className="category-admin-layout">
        <form className="portal-card category-create-card" onSubmit={submit}>
          <div className="category-create-head">
            <span><Plus size={20} /></span>
            <div>
              <h2>Yangi kategoriya</h2>
              <p>Qisqa va tushunarli nom kiriting.</p>
            </div>
          </div>
          <label><span>Nomi</span><input required placeholder="Masalan: Yuqori motivatsiya" value={title} onChange={(e) => setTitle(e.target.value)} /></label>
          <label><span>Kod</span><input required placeholder="high-motivation" value={code} onChange={(e) => setCode(e.target.value.toLowerCase().replace(/[^a-z0-9-]+/g, "-"))} /></label>
          <label><span>Turi</span><select value={kind} onChange={(e) => setKind(e.target.value)}><option value="direction">Ta’lim yo‘nalishi</option><option value="subject_level">Fan darajasi</option><option value="support">Qo‘llab-quvvatlash</option><option value="motivation">Motivatsiya</option><option value="learning_style">O‘rganish usuli</option><option value="special">Maxsus holat</option></select></label>
          <label><span>Fan kodi</span><input value={subjectSlug} onChange={(e) => setSubjectSlug(e.target.value)} placeholder="math, english..." /></label>
          <button className="portal-primary"><Plus size={18} /> Kategoriya qo‘shish</button>
        </form>

        <section className="category-library">
          <div className="category-library-head">
            <div><span>Mavjud teglar</span><h2>Kategoriya kutubxonasi</h2></div>
            <strong>{categories.length} ta</strong>
          </div>
          <div className="category-list-grid">
            {categories.map((category) => (
              <article className="portal-card category-list-card" key={category.id}>
                <span style={{ background: category.color }}><Tags size={19} /></span>
                <div>
                  <strong>{category.title}</strong>
                  <small>{kindLabels[category.kind] ?? category.kind}{category.subject_slug ? ` · ${category.subject_slug}` : ""}</small>
                  <p>{category.code}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
