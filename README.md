# DQMS — Dynamic Question Mastery System

An AI-powered learning platform built with **Django**, **PostgreSQL**, **Azure OpenAI**, and **Bootstrap 5**. Enter a topic, and DQMS auto-generates 5 progressive learning modules with mini-tests, instant practice exams, and a spaced-repetition revision schedule — complete with badges, streaks, analytics, an AI tutor chatbot, and email notifications.

---

## ✨ Features

| Module | Highlights |
|---|---|
| **Authentication** | Signup, login, logout, email verification, password reset, profile editor, login email notifications |
| **Dashboard** | Total/Completed/Pending topics, accuracy %, daily streak, reviews due, badges earned, 7-day activity chart, strong vs weak topics |
| **My Topics (AI Learning)** | Enter any topic + difficulty → AI generates 5 modules with content, key points, examples, summary, mini-tests; 80% pass to unlock next module |
| **Instant Test Mode** | 15 AI-generated MCQs, randomized, one attempt/topic/day, AI explanation on every wrong answer |
| **Long Knowledge (Revisions)** | 4/5/6-review spaced-repetition (Day 1, 3, 6, 10, 15, 21); failed reviews auto-shift future schedule by +1 day |
| **Analytics** | Topic mastery bar chart, pass/fail doughnut, 14-day activity line chart, difficulty pie |
| **Notifications** | Email + in-app: login alerts, welcome, test results, review reminders, badge unlocks |
| **Rewards** | Topic badges (10/25/50/100), Point badges (100/300/600/1000), streak badges, coins, leaderboard |
| **Notes** | CRUD personal notes, link to topics, search |
| **Admin Panel** | Full Django admin for users, topics, questions, reviews, notifications, badges, AI logs |
| **AI Tutor Chatbot** | Real-time chat backed by Azure OpenAI |
| **Voice Reading** | Browser TTS for module content |

---

## 🛠 Tech Stack

- **Backend:** Python 3.11, Django 4.2, Django REST Framework
- **Frontend:** Bootstrap 5, Chart.js, vanilla JS, Bootstrap Icons
- **Database:** PostgreSQL 15 (SQLite fallback for instant local dev)
- **AI:** Azure OpenAI (GPT-4o-mini or any deployment)
- **Auth:** Django auth + JWT (DRF SimpleJWT)
- **Email:** Django SMTP backend
- **Deployment:** Gunicorn + Whitenoise + Docker / Render / Railway-ready

---

## 📁 Project Structure

```
DQMS/
├── core/                # settings, urls, wsgi/asgi
├── accounts/            # auth, profile, streaks, signals, middleware
├── dashboard/           # main dashboard
├── topics/              # topics, learning modules, mini-tests
├── ai_engine/           # Azure OpenAI service layer + chatbot + AI usage logs
├── analytics/           # analytics views with chart data
├── revisions/           # spaced repetition plans + sessions
├── exams/               # instant test mode
├── notifications/       # email + in-app notifications + reminder cron
├── rewards/             # badges, points, coins, leaderboard
├── notes/               # personal notes CRUD
├── templates/           # all HTML templates (dark glassmorphism Bootstrap)
├── static/              # CSS, JS
├── media/               # uploaded avatars
├── requirements.txt
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start (Local — SQLite, no Docker)

```bash
# 1. Clone / unzip and enter the folder
cd DQMS

# 2. Create a virtualenv
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install deps
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env if needed — default USE_SQLITE=True works out of the box.

# 5. Migrate + create superuser
python manage.py migrate
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

Visit http://127.0.0.1:8000.

> Without Azure OpenAI credentials configured, DQMS uses **safe fallback content** so you can still explore every module, take quizzes, and try the full UX. Real AI-generated content kicks in once you set `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` in your `.env`.

---

## 🐘 Production Setup (PostgreSQL)

In `.env`, set:

```
USE_SQLITE=False
DB_NAME=dqms
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=127.0.0.1
DB_PORT=5432
```

Create the DB first:

```bash
createdb dqms
python manage.py migrate
```

---

## 🐳 Docker

```bash
cp .env.example .env
docker-compose up --build
```

App at http://localhost:8000. Postgres data persisted in the `pgdata` volume.

Create a superuser:

```bash
docker-compose exec web python manage.py createsuperuser
```

---

## 🤖 Azure OpenAI Setup

1. Create an Azure OpenAI resource in the [Azure portal](https://portal.azure.com).
2. Deploy a chat model (e.g. `gpt-4o-mini`).
3. Copy the **endpoint URL** and **API key** into `.env`:

```
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

The AI service layer (`ai_engine/services.py`) handles retries, JSON-only response parsing, and graceful fallbacks.

---

## ✉️ Email (Gmail SMTP) Setup

1. Enable 2FA on your Google account.
2. Create an [app password](https://myaccount.google.com/apppasswords).
3. Set in `.env`:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=DQMS <youremail@gmail.com>
```

In dev mode without SMTP creds, DQMS automatically uses the **console email backend** so you'll see emails in the terminal.

---

## 📅 Cron Jobs (Review Reminders)

DQMS ships a management command that emails users with reviews due today:

```bash
python manage.py send_review_reminders
```

Schedule it daily (cron / Render Cron Job / Railway cron):

```
0 8 * * *  cd /app && python manage.py send_review_reminders
```

---

## 🌐 Deployment

### Render

1. New → Web Service → connect this repo
2. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. Start command: `gunicorn core.wsgi:application`
4. Add a PostgreSQL database from the Render dashboard, copy `DATABASE_URL`-style values into `.env`
5. Set all `.env` keys in **Environment**

### Railway

1. New Project → Deploy from GitHub
2. Add a PostgreSQL plugin
3. Set environment variables (Railway exposes `PGHOST`, `PGUSER`, etc — map them to `DB_HOST`, `DB_USER`)
4. Deploy

### Docker on any VPS

```bash
docker-compose up -d --build
```

---

## 🔐 Security Checklist (Production)

- [ ] Set `DEBUG=False`
- [ ] Generate a strong `SECRET_KEY`
- [ ] Restrict `ALLOWED_HOSTS`
- [ ] Use HTTPS (set `SECURE_SSL_REDIRECT=True` if behind HTTPS reverse proxy)
- [ ] Use a real SMTP provider
- [ ] Rotate API keys regularly
- [ ] Run `python manage.py check --deploy`

---

## 🧪 Sample Workflow

1. **Sign up** → verify email → log in.
2. **Create a topic**: "Photosynthesis", difficulty "Medium".
3. DQMS calls Azure OpenAI to generate **5 learning modules** + mini-tests.
4. Read Module 1 → take 5-question mini-test → score 80%+ → next module unlocks.
5. Once all modules complete → topic marked done → badge awarded.
6. Take the **Instant Test** for instant 15-MCQ practice with AI explanations on wrong answers.
7. Schedule a **Revision Plan**: pick 4/5/6 reviews. Get email reminders on due days.
8. Track progress on **Dashboard** + **Analytics**.
9. Ask the **AI Tutor** for follow-up questions.
10. Earn **points → coins → badges**, climb the **leaderboard**.

---

## 📚 API Documentation

DQMS exposes basic JSON endpoints (DRF). Authenticate via session or JWT.

| Endpoint | Method | Description |
|---|---|---|
| `/ai/api/chatbot/` | POST | Chat with the AI tutor. Body: `{"history": [...], "message": "..."}` |
| `/notifications/` | GET | List in-app notifications |
| `/notifications/<id>/read/` | POST | Mark notification as read |

DRF + JWT are wired up in `settings.REST_FRAMEWORK` so you can extend into a full headless API.

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| "Could not connect to server" on Postgres | Check `DB_HOST` (use `db` inside Docker; `127.0.0.1` locally) |
| AI responses are placeholders | Set `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` |
| Emails not arriving | Check Gmail app password; check spam; in dev, check terminal (console backend) |
| `psycopg2` install fails | Install `libpq-dev` (Debian/Ubuntu) or use `psycopg2-binary` (already in requirements) |
| Static files missing in prod | Run `python manage.py collectstatic --noinput` |

---

## 📜 License

MIT — use it, fork it, ship it.

---

## 🙏 Credits

Built as the **Dynamic Question Mastery System** project — combining the best of spaced repetition, AI-generated content, and modern UX.
