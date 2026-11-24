# 1-ish hisoboti

## Qilingan ishlar

- 24.11 Python 3.14 va FastAPI asosida `backend` loyihasini yaratdim, kutubxonalarni `requirements.txt` (ishlash uchun) va `requirements-dev.txt` (test va lint uchun) ga ajratib, versiyalarini qotirdim.
- 24.11 Loyiha tuzilmasini ERP loyihamdagi uslubda qurdim: `app/database` (`connection.py`, `Base.py` va `MyDb` dependency), `app/model`, `app/scheme`, `app/routers`, `app/utils` (`config.py` ichida `settings`).
- 24.11 Ma'lumotlar bazasini async SQLAlchemy 2 orqali uladim: ulanishlar pool'i, `pool_pre_ping`, bazaga ulanish manzili `URL.create` bilan yig'iladi (parolda `@`, `:` bo'lsa ham buzilmaydi).
- 24.11 Development, Staging va Production sozlamalarini ajratdim: muhit `ENVIRONMENT` bilan tanlanadi va `.env.<muhit>` fayli o'qiladi. Production'da `DEBUG=true` yoki pochta sozlanmagan bo'lsa ilova ishga tushmaydi. Maxfiy `.env` fayllari repoga kirmaydi.
- 24.11 Alembic migratsiya tizimini async rejimda sozladim: constraint nomlash qoidasi, yangi migratsiyalarni `ruff` bilan avtomatik formatlash, `alembic check` bilan model va migratsiya mosligini tekshirish.
- 24.11 Docker Compose orqali lokal muhit yaratdim: MySQL 8.4, Redis, Mailpit va API. Dockerfile'da `dev` va `prod` bosqichlari bor; prod image yengil va root bo'lmagan foydalanuvchi bilan ishlaydi, `HEALTHCHECK` bor.
- 24.11 API hujjatlarini yoqdim: Swagger `/docs`, ReDoc `/redoc`, `/openapi.json`; `DOCS_ENABLED=false` bo'lsa uchalasi yopiladi. `/health/live` va `/health/ready` (bazani tekshiradi) endpointlarini yozdim.
- 24.11 GitHub Actions CI tayyorladim: `lint` (ruff), `test` (MySQL bilan migratsiyani oldinga, orqaga va qayta oldinga yurgizish, `alembic check`, pytest) va `docker` (prod image yig'ish).
- 24.11 `ai-ops-platform` frontendidagi mock qoidalarni o'rganib, backendda `User` va `Task` modellarini, birinchi migratsiyani yozdim: rollar (admin, rahbar, xodim), vazifa holatlari (`todo`, `in_progress`, `review`, `done`), muhimlik, muddat.
- 24.11 Autentifikatsiyani yozdim: parol `argon2` bilan, JWT (`PyJWT`), `get_current_user` va `require_role(...)`. Login vaqtida mavjud bo'lmagan email uchun ham parol tekshiriladi, shunda javob vaqti hisob borligini oshkor qilmaydi.
- 24.11 Foydalanuvchilar API'sini yozdim: ro'yxat, rahbarlar, qo'shish, tahrirlash, o'chirish. O'zini bloklash yoki rolini o'zgartirish taqiqlangan, ochiq vazifasi bor xodim o'chirilmaydi, rahbar boshqa rolga o'tsa jamoasi bo'shatiladi.
- 24.11 Vazifalar API'sini yozdim: kim qaysi vazifani ko'rishi SQL so'rov darajasida (`visible_tasks`), tayinlash faqat o'z jamoasiga, holat o'tishlari (xodim `todo → in_progress → review`, rahbar `review → done` yoki izoh bilan qaytaradi), har vazifada `can.manage` va `can.advance`.
- 24.11 Jamoa (`/team`) va bosh sahifa statistikasi (`/dashboard/stats`) endpointlarini yozdim, `doneWeek` haqiqatan oxirgi 7 kunni sanaydi.
- 24.11 JSON maydonlarini frontend bilan bir xil camelCase qildim, xato kodlari frontenddagi `apiErrors` tarjimalari bilan mos (`emailTaken`, `noteRequired`, `invalidTransition` va boshqalar).
- 24.11 Parolni tiklashni yozdim: token bir martalik va 15 daqiqa amal qiladi (parol o'zgargach eski token yaroqsiz), havola SMTP orqali uch tilda (uz, ru, en) yuboriladi. Dev'da xatlar Mailpit'da ko'rinadi.
- 24.11 Login limitini yozdim: faqat xato urinishlar sanaladi (bir hisobga 5 ta, bir IP'ga 20 ta, 15 daqiqa), javobda `Retry-After` bor. `REDIS_URL` berilsa limit Redis'da saqlanadi va bir nechta server uchun umumiy bo'ladi.
- 24.11 Asl foydalanuvchi IP'sini `X-Forwarded-For` orqali olishni sozladim: faqat `FORWARDED_ALLOW_IPS` dagi ishonchli manzildan kelgan sarlavha qabul qilinadi.
- 24.11 Bildirishnomalarni yozdim: vazifa tayinlanganda, tekshiruvga yuborilganda, tasdiqlanganda, qaytarilganda, yangi xodim qo'shilganda, rol o'zgarganda va parol tiklanganda yaratiladi. "Muddat yaqin" va "kechikdi" eslatmalari ro'yxat so'ralganda bir marta qo'shiladi. Bittasini yoki hammasini o'qilgan deb belgilash mumkin.
- 24.11 Seed skriptini yozdim: frontend mock'idagi 13 xodim, 13 vazifa va boshlang'ich bildirishnomalar; `--reset` bazani tozalab qayta yaratadi, production'da ishlamaydi.
- 24.11 Frontendni backendga uladim: `src/lib/backend.ts` yagona aloqa nuqtasi, `service.ts` endi backendni chaqiradi, backend tokeni httpOnly sessiya cookie'sida saqlanadi. Hisob holati har so'rovda backenddan olinadi, bloklangan hisob darhol chiqib ketadi. Mock fayllari (`src/lib/mock`, `store.ts`) o'chirildi.
- 24.11 Bildirishnomalar menyusini backendga uladim: matnlarda vazifa nomi, xodim ismi va qaytarish izohi chiqadi, tarjimalar uch tilda yangilandi.
- 24.11 E2E testlarni haqiqiy backendga moslashtirdim: Playwright avval backendni alohida `erpcrm_e2e` bazasida ko'taradi (`alembic upgrade`, `seed --reset`, uvicorn), keyin Next.js'ni. Qattiq yozilgan ID'lar o'rniga nom bo'yicha qidirish (`seedIds`) qo'shdim.
- 24.11 Backend uchun 95 ta pytest test yozdim (auth, foydalanuvchilar, vazifalar, jamoa, statistika, bildirishnomalar, pochta, Redis limiti, sozlamalar). Ruff, migratsiya sikli, `alembic check`, frontend `typecheck`, `lint`, `check:i18n` va `build` o'tdi.
- 24.11 Haqiqiy backend bilan 107 ta Playwright E2E testning hammasi o'tdi (kirish, rollar, vazifalar aylanishi, foydalanuvchilar, bildirishnomalar, limitlar, qulaylik, telefon). Loyihani GitHub'ga yukladim.
- 24.11 Ma'lumotlar bazasini PostgreSQL'dan MySQL'ga o'tkazdim (ERP loyihamdagidek `aiomysql`): baza `alembic upgrade` va testlarda o'zi yaratiladi (`utf8mb4`), vaqtlar UTC'da saqlanadi, Docker va CI MySQL 8.4 da. 95 ta backend testi va E2E testlar MySQL bilan qayta o'tdi.

## Muammolar

- Kompyuterda Docker o'rnatilmagan edi, dastlab tanlangan PostgreSQL esa yo'q edi.
- `alembic.ini` dagi `timezone = UTC` Windows'da xato berdi: vaqt zonalari bazasi yo'q.
- Testlar juda sekin ishladi: 76 ta test 3 daqiqa.
- Jadvallarni bir marta yaratish uchun session darajasidagi async fixture testlarni osib qo'ydi.
- Ruff `Depends(require_role(...))` ni B008 xatosi deb ko'rsatdi.
- Frontend E2E testlari mock'dagi `u_e1`, `t_9` kabi ID'larga bog'langan edi, parol tiklash testi esa menejer parolini haqiqatan o'zgartirib, keyingi testlarni buzardi.
- `check-i18n.mjs` Windows'da `C:\C:\...` yo'li bilan yiqildi.
- Bildirishnoma menyusi ochilganda kelgan eski javob foydalanuvchi endigina o'qigan bildirishnomani qayta "o'qilmagan" qilib qo'yardi.
- Haqiqiy backend bilan login va birinchi sahifa yuklanishi mock'dagidan sekinroq bo'ldi: ikkita E2E test (birinchi kirish va qulaylik tekshiruvi) vaqt chegarasiga sig'madi.
- MySQL'ga o'tganda uchta farq chiqdi: `DATETIME` vaqt zonasini saqlamaydi, `COUNT(...) FILTER` sintaksisi yo'q, tashqi kalit ishlatayotgan indeksni jadvaldan oldin o'chirib bo'lmaydi (`downgrade` yiqildi).

## Yechim

- Avval testlarni vaqtinchalik `pgserver` (pip orqali o'rnatiladigan PostgreSQL) bilan tekshirdim. Keyin loyihani kompyuterda allaqachon bor MySQL'ga o'tkazdim, endi alohida baza o'rnatish kerak emas.
- `timezone` qatorini olib tashladim: fayl nomidagi sana faqat ko'rinish uchun, tartib revision zanjiri bo'yicha.
- Sekinlikni o'lchab ko'rdim: har ulanish 2 soniya kutardi, chunki `localhost` avval IPv6 (`::1`) ga urinardi. Bundan tashqari jadvallar har testda qayta yaratilardi. Jadvallarni sessiyada bir marta yaratib, har testdan keyin `DELETE` qiladigan qildim. Natija: 95 ta test ~50 soniya.
- Sxema yaratishni alohida `asyncio.run` bilan sync fixture'ga o'tkazdim, ulanishlarda `NullPool` ishlatdim.
- `ruff.toml` da `extend-immutable-calls` ga `Depends` va `require_role` ni qo'shdim.
- E2E uchun `seedIds` yordamchisini yozdim (ID nom bo'yicha topiladi), parol tiklash testini demo bo'lmagan hisobga o'tkazdim, bildirishnoma testini aniq songa bog'liq bo'lmaydigan qildim.
- Skriptda yo'lni `fileURLToPath` bilan oladigan qildim.
- Har mahalliy o'zgarishda versiya raqamini oshiradigan qildim: undan oldin boshlangan yuklash natijasi e'tiborsiz qoldiriladi.
- Avval backendni alohida o'lchadim: login ~0,17 s, `/auth/me` 14 ms, statistika ~80 ms, ya'ni sekinlik sovuq startda edi. Testdagi kirish kutish vaqtini 15 soniyaga, barcha sahifalarni aylanadigan qulaylik testlarini 60 soniyaga oshirdim.
- Vaqt uchun `UTCDateTime` turini yozdim (UTC'da saqlab, UTC sifatida o'qiydi), jamoa hisobini `COUNT(CASE ...)` ga o'tkazdim, migratsiyalarning `downgrade` qismida faqat jadvallarni o'chiradigan qildim (indekslar jadval bilan o'chadi).
