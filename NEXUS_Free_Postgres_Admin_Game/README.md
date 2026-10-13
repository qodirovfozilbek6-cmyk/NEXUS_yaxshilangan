# 💎 NEXUS — Enter Your Digital Universe

**One Universe. One Identity. Infinite Possibilities.**

NEXUS is a Telegram-powered crystal and rank experience built with Python, FastAPI, Aiogram, PostgreSQL/SQLite, and a web Mini App.

## Features
- 💎 Server-side crystal balance shared between Telegram and the website
- 🗄️ PostgreSQL support through `DATABASE_URL`; SQLite remains available for local development
- 🔁 One-time import of existing SQLite user balances if the old database file is still present when PostgreSQL is first enabled
- 🤖 Telegram bot, Mini App authentication, and browser Telegram Login
- 👑 Creator-only admin panel with user list, IDs, balances, last login method, and activity overview
- 🎮 Crystal Rush: 15-second mini-game; rewards are stored against the authenticated Telegram ID
- 🏆 Rank progression, cooldowns, shop, and world statistics

## Free database setup (Neon)
1. Create a free PostgreSQL project at [Neon](https://neon.com/).
2. In the Neon dashboard, choose **Connect** and copy the PostgreSQL connection string. Prefer the pooled connection for this app and keep its `sslmode=require` parameter.
3. In Render, open the NEXUS Web Service → **Environment** and add:
   - `DATABASE_URL` — the complete Neon connection string (keep it secret)
   - `NEXUS_OWNER_ID` — your numeric Telegram user ID
   - `BOT_TOKEN` — your bot token
   - `WEBAPP_URL` — `https://nexus-2-tg9y.onrender.com/app/` (or the current public URL)
4. Save changes and deploy. On startup the app creates its tables automatically.
5. Open the website, sign in through Telegram, and check that the balance persists after refresh.

Neon’s free allowance can change over time; check its current plan limits in the Neon dashboard. Neon’s current documentation explains how to retrieve the connection string and use the pooler. See [Neon connection guide](https://neon.com/docs/get-started/connect-neon).

**Important:** if the old SQLite file still exists on the server, the first PostgreSQL startup imports user IDs and crystal balances once. If the old file has already disappeared due to an ephemeral host restart/deploy, those lost balances cannot be reconstructed automatically. After PostgreSQL is enabled, keep `DATABASE_URL` configured; do not remove it or the app will switch back to SQLite.

## Creator panel
- Open `/app/` and log in using the Telegram account whose numeric ID is set in `NEXUS_OWNER_ID`.
- The **CREATOR** link appears for that account and opens `/app/admin.html`.
- The API checks the authenticated Telegram ID on every admin request; hiding the link is not the security control.
- The user list contains people who have used `/start` or authenticated on the website/Mini App. “Manba” means their **most recent login method**, not a separate non-Telegram identity.

If the Creator link does not appear, check that `NEXUS_OWNER_ID` is set to the correct numeric Telegram ID in Render and redeploy.

## Crystal Rush game
- A game lasts 15 seconds.
- A player can start one session every five minutes.
- The server validates the session and caps the reward at 30 crystals; it updates the same PostgreSQL balance used by the rest of NEXUS.
- This is a starter mini-game. As with any client-click game, it is not designed as a cash-value or competitive prize system.

## Deploy commands
**Build command**
```bash
pip install -r requirements.txt
```

**Start command**
```bash
python -m uvicorn nexus.main:app --host 0.0.0.0 --port $PORT
```

## Enable browser Telegram Login
1. Open [@BotFather](https://t.me/BotFather).
2. Run `/setdomain` and select `@nexus_fozilbek_bot`.
3. Set the domain to `nexus-2-tg9y.onrender.com` (domain only; no `https://` or path).
4. Deploy and open `https://nexus-2-tg9y.onrender.com/app/`.

The backend verifies Telegram Login Widget data and Mini App `initData`. Browser sessions use a signed, `HttpOnly`, `Secure`, `SameSite=Lax` cookie.

## Environment variables
- `BOT_TOKEN` — Telegram bot token (secret)
- `NEXUS_OWNER_ID` — numeric Telegram ID for the creator
- `WEBAPP_URL` — public HTTPS Mini App URL
- `DATABASE_URL` — PostgreSQL URL from Neon; if empty, local SQLite is used
- `DATABASE_PATH` — SQLite path used for local development and one-time legacy import
- `DEBUG=false`

## Project structure
```text
NEXUS/
├── nexus/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── handlers.py
│   └── security.py
├── web/
│   ├── index.html
│   └── admin.html
├── requirements.txt
├── .env.example
└── README.md
```

**Created by Fozilbek Qodirov**
