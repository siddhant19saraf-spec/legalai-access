# LegalAI Access

An AI-powered **general legal information** platform built for the Hack2Skill PromptWars Virtual Challenge — *AI for Legal Assistance & Access*.

> **This platform provides general legal information only and does not constitute legal advice.** The information is AI-generated and may contain inaccuracies. For matters that could significantly affect your rights, liberty, or finances, consult a qualified attorney licensed in your jurisdiction. No attorney-client relationship is created by using this service.

## Overview

LegalAI Access takes a natural-language legal question and returns a **structured, risk-aware, jurisdiction-aware information packet** — summary, explanation, next steps, escalation guidance, limitations, sources (when a curated source exists), and a persistent disclaimer. It is deliberately built as a multi-step pipeline (classify → retrieve → generate → validate → safety-check), not a single chatbot prompt.

## Problem Statement

Access to legal information is a major barrier to justice. Many people cannot afford attorneys for routine questions, and public resources are fragmented, jargon-heavy, or jurisdiction-specific without clear guidance on risk and next steps.

## Solution

A production web application that:

1. Accepts natural-language legal questions (with optional jurisdiction and context)
2. Classifies request type (deadline inquiry, procedural guidance, rights explanation, etc.)
3. Assesses risk level (low / medium / high / critical) from keyword and category rules
4. Detects or accepts jurisdiction
5. Attaches **curated** legal sources when a match exists (and says so when none does)
6. Generates a structured AI response with disclaimers, uncertainty notes, and next steps
7. Enforces safety checks (no fabricated citations, no definitive-outcome promises, high-risk escalation)
8. Collects optional user feedback (in-memory; not persisted across restarts)

## Key Features

- **Multi-step AI workflow** — classification → source retrieval → generation → output validation → safety gate
- **Risk-aware responses** — critical/high-risk queries get a prominent escalation notice and mandatory uncertainty notes
- **Source transparency** — curated sources shown with citation, URL, and verification status; explicit "no verified source" state when none matches
- **Jurisdiction awareness** — US federal, CA/NY/TX, UK, Canada, Australia, EU, international (auto-detect fallback)
- **Prompt-injection defense** — pattern scanning with risk scoring; high-risk inputs are blocked with a structured security response
- **Responsible-AI disclaimers** — persistent banner, per-response disclaimer, footer notice
- **Accessible interface** — labelled controls, keyboard operable, focus indicators, live regions for loading/errors (see Accessibility)
- **Security hardening** — rate limiting, security headers, input size limits, no secrets in the frontend
- **Tested** — 52 backend tests, 33 frontend tests, lint + type-check + production build

## User Journey

1. Open the app → workspace (question form, jurisdiction selector, examples, online status) is visible
2. Type a legal question (optionally open **Additional Context**, pick a jurisdiction)
3. Submit (button or Ctrl+Enter) → loading state with live announcement
4. Receive structured response: metadata badges, answer, key points, risk level, jurisdiction, sources, next steps, escalation (if any), limitations, disclaimer
5. Optionally rate the response (feedback endpoint)
6. **Ask Another Question** or **Clear Form** to reset

Error paths (empty/short/oversized input, invalid jurisdiction, backend down, rate limit, blocked injection) show recoverable, accessible error UI — never stack traces.

## Architecture

Full diagram and component tables: **[docs/architecture.md](docs/architecture.md)** (Mermaid).

```mermaid
flowchart LR
    U[User] --> F[Next.js 14 frontend<br/>Vercel]
    F -->|POST /api/v1/ask| B[FastAPI backend<br/>Render]
    B --> S[Safety + validation<br/>prompt defense, output validator, safety layer]
    S --> A[AI orchestration<br/>classify → retrieve → prompt → LLM → validate]
    A --> L[LLM provider<br/>OpenAI or Anthropic<br/>server-side keys only]
    A --> R[Curated source table<br/>in-code]
    A --> F
```

## AI Workflow

**LLM-invoked (when a valid API key is configured server-side):** summary/explanation/next-steps generation only — JSON mode, low temperature, risk-guided system instructions.

**Rule-based (not LLM):** request classification, risk assessment, jurisdiction detection, legal category, source selection, clarification questions, prompt-injection scan, output validation, safety checks.

**Provider selection:** `OPENAI_API_KEY` (gpt-4o-mini) → else `ANTHROPIC_API_KEY` (claude-3-haiku) → else an explicit **MockProvider** that labels its output as mock (visible in responses when no valid key is set).

**Not used in the live path:** embeddings/vector search (an embedding model name exists in settings but no retrieval call uses it), document processing, real-time legal data.

## Safety & Responsible AI

- Server-attached disclaimer on **every** response; persistent frontend banner
- High-risk keyword rules (arrest, eviction, domestic violence, deadlines, etc.) force escalation guidance + uncertainty notes — enforced by validator, not just prompted
- Definitive-outcome language ("you will win", "guaranteed") detected → modified or fallback
- Unauthorized-practice-of-law patterns detected → modified
- Fabrication heuristics flag statute/case-style citations not backed by provided sources
- High-risk situations (violence, arrest, imminent deadlines) get prominent UI escalation toward attorneys/legal aid/public defenders
- The product never claims to be a lawyer and states it provides information, not advice

## Security

- **Secrets:** AI and service keys are server-side only (Render env vars). Frontend bundle contains only `NEXT_PUBLIC_API_URL`. `.env` files are gitignored; `.env.example` has placeholders.
- **Rate limiting:** 30 requests/minute/IP (health checks exempt) with `Retry-After` and standard rate-limit headers
- **Input limits:** question ≤ 5000 chars, context ≤ 2000, body ≤ 1 MB
- **Headers:** CSP, `X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`
- **CORS:** restricted allow-list including the production Vercel origin
- **Errors:** generic `{error, code}` responses; stack traces only in server logs
- **Prompt injection:** strict scan/sanitize/block before the LLM; response-side injection-artifact check as defense in depth

> **Note:** a Render API token was previously committed in `backend/check-deploy.ps1`; it has been removed from the working tree (now reads `RENDER_API_KEY` from the environment). That token remains in git history and **should be revoked/rotated in the Render dashboard.**

## Accessibility

Implemented (not a formal WCAG certification claim):

- Semantic structure: `header` / `main` / `footer`, labelled sections, heading hierarchy
- All form controls have associated labels; hints and errors wired via `aria-describedby` / `aria-invalid`
- Keyboard operable form (Ctrl+Enter submits), visible focus rings on controls
- Loading state announced (`aria-live`), errors use `role="alert"`, status badge updated
- Screen-reader-only live text for submit/loading status
- Dark-mode color variants on form surfaces
- Responsive layout from ~375px to desktop

**Not claimed:** WCAG 2.1 AA compliance has not been verified by a formal audit or assistive-technology testing pass.

## Testing

### Backend (52 tests)
```bash
cd backend
python -m pytest -q
```
Covers health, ask happy path, validation (empty/short/long/invalid jurisdiction), high-risk escalation, conversation IDs, feedback, plus AI workflow, prompt defense, safety, and output validation behavior.

### Frontend (33 tests)
```bash
cd frontend
npm test
npm run lint
npm run type-check
npm run build
```
Covers the `useLegalAssistant` hook (ask/error/reset/feedback), `QuestionInput` validation and a11y attributes, and accessible component behavior.

## Technology Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS 4 |
| Frontend tests | Jest, React Testing Library, jsdom |
| Backend | FastAPI, Pydantic v2, Uvicorn, Python 3.11+ |
| Backend tests | Pytest, pytest-asyncio, httpx (ASGI) |
| AI | OpenAI `gpt-4o-mini` *or* Anthropic `claude-3-haiku` (server-side key); mock fallback |
| Hosting | Vercel (frontend), Render (backend), GitHub (source, Render auto-deploy) |

## Project Structure

```
PROJECT/
├── frontend/                 # Next.js app
│   ├── src/app/page.tsx      # Workspace UI
│   ├── src/components/       # Form, response, a11y, disclaimers, error UI
│   ├── src/hooks/            # useLegalAssistant
│   ├── src/lib/api.ts        # API client
│   └── src/types/            # Shared types
├── backend/                  # FastAPI app
│   ├── app/main.py           # App, CORS, middleware, error handlers
│   ├── app/api/              # Routes, rate-limit/security middleware
│   ├── app/models/           # Pydantic schemas
│   ├── app/services/         # AI workflow, safety, validation, LLM client, sources
│   └── app/tests/            # Pytest suite
├── docs/architecture.md      # Architecture diagram + component docs
├── .env.example              # Config template (no secrets)
└── README.md
```

## Environment Variables

Template: [.env.example](.env.example)

| Variable | Where | Required | Purpose |
|----------|-------|----------|---------|
| `OPENAI_API_KEY` | Render (backend) | one of the two keys | Real LLM responses (preferred) |
| `ANTHROPIC_API_KEY` | Render (backend) | alternative | Real LLM responses |
| `SECRET_KEY` | Render | recommended | App secret (≥ 32 chars) |
| `BACKEND_CORS_ORIGINS` | Render | yes | Allowed frontend origins |
| `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | Render | no | Defaults 30 / 60 |
| `LOG_LEVEL` | Render | no | Default `INFO` |
| `NEXT_PUBLIC_API_URL` | Vercel (frontend build) | yes in prod | Backend base URL (public by design) |
| `RENDER_API_KEY` | local only (optional) | no | For `backend/check-deploy.ps1` helper |

Without a valid AI key, the backend still runs safely but returns **explicitly labeled mock content**.

## Local Development

### Prerequisites
- Node.js 20+
- Python 3.11+
- An OpenAI **or** Anthropic API key (optional for UI-only work; mock mode otherwise)

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Unix: source .venv/bin/activate
pip install -r requirements.txt
copy ..\.env.example .env   # add your keys
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
# .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Visit `http://localhost:3000` (UI) and `http://localhost:8000/docs` (OpenAPI).

## Deployment

- **Frontend:** Vercel — `https://frontend-mocha-six-92.vercel.app/`  
  Build with `NEXT_PUBLIC_API_URL=https://legalai-backend-6jio.onrender.com`
- **Backend:** Render web service via [`backend/render.yaml`](backend/render.yaml) — `uvicorn app.main:app`, health check `/api/v1/health`, auto-deploy on push to `main`
- **CI:** none configured in this repository (tests run locally/Manually)

## Assumptions

- English-only UI and responses
- Jurisdiction coverage limited to the configured enum; unknown → clarification question + general information
- Sources are a small **curated in-code table** (US Federal and California entries today), not a comprehensive legal database
- Conversation context lives in backend process memory only (lost on restart/deploy, not shared across instances)
- Feedback is stored in memory for demonstration only

## Limitations

1. **Not legal advice** — general information only
2. **AI-generated content** — may be inaccurate; verify with official sources
3. **Curated sources only** — no live legal research; many jurisdictions/categories have no matching source (UI states this honestly)
4. **No document upload**, no user accounts, no persistent sessions
5. **No real-time legal data** — model training-cutoff knowledge
6. **Mock mode** when no valid LLM key is configured (responses are labeled as mock)
7. **Not formally audited** for WCAG 2.1 AA or independent security review
8. Rate limit is per-instance in-memory (resets on deploy; not distributed)

## Future Improvements

- [ ] Verified production LLM key management + provider observability
- [ ] Persistent, encrypted conversation history
- [ ] Broader source coverage / real legal-aid directory integrations
- [ ] Document upload and analysis
- [ ] Multi-language support
- [ ] Formal accessibility audit (AT testing) toward WCAG 2.1 AA
- [ ] Distributed rate limiting and session stores
- [ ] Admin view for feedback analysis

## Repository Hygiene

- `.gitignore` excludes `node_modules`, virtualenvs, `.env*`, build outputs, coverage, `*.tsbuildinfo`
- No secrets in the current tree (`.env.example` placeholders only)
- One branch (`main`); repository size ≈ 0.3 MB (limit: 10 MB)
- Public GitHub repository

## License

MIT — see [LICENSE](LICENSE).

## Contributing

This is a hackathon submission. For any production use, independently security-audit the system, verify legal information with qualified attorneys, and add real data-retention/privacy controls.
