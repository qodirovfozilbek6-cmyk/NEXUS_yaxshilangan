# 💎 NEXUS — Enter Your Digital Universe

<p align="center">
  <strong>Your World. Your Crystals. Your Legacy.</strong>
</p>

<p align="center">
  A futuristic Telegram Mini App where technology, gaming, and a digital universe come together.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Telegram-Mini%20App-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

---

## 🌌 About NEXUS

**NEXUS** is a futuristic digital world designed around crystals, progression, and interactive experiences. Built with Python and integrated with Telegram, NEXUS brings a web-based gaming experience directly to users.

Collect crystals, explore the interface, improve your progress, and enter a digital universe designed to grow.

> ✨ This is more than a Mini App — it's the beginning of a digital universe.

## 🚀 Features

### 💎 Crystal Economy

* Collect crystals through the built-in collection system.
* Earn rewards by playing Crystal Rush.
* Store user balances in a database.
* Apply cooldowns to collection and game rewards.

### 🎮 Crystal Rush

* Play a fast-paced, 15-second clicking game.
* Earn crystals according to your score.
* Receive rewards through the backend API.
* Play again after the cooldown expires.

### 👑 Creator Dashboard

* Access a dedicated Creator administration panel.
* View registered Telegram users.
* Search users and navigate through the user list.
* Review Telegram IDs, usernames, crystal balances, and activity information.
* Check whether users most recently connected through the bot, Mini App, or website.

### 🔐 Telegram Authentication

* Integrate the Telegram bot with the web application.
* Authenticate supported Telegram Mini App sessions.
* Support Telegram Login for website access.
* Protect administrative API endpoints using the configured Creator Telegram ID.

### 🗄️ Persistent Database

* PostgreSQL support through `DATABASE_URL`.
* Compatible SQLite fallback for local development.
* Store user profiles, balances, activity, and game sessions.
* Optional one-time import of existing SQLite user balances into PostgreSQL when the original database file is available.

### 🎨 Futuristic Interface

* Dark, modern visual style.
* Aurora-inspired colors and glowing crystal elements.
* Responsive web interface.
* Designed for use on desktop and mobile devices.

---

## 🧰 Technology Stack

| Technology            | Purpose                             |
| --------------------- | ----------------------------------- |
| Python 3.11+          | Main programming language           |
| aiogram 3.x           | Telegram bot integration            |
| FastAPI               | Backend and API                     |
| PostgreSQL            | Persistent production database      |
| SQLite                | Local development fallback          |
| HTML, CSS, JavaScript | Mini App interface                  |
| Neon                  | Free-tier PostgreSQL hosting option |
| Render                | Web service hosting option          |

## 🏗️ Project Structure

```text
NEXUS/
├── nexus/
│   ├── main.py          # FastAPI app and Telegram bot
│   ├── config.py        # Environment configuration
│   └── db.py            # Database and game logic
├── web/
│   ├── index.html       # Main NEXUS interface
│   └── admin.html       # Creator dashboard
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore
├── README.md
└── README_UZ.txt
```

*The exact structure may change as the project evolves.*

## ⚙️ Run Locally

### 1. Requirements

Install the following:

* Python 3.11 or newer
* Git (optional)
* A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 2. Clone the repository

```bash
git clone https://github.com/qodirovfozilbek6-cmyk/NEXUS.git
cd NEXUS
```

### 3. Create a virtual environment

**Windows:**

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
py -3.11 -m pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file based on `.env.example`.

Example:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
NEXUS_OWNER_ID=YOUR_NUMERIC_TELEGRAM_ID
WEBAPP_URL=https://your-domain.example
DATABASE_URL=
DATABASE_PATH=nexus.db
```

Replace the example values with your own configuration.

**Important:** Keep `.env` private. Never commit your bot token, database credentials, or other secrets to GitHub.

### 6. Start NEXUS

```bash
py -3.11 -m uvicorn nexus.main:app --host 127.0.0.1 --port 8000
```

Open the local address:

```text
http://127.0.0.1:8000/app/
```

Telegram Mini Apps require a properly configured HTTPS URL when accessed through Telegram.

---

## ☁️ Free-Tier Deployment

NEXUS can be deployed using services that offer free tiers. Availability and limits depend on each provider's current plan.

### Step 1 — Create a PostgreSQL database

1. Create an account at [Neon](https://neon.tech/).
2. Create a PostgreSQL project.
3. Open the connection details.
4. Copy the connection string.
5. Keep the connection string private.

### Step 2 — Configure Render

1. Open [Render](https://render.com/).
2. Create a Web Service connected to your GitHub repository.
3. Set the build command:

```bash
pip install -r requirements.txt
```

4. Set the start command:

```bash
uvicorn nexus.main:app --host 0.0.0.0 --port $PORT
```

5. Add the required environment variables in the Render dashboard.

| Variable         | Value                                  |
| ---------------- | -------------------------------------- |
| `BOT_TOKEN`      | Your Telegram bot token                |
| `NEXUS_OWNER_ID` | Your numeric Telegram user ID          |
| `WEBAPP_URL`     | Your deployed HTTPS URL                |
| `DATABASE_URL`   | Your Neon PostgreSQL connection string |

Set any additional variables required by `.env.example` or the current application configuration.

### Step 3 — Configure Telegram

1. Open [@BotFather](https://t.me/BotFather).
2. Select your bot.
3. Configure the Mini App or website domain using your actual deployed domain.
4. Confirm that the domain matches your application URL.
5. Open the Mini App and test authentication.

### Step 4 — Open NEXUS

Main application:

`https://your-domain.example/app/`

Creator dashboard:

`https://your-domain.example/app/admin.html`

Replace `your-domain.example` with your actual Render domain.

**Note:** A free hosting service may sleep when inactive or impose usage limits. Free hosting does not guarantee uninterrupted 24/7 availability.

---

## 👑 Creator Access

The Creator dashboard is intended for the administrator whose numeric Telegram ID matches `NEXUS_OWNER_ID`.

To configure it:

1. Find your numeric Telegram user ID using a trusted Telegram ID tool.
2. Set that ID in the hosting provider's environment variables.
3. Redeploy the application.
4. Authenticate with the matching Telegram account.
5. Open the Creator dashboard.

The dashboard is not intended to be a public user directory. Administrative API endpoints must enforce server-side authorization; hiding the dashboard link alone is not sufficient.

## 🎯 Game Reward Rules

Crystal Rush currently uses a short game session:

* **Session duration:** 15 seconds
* **Reward formula:** `min(30, clicks // 2)`
* **Cooldown:** 5 minutes between game starts

The server calculates the reward from the submitted score and applies a maximum reward per session.

This is a starter game mechanic, not a fully cheat-proof competitive system. Production use may require stronger validation, rate limiting, and abuse detection.

## 🛡️ Security

* Store secrets in environment variables.
* Never publish `.env` or private database credentials.
* Keep Creator endpoints protected by server-side authorization.
* Use HTTPS for production Telegram authentication.
* Validate game sessions and reward requests on the server.
* Back up your database and test migrations before important updates.

## 🧭 Roadmap

Potential future improvements:

* [ ] More mini-games and crystal rewards
* [ ] User levels and achievements
* [ ] Crystal shop and unlockable items
* [ ] Daily missions and streak rewards
* [ ] User profile customization
* [ ] Improved game validation and anti-abuse protection
* [ ] Expanded Creator analytics
* [ ] Automated database backup tools
* [ ] More visual themes and universe environments

## 🤝 Contributing

Ideas, bug reports, and improvements are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Test your changes.
5. Submit a pull request describing the improvement.

Please do not include private tokens, credentials, or personal user data in contributions.

## 📜 License

This project is distributed under the MIT License, provided that a corresponding `LICENSE` file is included in the repository.

## 🌠 The NEXUS Vision

NEXUS is built around a simple idea:

**Your progress should be yours to keep. Your world should be yours to explore.**

Every crystal is progress. Every feature is another step toward a bigger digital universe.

<p align="center">
  <strong>💎 NEXUS — Your World. Your Crystals. Your Legacy.</strong>
</p>

<p align="center">
  Created with ambition by <strong>Fozilbek Qodirov</strong>
</p>
