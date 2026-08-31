# ResumAI

ResumAI is a FastAPI-based professional profile site that lets visitors register, browse a profile, and ask AI-powered questions about a person's experience using data stored in Markdown files under `data/`.

## Features

- FastAPI app with environment-based config and SQLite-first local development
- SQLAlchemy data models for sessions, chat history, and logged AI interactions
- OpenAI-compatible AI provider abstraction for interchangeable model backends
- Strict anti-hallucination prompt that only answers from supplied professional context
- Knowledge base retrieval from editable Markdown files in `data/`
- Public profile flow with signed session cookies and AJAX chat
- Admin dashboard with HTTP Basic auth, filters, and session detail view
- Bootstrap/Jinja2 UI with a lightweight client-side chat widget

## Application structure

- `app/main.py` – FastAPI app entry point
- `app/config.py` – environment-driven settings (`DATABASE_URL`, AI credentials, admin creds, etc.)
- `app/database.py` – SQLAlchemy engine/session setup; defaults to SQLite and supports MySQL via `DATABASE_URL`
- `app/models/` – SQLAlchemy models for visitors, messages, and AI interactions
- `app/routes/` – public routes and admin routes
- `app/services/` – knowledge retrieval, conversation flow, and AI provider logic
- `app/templates/` – Jinja2 HTML templates
- `app/static/` – CSS and JavaScript assets

## Data layer

The app stores visitor and chat information in the database using SQLAlchemy models:

- `VisitorSession` – visitor identity, company, email, timing, and user-agent metadata
- `ConversationMessage` – chronological user/assistant chat messages
- `AIInteraction` – logged Q&A including question, answer, model, and response timing

## AI provider abstraction

The AI logic is abstracted behind `AIProvider`, with `OpenAICompatibleProvider` implemented for OpenAI-compatible APIs. It reads from environment variables:

- `AI_API_KEY`
- `AI_API_BASE_URL`
- `AI_MODEL`

The provider is selected via `get_ai_provider()`, making it easy to swap in additional providers later.

## Strict anti-hallucination prompt

The system prompt explicitly requires the AI to answer only using the supplied professional context. If the app cannot verify the answer from the retrieved knowledge, it returns a controlled "not enough information" response instead of guessing.

## Knowledge base

The editable source of truth lives in the Markdown files under `data/`:

- `profile.md`
- `resume.md`
- `skills.md`
- `education.md`
- `projects.md`
- `leadership.md`
- `ai-experience.md`
- `personal-experience.md`

`KnowledgeService` loads these files, splits them into heading-based chunks, and ranks relevant chunks by keyword overlap. The structure is designed so a future embeddings/vector-database implementation can be swapped in behind the same interface.

## Routes and UI

Public flow:

- `/` – welcome page and registration form
- `/register` – creates a visitor session and stores it in a signed session cookie
- `/profile` – displays profile sections and the chat widget
- `/chat` – AJAX endpoint that answers a question based on retrieved context

Admin flow:

- `/admin` – HTTP Basic-auth-protected dashboard
- `/admin?company=...&visitor_name=...&visit_date=...` – filters visitor sessions
- `/admin/session/{session_id}` – shows the full session detail with messages and AI interactions

The UI uses Jinja2 templates and Bootstrap styling, with a lightweight vanilla JavaScript chat widget that submits to `/chat` without a full page reload.

## Configuration and setup

A sample configuration file is provided at `.env.example` and includes:

- `DATABASE_URL`
- `AI_API_KEY`
- `AI_API_BASE_URL`
- `AI_MODEL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SECRET_KEY`

Install dependencies:

```bash
cd /Users/ryanbouche/PycharmProjects/resum-ai
python3 -m pip install -r requirements.txt
```

Create a `.env` file from the example and customize it for your environment, then run the app:

```bash
cd /Users/ryanbouche/PycharmProjects/resum-ai
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

- http://127.0.0.1:8000/
- Admin login defaults to `admin` / `changeme` unless you override them in `.env`

## Remaining work

- Add automated tests covering session creation, message persistence, knowledge loading, AI service mocking, and admin auth protection
- Expand setup and run instructions for local development and deployment
- Complete end-to-end manual verification of the running app
- Ensure final `code_review` / `codeql_checker` passes

## Notes

This project is intentionally structured for simple local use and future expansion: the knowledge base is authored in Markdown, the AI layer is provider-agnostic, and the app is organized around a clean FastAPI service architecture.
