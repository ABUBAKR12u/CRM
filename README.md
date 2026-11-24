# CRM

Korxona rahbari va xodimlari uchun AI biznes operatsion platformasi: rolga qarab ishlaydigan boshqaruv paneli, vazifalar, tasdiqlash jarayoni, jamoa va bildirishnomalar.

| Papka | Nima | Texnologiya |
| --- | --- | --- |
| [`backend/`](./backend) | API, biznes qoidalari, ma'lumotlar bazasi | Python 3.14, FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, Redis |
| [`ai-ops-platform/`](./ai-ops-platform) | Veb interfeys | Next.js 16, TypeScript, Tailwind CSS 4, Ant Design 6, next-intl |
| [`.github/workflows/`](./.github/workflows) | CI | GitHub Actions |
| [`docs/`](./docs) | Qilingan ishlar hisoboti | |

## Ishga tushirish

Kerak bo'ladi: Python 3.14, Node.js 20+, PostgreSQL (yoki Docker Desktop).

### 1-yo'l: Docker bilan (eng oson)

```powershell
cd backend
docker compose up --build
```

PostgreSQL, Redis, Mailpit va API birga ko'tariladi, migratsiya va demo ma'lumotlar avtomatik. API: <http://localhost:8000/docs>, yuborilgan xatlar: <http://localhost:8025>.

### 2-yo'l: Docker'siz (Windows)

1. PostgreSQL o'rnating va `psql` da bir marta bajaring:

   ```sql
   CREATE ROLE erpcrm LOGIN PASSWORD 'erpcrm';
   CREATE DATABASE erpcrm OWNER erpcrm;
   CREATE DATABASE erpcrm_test OWNER erpcrm;
   ```

2. Backend (birinchi marta):

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   python -m alembic upgrade head
   python -m app.utils.seed
   ```

3. Backendni ishga tushirish (har safar, `backend` papkasidan):

   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload
   ```

   Server albatta `backend` papkasidan ishga tushiriladi: `.env.development` va `alembic.ini` shu yerdan o'qiladi. Redis va SMTP shart emas: limit xotirada ishlaydi, parol tiklash havolasi formaning o'zida ko'rsatiladi.

### Frontend

Yangi terminalda:

```powershell
cd ai-ops-platform
npm install
copy .env.example .env.local
npm run dev
```

`.env.local` dagi `SESSION_SECRET=` ga kamida 32 belgili kalit yozing: `node -e "console.log(require('crypto').randomBytes(48).toString('base64url'))"`. Brauzerda <http://localhost:3000> ni oching.

### Testlar

- Backend: `cd backend`, `python -m pytest`
- Frontend: `npm run typecheck`, `npm run lint`, `npm run build`, keyin `npm run test:e2e` (batafsil: [frontend README](./ai-ops-platform/README.md))

## Demo hisoblar

| Rol | Email | Parol |
| --- | --- | --- |
| Admin | `admin@aiops.uz` | `Admin#2026` |
| Rahbar | `manager@aiops.uz` | `Manager#2026` |
| Xodim | `employee@aiops.uz` | `Employee#2026` |

Demo ma'lumotlarni backend seed'i yaratadi va u production'da ishlamaydi.

## Hujjatlar

- [Backend](./backend/README.md): tuzilma, API, muhitlar, migratsiyalar, testlar.
- [Frontend](./ai-ops-platform/README.md): tuzilma, rollar, skriptlar, E2E testlar.
- [1-ish hisoboti](./docs/1-ish.md): qilingan ishlar tartib bilan.
