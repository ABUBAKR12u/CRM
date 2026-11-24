# ai-ops-platform

Korxona rahbari va xodimlari uchun AI biznes operatsion platformasi: rolga qarab ishlaydigan boshqaruv paneli. Next.js 16 (App Router), TypeScript `strict`, Tailwind CSS 4 va Ant Design 6 asosida. Uch rol (admin, rahbar, xodim), uch til (o'zbek, rus, ingliz), Light/Dark rejim, serverda tekshiriladigan ruxsatlar. Ma'lumotlar va biznes qoidalari Python backendda (`../backend`, FastAPI + PostgreSQL).

## Hisobotlar

- [Hafta 1 hisobi](./docs/weekly/hafta-1.md)
- [Hafta 2 hisobi](./docs/weekly/hafta-2.md)
- [Hafta 3 hisobi](./docs/weekly/hafta-3.md)
- [Hafta 4 hisobi](./docs/weekly/hafta-4.md)

## Loyiha tuzilmasi

```
src/
├── app/
│   ├── [locale]/(auth)/        # Login, parolni unutdim, yangi parol
│   ├── [locale]/(app)/         # Himoyalangan panel (dashboard, vazifalar, foydalanuvchilar, jamoa...)
│   └── api/
│       ├── auth/               # login, logout, forgot-password, reset-password, session-expired
│       ├── notifications/      # Bildirishnomalar (backend proksisi)
│       ├── users/              # Foydalanuvchilar API (backend proksisi)
│       └── tasks/              # Vazifalar API (backend proksisi)
├── components/
│   ├── ui/                     # Modal, ConfirmDialog, DataTable, forma maydonlari, Badge, Toast, Popover
│   ├── layout/                 # AppShell, Sidebar, Header, Breadcrumbs, CommandPalette, bildirishnomalar
│   ├── auth/                   # Login va parol formalari
│   ├── users/ tasks/ team/     # Sahifa komponentlari
│   └── providers/              # Mavzu va Ant Design provayderlari
├── i18n/                       # next-intl sozlamalari (uz, ru, en)
├── lib/
│   ├── auth/                   # Rollar, token, sessiya, Zod sxemalari
│   ├── api/                    # API himoyasi: aktyor, limit, javoblar
│   ├── backend.ts              # Backend bilan yagona aloqa nuqtasi (server-only)
│   ├── data/                   # Backend adapteri (service.ts) va turlar
│   └── schemas/                # Umumiy Zod sxemalari
├── messages/                   # uz.json, ru.json, en.json
└── proxy.ts                    # Til + sessiya + rol himoyasi
e2e/                            # Playwright testlari (kirish, navigatsiya, API, axe, responsive)
scripts/                        # check-i18n.mjs (tarjimalar to'liqligi)
docs/weekly/                    # Haftalik hisobotlar
```

## Ishni boshlash

1. Bog'liqliklarni o'rnatish:

   ```bash
   npm install
   ```

2. Sozlama faylini yaratish va maxfiy kalitni yozish (kamida 32 belgi):

   ```bash
   cp .env.example .env.local
   node -e "console.log(require('crypto').randomBytes(48).toString('base64url'))"
   ```

   Chiqqan kalitni `.env.local` dagi `SESSION_SECRET=` dan keyin qo'ying.

3. Tekshiruv:

   ```bash
   npm run typecheck
   npm run lint
   npm run check:i18n
   ```

4. Ilovani ishga tushirish:

   ```bash
   npm run dev
   ```

   Brauzerda `http://localhost:3000` ochiladi va `/uz/login` ga yo'naltiradi.

## Demo hisoblar

Rol login formasida tanlanmaydi, email va paroldan avtomatik aniqlanadi.

| Rol    | Email               | Parol           |
| ------ | ------------------- | --------------- |
| Admin  | `admin@aiops.uz`    | `Admin#2026`    |
| Rahbar | `manager@aiops.uz`  | `Manager#2026`  |
| Xodim  | `employee@aiops.uz` | `Employee#2026` |

Hisoblarni backend seed'i yaratadi (`python -m app.utils.seed`, production'da ishlamaydi). Login sahifasidagi ro'yxat dev'da doim, production build'da faqat `SHOW_DEMO_ACCOUNTS=true` bo'lsa ko'rinadi. **Ochiq internetga chiqariladigan muhitda buni yoqmang.**

## Rollar

- **Admin:** barcha bo'limlar, foydalanuvchilarni boshqarish, rollar va tizim sozlamalari.
- **Rahbar:** butun korxonani ko'radi (faqat o'qish), o'z jamoasiga vazifa tayinlaydi va tasdiqlaydi. Xodim qo'sha olmaydi.
- **Xodim:** o'z vazifalari, hujjatlari, AI yordamchi va profil.

Ruxsatlar bitta joyda: [`src/lib/auth/roles.ts`](./src/lib/auth/roles.ts). Himoya uch qatlamda: `src/proxy.ts` (har so'rovda), `(app)/layout.tsx` va har sahifada serverda qayta tekshiruv. API ham ruxsatni serverda tekshiradi.

## Skriptlar

| Buyruq               | Vazifa                                 |
| -------------------- | -------------------------------------- |
| `npm run dev`        | Ishlab chiqish serveri                 |
| `npm run build`      | Production build                       |
| `npm run lint`       | ESLint                                 |
| `npm run typecheck`  | TypeScript tekshiruvi                  |
| `npm run check:i18n` | Tarjimalar to'liqligi (uz, ru, en)     |
| `npm run format`     | Prettier                               |
| `npm run test:e2e`   | Playwright E2E (avval `npm run build`) |

E2E uchun bir marta `npx playwright install chromium` kerak. Tayyor Chromium bo'lsa, `PW_CHROMIUM_PATH=/yo'l/chrome` bilan ishga tushirish mumkin. Testlar production serverda (`next start`) ishlaydi. `git commit` oldidan Husky `lint-staged` va `typecheck` ni ishga tushiradi.

## Backend bilan ishlash

1. Backendni ishga tushiring: `../backend` papkasida `docker compose up --build` (PostgreSQL, Redis, Mailpit va API birga ko'tariladi). Batafsil: [`../backend/README.md`](../backend/README.md).
2. `.env.local` da `BACKEND_URL=http://localhost:8000` bo'lsin.
3. `npm run dev` va `http://localhost:3000`.

Brauzer backendga to'g'ridan-to'g'ri murojaat qilmaydi: `src/app/api/*` route'lari va server komponentlar `src/lib/data/service.ts` orqali backendni chaqiradi. Backend tokeni httpOnly sessiya cookie'si ichida saqlanadi. Rol va hisob holati har so'rovda backenddan olinadi (`/auth/me`), shuning uchun bloklangan hisob darhol chiqib ketadi.

Login limiti backendda (Redis bilan bir nechta serverda ham umumiy). Next.js asl IP'ni `X-Forwarded-For` orqali uzatadi; backenddagi `FORWARDED_ALLOW_IPS` ga Next.js serverining manzili yozilishi kerak. Next.js'ning oldida reverse proxy bo'lmasa, IP sarlavhasini mijoz o'zi yozib yuborishi mumkin: bunday holatda faqat hisob bo'yicha limit ishonchli.

Parolni tiklash havolasini backend SMTP orqali yuboradi (dev'da Mailpit: `http://localhost:8025`). Production bo'lmagan muhitda havola qo'shimcha ravishda formaning o'zida ham ko'rsatiladi.

## E2E testlar

Playwright avval backendni alohida `erpcrm_e2e` bazasida ko'taradi (`alembic upgrade head`, `seed --reset`, uvicorn :8100), keyin `next start` (:3100). Kerakli narsalar: PostgreSQL (`docker compose up -d db` yoki o'zingizniki), backend kutubxonalari va `npm run build`.

```bash
E2E_PYTHON=../backend/.venv/bin/python npm run test:e2e
```

| O'zgaruvchi       | Default      | Vazifasi                                 |
| ----------------- | ------------ | ---------------------------------------- |
| `E2E_PYTHON`      | `python`     | Backend kutubxonalari o'rnatilgan python |
| `E2E_BACKEND_DIR` | `../backend` | Backend papkasi                          |
| `E2E_DB_NAME`     | `erpcrm_e2e` | Har ishga tushishda tozalanadigan baza   |
