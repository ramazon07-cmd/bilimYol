import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import test from "node:test";

async function compiledPageSource() {
  const directory = new URL("../dist/server/ssr/assets/", import.meta.url);
  const files = await readdir(directory);
  const pageFile = files.find((file) => file.startsWith("page-") && file.endsWith(".js"));
  assert.ok(pageFile, "Compiled page asset was not generated");
  return readFile(new URL(pageFile, directory), "utf8");
}

test("production build contains the working parent, teacher, and admin flows", async () => {
  const source = await compiledPageSource();
  assert.match(source, /BilimYo‘l akademik bo‘limi/);
  assert.match(source, /Tasdiqlandi/);
  assert.match(source, /O‘quvchini saytda tekshirish/);
  assert.match(source, /10 ta savol/);
  assert.match(source, /Oddiy tizim sozlamalari/);
  assert.match(source, /tel:0000/);
  assert.match(source, /Umumiy diagnostik/);
  assert.match(source, /10 savollik mini-imtihon/);
  assert.match(source, /Matematika 4 savol/);
  assert.match(source, /bilimyol_admin_mini_exam_results/);
  assert.match(source, /bilimyol_student_mini_exam_results/);
  assert.doesNotMatch(source, /O‘quvchi test natijasi/);
  assert.match(source, /Admin kabinetiga qaytish/);
  assert.match(source, /Yon menyuni yopish/);
  assert.match(source, /Yon menyuni ochish/);
  assert.match(source, /bilimyol-exam-start/);
  assert.match(source, /bilimyol_sidebar_open/);
});
