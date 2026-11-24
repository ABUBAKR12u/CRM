# AI Ops Platform — backend

`ai-ops-platform` frontendi uchun backend: FastAPI, SQLAlchemy (async), MySQL. Frontenddagi mock (`src/lib/data/service.ts`, `src/lib/mock/users.ts`) qoidalari shu yerda serverda bajariladi: rollar, vazifa holatlari, kim nimani ko'radi va boshqaradi, login limiti va parol tiklash.

## Tuzilma

| Papka / fayl | Vazifasi |
| --- | --- |
| `app/main.py` | FastAPI ilovasi, CORS va routerlarni ulash |
| `app/database/connection.py` | Async engine, `SessionLocal`, `get_db` |
| `app/database/Base.py` | `Base`, `MyDb` dependency, `str_enum`, `utcnow` |
| `app/model/` | `users.py` (`User`, `Role`), `tasks.py` (`Task`, `TaskStatus`, `Priority`), `notifications.py` |
| `app/scheme/` | Pydantic sxemalari; JSON maydonlari camelCase (`managerId`, `assigneeName`) |
| `app/routers/` | `auth`, `users`, `tasks`, `team`, `dashboard`, `notifications`, `health` |
| `app/utils/config.py` | Muhit sozlamalari (`settings`) |
| `app/utils/security.py` | Parol (argon2), JWT, `get_current_user`, `require_role` |
| `app/utils/permissions.py` | Vazifa ko'rinishi, tayinlash va holat o'tishlari qoidalari |
| `app/utils/checker.py` | Topilmasa yoki ruxsat yo'q bo'lsa xato beradigan tekshiruvlar |
| `app/utils/rate_limiting.py` | Login, parol tiklash limitlari (Redis yoki xotira) |
| `app/utils/notifications.py` | Bildirishnoma yaratish va muddat eslatmalari |
| `app/utils/email.py` | SMTP orqali parol tiklash xati (uz, ru, en) |
| `app/utils/seed.py` | Frontend mock'idagi demo ma'lumotlar: 13 xodim, 13 vazifa (production'da ishlamaydi) |

Yangi bo'lim qo'shilganda bir xil nomdagi uchta fayl yaratiladi: `app/model/<nom>.py`, `app/scheme/<nom>.py`, `app/routers/<nom>.py`. Router `app/main.py` da ulanadi, model `alembic/env.py` dagi `from app.model import ...` qatoriga qo'shiladi.

## Ishga tushirish (Docker)

1. `backend` papkasida `docker compose up --build` buyrug'ini bajaring.
2. MySQL, Redis, Mailpit va API ko'tariladi. API migratsiyalarni bajaradi, demo ma'lumotlarni yaratadi va `--reload` bilan ishlaydi.
   Yuborilgan xatlar (parol tiklash): <http://localhost:8025>.
3. Brauzerda <http://localhost:8000/docs> manzilini oching. `Authorize` tugmasida demo email va parol bilan kirish mumkin.

## Ishga tushirish (Docker'siz)

1. Kutubxonalarni o'rnating: `pip install -r requirements-dev.txt`.
2. `.env` faylida MySQL login'ini yozing (`DB_USERNAME`, `DB_PASS`). Bazalar (`erpcrm`, testlar uchun `erpcrm_test`) birinchi migratsiyada o'zi yaratiladi.
3. Migratsiyalar: `python -m alembic upgrade head`.
4. Demo ma'lumotlar: `python -m app.utils.seed` (bazani tozalab qayta yaratish: `--reset`).
5. Server: `python -m uvicorn app.main:app --reload`.

## Demo hisoblar

| Rol | Email | Parol |
| --- | --- | --- |
| Admin | `admin@aiops.uz` | `Admin#2026` |
| Rahbar | `manager@aiops.uz` | `Manager#2026` |
| Xodim | `employee@aiops.uz` | `Employee#2026` |

Qolgan seed xodimlari va admin yaratgan yangi foydalanuvchilarda parol bo'lmaydi: ular `forgot-password` orqali parol o'rnatadi.

## API

Barcha himoyalangan so'rovlar `Authorization: Bearer <token>` sarlavhasi bilan yuboriladi. Xato bo'lsa javob `{"detail": "<kod>"}` ko'rinishida keladi; kodlar frontenddagi `apiErrors` tarjimalari bilan bir xil (`forbidden`, `notFound`, `emailTaken`, `selfAction`, `hasOpenTasks`, `invalidAssignee`, `invalidManager`, `invalidTransition`, `noteRequired`, `empty`, `invalid`, `blocked`, `invalid_token`, `rate_limited`).

| API | Kim | Vazifasi |
| --- | --- | --- |
| `POST /auth/login` | hamma | Form: `username` (email), `password`. Token va foydalanuvchi qaytadi |
| `GET /auth/me` | kirgan | Joriy foydalanuvchi |
| `POST /auth/forgot-password` | hamma | `email`, `locale`. Havola SMTP orqali yuboriladi; javob har doim bir xil; production bo'lmagan muhitda `resetToken` ham qaytadi |
| `POST /auth/reset-password` | hamma | `token`, `password`, `confirm`; token bir martalik, 15 daqiqa |
| `GET /users/` | admin | Foydalanuvchilar ro'yxati |
| `GET /users/managers` | admin | Faol rahbarlar (forma uchun) |
| `POST /users/` | admin | Foydalanuvchi qo'shish |
| `PATCH /users/{id}` | admin | Qisman yangilash; o'zini bloklash yoki rolini o'zgartirish taqiqlangan |
| `DELETE /users/{id}` | admin | Ochiq vazifasi bo'lsa o'chirilmaydi |
| `GET /tasks/` | kirgan | Ko'rinadigan vazifalar; har birida `can.manage` va `can.advance` |
| `GET /tasks/assignees` | kirgan | Vazifa tayinlash mumkin bo'lgan odamlar |
| `POST /tasks/` | admin, rahbar | Vazifa yaratish |
| `PATCH /tasks/{id}` | admin, rahbar | Maydonlarni yangilash |
| `PATCH /tasks/{id}/status` | kirgan | Holatni o'zgartirish; tekshiruvdan qaytarishda `note` majburiy |
| `DELETE /tasks/{id}` | admin, rahbar | Vazifani o'chirish |
| `GET /team/` | rahbar | Jamoa a'zolari va ularning ochiq, tekshiruvdagi, bajarilgan vazifalari soni |
| `GET /dashboard/stats` | kirgan | Bosh sahifa ko'rsatkichlari |
| `GET /notifications/` | kirgan | Oxirgi 30 bildirishnoma va o'qilmaganlar soni |
| `PATCH /notifications/{id}/read` | kirgan | Bittasini o'qilgan deb belgilash |
| `POST /notifications/read` | kirgan | Hammasini o'qilgan deb belgilash |
| `GET /health/live`, `GET /health/ready` | hamma | Server va baza holati |

Bildirishnomalar hodisalarda yaratiladi: vazifa tayinlanganda (`taskAssigned`), tekshiruvga yuborilganda — yaratuvchi va rahbarga (`approvalWaiting`), tasdiqlanganda (`approved`), qaytarilganda (`taskReturned`), yangi xodim qo'shilganda — adminlarga (`newUser`), rol o'zgarganda (`roleChange`), parol tiklanganda — adminlarga (`passwordReset`). Muddat eslatmalari (`deadlineSoon` — bugun/ertaga, `taskLate` — rahbarga muddati o'tgan) ro'yxat so'ralganda bir marta yaratiladi. Amalni bajargan odamning o'ziga bildirishnoma kelmaydi.

Vazifa holatlari: xodim `todo → in_progress → review` (va `in_progress → todo`); rahbar yoki admin `review → done` yoki izoh bilan `review → in_progress`. O'ziga tayinlangan vazifani hech kim o'zi tasdiqlay olmaydi.

## Muhitlar

Muhit `ENVIRONMENT` bilan tanlanadi: `development` (default), `staging`, `production`. Sozlamalar tartibi: tizim env o'zgaruvchilari, keyin `.env` (shaxsiy, repoga kirmaydi), keyin `.env.<ENVIRONMENT>`.

| O'zgaruvchi | Default | Izoh |
| --- | --- | --- |
| `SECRET_KEY` | — | Majburiy, kamida 32 belgi: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ACCESS_TOKEN_MINUTES` | `480` | Sessiya muddati (8 soat) |
| `RESET_TOKEN_MINUTES` | `15` | Parol tiklash havolasi muddati |
| `DB_USERNAME`, `DB_PASS`, `DB_NAME` | — | Majburiy |
| `DB_HOST`, `DB_PORT` | `127.0.0.1`, `3306` | |
| `DEBUG` | `false` | Production'da `true` bo'lsa ilova ishga tushmaydi |
| `DOCS_ENABLED` | `true` | `false` bo'lsa `/docs`, `/redoc`, `/openapi.json` yopiladi |
| `CORS_ORIGINS` | `[]` | JSON ro'yxat: `["https://app.example.uz"]` |
| `FRONTEND_URL` | `http://localhost:3000` | Xatdagi parol tiklash havolasi uchun |
| `FORWARDED_ALLOW_IPS` | `["127.0.0.1"]` | `X-Forwarded-For` ga ishoniladigan manzillar (Next.js serveri, proxy); CIDR mumkin |
| `REDIS_URL` | — | Berilsa login limitlari Redis'da (bir nechta worker/server uchun umumiy); bo'lmasa xotirada |
| `SMTP_HOST`, `SMTP_PORT` | —, `587` | Production'da `SMTP_HOST` majburiy |
| `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_TLS`, `SMTP_FROM` | —, —, `true`, `AI Ops <no-reply@aiops.uz>` | |

## Migratsiyalar

Model o'zgarganda: `python -m alembic revision --autogenerate -m "add documents table"`. Qo'llash `python -m alembic upgrade head`, orqaga `python -m alembic downgrade -1`, moslikni tekshirish `python -m alembic check`. Production'da migratsiya deploydan oldin alohida bajariladi.

## Testlar

`python -m pytest` — testlar `<DB_NAME>_test` bazasida ishlaydi (Redis va SMTP soxta obyektlar bilan tekshiriladi). Jadvallar bir marta yaratiladi, har testdan keyin tozalanadi. Kod sifati: `ruff check .` va `ruff format --check .`.

## Frontend

`ai-ops-platform` shu API'ga ulangan: `src/lib/data/service.ts` backendni chaqiradi, token Next.js'ning httpOnly cookie'sida saqlanadi. Frontend e2e testlari backendni `erpcrm_e2e` bazasida o'zi ko'taradi (`../ai-ops-platform/README.md`, "E2E testlar").
