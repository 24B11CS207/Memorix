# DQMS Agent Instructions

## Project Overview
DQMS is a Django-based AI-powered educational platform for dynamic question mastery. It features AI-generated learning modules, spaced-repetition revisions, analytics, rewards, and chatbot integration using Azure OpenAI.

## Quick Setup
- Local dev: `python manage.py migrate && python manage.py runserver` (uses SQLite by default)
- Production: Set `USE_SQLITE=False` in `.env`, configure Postgres, run `docker-compose up --build`
- Dependencies: `pip install -r requirements.txt`

## Architecture
- Multi-app Django structure: `accounts`, `ai_engine`, `analytics`, `core`, `dashboard`, `exams`, `notes`, `notifications`, `revisions`, `rewards`, `topics`
- Key patterns: JSONField for flexible data, class-based views, Bootstrap 5 templates, AI abstraction in `ai_engine/services.py`
- Boundaries: Apps loosely coupled via models and signals; monolithic design

## Conventions
- Environment variables via `django-environ` (`.env` file)
- Database toggling: SQLite for dev, Postgres for prod
- AI fallbacks: Graceful degradation when Azure OpenAI unavailable
- Custom middleware: `StreakMiddleware` for user streaks
- No test suite: Manual testing; add `pytest` for automation
- Email: Console backend in dev, SMTP in prod

## Common Pitfalls
- AI dependency: Ensure Azure OpenAI keys in `.env`; features degrade without it
- Database switching: Migrate after toggling `USE_SQLITE`
- Cron jobs: Schedule `python manage.py send_review_reminders` daily
- Static files: Run `collectstatic` for production
- Security: Set `SECRET_KEY` and API keys securely; disable `DEBUG` in prod

## Key Files
- `core/settings.py`: Central configuration
- `topics/models.py`: Core domain models
- `ai_engine/services.py`: AI service layer
- `templates/base.html`: Main layout template
- `README.md`: Detailed setup and deployment guide

## Workflow
- Topics → AI modules → mini-tests → revisions → exams
- Model changes: Update app `models.py`, run `makemigrations`
- AI calls: Route through `ai_engine` with error handling
- Deployment: Use Docker for consistency

Link to [README.md](README.md) for comprehensive documentation.</content>
<parameter name="filePath">d:\cse\DQMSClaude\DQMS\AGENTS.md