# RBIS Academic Diagnostic

Prezident maktabiga tayyorgarlik uchun sinfga mos testlarni boshqaradigan, natijani fan, mavzu va ko‘nikma bo‘yicha tahlil qiladigan, o‘quvchiga shaxsiy roadmap hamda Dream University progressini ko‘rsatadigan full-stack MVP.

## RBIS dizayn tizimi

Login, admin, student, teacher, parent va PDF/chop etish ko‘rinishlari bitta
RBIS komponentlar tizimidan foydalanadi. Asosiy tokenlar
`frontend/app/lib/rbis-theme.ts`da, umumiy UI standartlari esa
`frontend/app/globals.css`da saqlanadi.

```bash
cd frontend
npm run lint:theme
```

Bu audit barcha 11 ta RBIS rang tokeni mavjudligini, eski ko‘k/navy asosiy
ranglar qaytib kelmaganini va sidebar, tugma, card, jadval, modal hamda print
standartlari saqlanganini tekshiradi.

## Texnologiyalar

- Frontend: Next.js-compatible Vinext, React 19, TypeScript, Lucide icons, custom SVG charts
- Backend: Django 5.2, Django REST Framework, SimpleJWT
- Database: SQLite development uchun, PostgreSQL production uchun
- API hujjati: drf-spectacular / Swagger

## Loyiha tarkibi

```text
frontend/             React frontend, sahifalar va API client
  app/                 Diagnostika interfeysi
  public/              Statik fayllar
backend/               Django REST API
  apps/accounts/      4 rol, sinf va ota-ona bog‘lanishi
  apps/academics/     Fan, mavzu, ko‘nikma, savol va imtihon
  apps/diagnostics/   Attempt, tahlil, hisobot va roadmap engine
  apps/pathways/      Dream University, sertifikatlar va qabul progressi
```

## 1. Backendni ishga tushirish

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

API: `http://localhost:8000/api/`  
Swagger: `http://localhost:8000/api/docs/`

Demo foydalanuvchilar faqat lokal `DEBUG=True` muhitida yaratiladi:

| Rol | Login | Parol |
|---|---|---|
| Admin | `admin` | `admin12345` |
| O‘qituvchi | `teacher` | `teacher123` |
| O‘quvchi | `student` | `student123` |
| Ota-ona | `parent` | `parent123` |

## 2. Frontendni ishga tushirish

Frontend alohida papkada ishlaydi:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Ichki frontend demo rejimi default holatda o‘chiq. Faqat lokal UI demo kerak bo‘lsa
`NEXT_PUBLIC_ENABLE_DEMO_MODE=true` qo‘ying. Productionda haqiqiy API va alohida
foydalanuvchi hisoblaridan foydalaning.

## 4 ta rol uchun kabinetlar

- **O‘quvchi:** diagnostik hisobot, fan tahlili, savollar va shaxsiy roadmap. Admin o‘tkazgan mini-imtihon natijasi aynan Umumiy diagnostik xulosa sahifasida ochiladi; bu rejimda Dream University ko‘rsatilmaydi.
- **Ota-ona:** farzand natijalari, haftalik vazifalar, Dream University tanlovi, sertifikat progressi va o‘qituvchi bilan xabarlar.
- **O‘qituvchi:** sinf diagnostikasi, o‘quvchilar jadvali, roadmap tasdiqlash va topshiriqlar.
- **Administrator:** kelgan o‘quvchidan 10 savollik Math/English/IQ mini-imtihonini olish, natijani darhol Student Portalning Umumiy hisobotiga uzatish, foydalanuvchilar va tizim sozlamalari.

## Sinf testlari va 100 ballik shkala

- Har bir test aniq bir sinf va grade bilan bog‘lanadi.
- Test paketida `IQ`, `Math` va `English` fanlari mavjud.
- Har bir fan natijasi alohida `100/100` shkala bo‘yicha normallashtiriladi.
- Umumiy natija fan og‘irliklari asosida yana `100/100` ko‘rinishida hisoblanadi.
- Admin `Butun sinf` yoki `Bitta o‘quvchi` rejimini tanlab testni ochishi mumkin.

## Admin mini-imtihoni natijasi

- Kabinet topbaridagi toggle tugma chap sidebarni istalgan payt ochib-yopadi.
- Admin `Imtihonni boshlash` tugmasini bosishi bilan sidebar avtomatik yopilib, savollar uchun keng ekran ochiladi.
- Sidebar holati brauzerda saqlanadi va toggle orqali qayta ochiladi.
- Admin `Natijani hisoblash` tugmasini bosishi bilan o‘sha nomzodning Student Portal hisobotiga o‘tadi.
- Dastlab **Umumiy** bo‘limi ochiladi.
- Yuqori menyuda faqat **Umumiy, Matematika, Ingliz tili va IQ** ko‘rsatiladi.
- Nomzod, sinf, umumiy ball, to‘g‘ri javoblar va fanlar kesimidagi ballar 10 savollik testdan olinadi.
- Ushbu natija rejimida **Dream University** va alohida **Qabul testi** menyusi ko‘rsatilmaydi.

## Dream University progressi

- Ota-ona va o‘quvchi bitta umumiy universitet maqsadini boshqaradi.
- Math, English va IQ progressi o‘quvchining eng oxirgi mock hisobotidan olinadi.
- IELTS va SAT progressi faqat administrator tasdiqlagan (`verified`) sertifikatdan olinadi.
- Sertifikat universitet talabiga yetsa, shu talab avtomatik `100% · Tayyor` bo‘ladi.
- Universitet o‘zgarsa, uning maqsad ballari asosida progress qayta hisoblanadi.

Login sahifasi demo login va parollarni avtomatik to‘ldirmaydi. Live API ishlaganda
kabinet backend qaytargan haqiqiy foydalanuvchi roli asosida ochiladi.

## Asosiy API oqimi

1. `POST /api/auth/token/` — JWT olish
2. `GET /api/assignments/` — biriktirilgan imtihonlar
3. `POST /api/assignments/{id}/start/` — urinishni boshlash
4. `POST /api/attempts/{id}/answer/` — javobni avtomatik saqlash
5. `POST /api/attempts/{id}/submit/` — testni yakunlash va hisobot yaratish
6. `GET /api/reports/` — diagnostik hisobotlar
7. `POST /api/roadmaps/{id}/approve/` — o‘qituvchi roadmapni tasdiqlashi
8. `GET /api/exams/by-class/?classroom={id}` — sinfga mos testlarni olish
9. `POST /api/exams/{id}/assign-class/` — testni butun sinfga biriktirish
10. `POST /api/exams/{id}/assign-student/` — testni bitta o‘quvchiga biriktirish
11. `GET/PATCH /api/university-goals/` — Dream University maqsadi va live progress
12. `POST /api/certificates/` — sertifikat kiritish
13. `POST /api/certificates/{id}/verify/` — admin sertifikatni tasdiqlashi

## Testlar

```bash
cd backend
python manage.py test
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Production uchun

- `.env` ichida kuchli `SECRET_KEY` kiriting.
- `DATABASE_URL` orqali PostgreSQL ulang.
- `DEBUG=False` va aniq `ALLOWED_HOSTS` o‘rnating.
- Frontendda `NEXT_PUBLIC_API_BASE_URL=https://api-domeningiz.uz/api` kiriting.
- `NEXT_PUBLIC_ENABLE_DEMO_MODE=false` qoldiring va production bazada eski demo hisoblar bo‘lsa, ularni o‘chiring yoki parollarini almashtiring.
