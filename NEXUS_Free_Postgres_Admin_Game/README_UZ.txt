NEXUS — PostgreSQL, Creator paneli va Crystal Rush

1. Render -> Environment bo‘limida DATABASE_URL nomli o‘zgaruvchi yarating.
2. Neon.com saytidan bepul PostgreSQL loyiha oching, Connect tugmasidan connection string oling va DATABASE_URL ga kiriting.
3. NEXUS_OWNER_ID ga o‘z Telegram raqamli ID’ingizni kiriting.
4. BOT_TOKEN va WEBAPP_URL sozlamalari ham to‘g‘ri ekanini tekshiring.
5. Deploy qiling. Bazadagi kristallar foydalanuvchi Telegram ID’si bilan saqlanadi.
6. Eski SQLite fayli serverda hali mavjud bo‘lsa, birinchi PostgreSQL ishga tushishida foydalanuvchi balanslari bir marta ko‘chiriladi.
7. Saytga Creator ID bilan kiring; CREATOR tugmasi orqali /app/admin.html ochiladi.
8. Crystal Rush o‘yini 15 soniya davom etadi, 5 daqiqada bir marta o‘ynaladi, mukofot balansga server orqali qo‘shiladi.

Muhim: DATABASE_URL sir hisoblanadi. Uni ommaviy GitHub kodiga yozmang. Faqat Render Environment bo‘limida saqlang.
