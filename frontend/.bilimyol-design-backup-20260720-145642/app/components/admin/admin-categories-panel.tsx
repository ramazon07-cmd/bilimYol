"use client";

import { Plus, Tags } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { createCategory, getCategories, type Category } from "../../lib/profiling-api";

export function AdminCategoriesPanel() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [title, setTitle] = useState("");
  const [code, setCode] = useState("");
  const [kind, setKind] = useState("direction");
  const [subjectSlug, setSubjectSlug] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { getCategories("page_size=100").then((payload) => setCategories(payload.results)).catch((requestError: Error) => setError(requestError.message)); }, []);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError("");
    try { const item = await createCategory({ title, code, kind, subject_slug: subjectSlug, description: "", color: "#071b3a", is_active: true, order: categories.length + 1 }); setCategories((current) => [...current, item]); setTitle(""); setCode(""); setSubjectSlug(""); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Kategoriya yaratilmadi."); }
  };
  return <div><div className="admin-page-heading"><div><span>Kategoriyalar</span><h1>Profiling teglarini boshqarish</h1><p>Yo‘nalish, fan darajasi, motivatsiya va qo‘llab-quvvatlash turlari.</p></div></div>{error && <div className="admin-flow-message error">{error}</div>}<div className="category-admin-layout"><form className="portal-card category-create-card" onSubmit={submit}><h2>Yangi kategoriya</h2><label><span>Nomi</span><input required value={title} onChange={(e) => setTitle(e.target.value)} /></label><label><span>Kod</span><input required value={code} onChange={(e) => setCode(e.target.value.toLowerCase().replace(/[^a-z0-9-]+/g, "-"))} /></label><label><span>Turi</span><select value={kind} onChange={(e) => setKind(e.target.value)}><option value="direction">Ta’lim yo‘nalishi</option><option value="subject_level">Fan darajasi</option><option value="support">Qo‘llab-quvvatlash</option><option value="motivation">Motivatsiya</option><option value="learning_style">O‘rganish usuli</option><option value="special">Maxsus holat</option></select></label><label><span>Fan slug</span><input value={subjectSlug} onChange={(e) => setSubjectSlug(e.target.value)} placeholder="math, english..." /></label><button className="portal-primary"><Plus size={16} /> Qo‘shish</button></form><div className="category-list-grid">{categories.map((category) => <article className="portal-card" key={category.id}><span style={{ background: category.color }}><Tags size={18} /></span><div><strong>{category.title}</strong><small>{category.kind}{category.subject_slug ? ` · ${category.subject_slug}` : ""}</small><p>{category.code}</p></div></article>)}</div></div></div>;
}
