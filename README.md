# LegalAI Access

An AI-powered legal information platform built for the Hack2Skill PromptWars Virtual Challenge — **AI for Legal Assistance & Access**.

## Problem Statement

Access to legal information is a fundamental barrier to justice. Most people cannot afford attorneys for routine legal questions, and existing resources are often fragmented, jargon-heavy, or jurisdiction-specific without clear guidance. This platform bridges that gap by providing plain-language legal information with clear risk assessment, verified source citations, and appropriate escalation guidance.

## Solution

LegalAI Access is a production-quality web application that:

1. **Accepts natural-language legal questions** from users
2. **Classifies the request type** (deadline inquiry, procedural guidance, rights explanation, etc.)
3. **Assesses risk level** (low/medium/high/critical) based on keywords and legal category
 4. **Detects or accepts jurisdiction** for accurate, location-specific information
 5. **Retrieves verified legal sources** (statutes, regulations, government publications) when available
 6. **Generates structured AI responses** with clear disclaimers, uncertainty notes, and practical next steps
 7. **Provides escalation guidance** for high-risk situations (eviction, arrest, deportation, domestic violence, etc.)
 8. **Collects user feedback** to improve quality over time

## Key Features

- **Multi-step AI workflow** — Not a single chatbot prompt; uses classification → retrieval → generation → validation pipeline
- **Risk-aware responses** — Critical/high-risk queries receive prominent escalation guidance
- **Source transparency** — Verified sources shown with citations, URLs, and verification status
- **Jurisdiction awareness** — Supports US federal, CA/NY/TX, UK, Canada, Australia, EU, and international
- **Responsible AI disclaimers** — Clear communication that this is information, not legal advice
- **Accessible by default** — WCAG 2.1 AA compliant, keyboard navigable, screen reader friendly
- **Security hardened** — Rate limiting, CSP, input validation, secure headers, no secrets in repo
- **Comprehensive testing** — Unit, API, AI behavior, security, and frontend tests

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Frontend      │────▶│   Backend       │────▶│   AI Provider    │
│   (Next.js 14)  │     │   (FastAPI)     │     │   (OpenAI/       │
│                 │     │                 │     │    Anthropic)    │
│ - React 18      │     │ - Pydantic v2   │     │                  │
│ - TypeScript    │     │ - Rate Limiting │     │ - GPT-4o-mini    │
│ - Tailwind CSS  │     │ - Security Hdrs │     │ - Embeddings     │
│ - Jest/RTL      │     │ - CORS          │     │                  │
└─────────────────┘     └─────────────────┘     └──────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  AI Workflow    │
                       │                 │
                       │ 1. Classify     │
                       │ 2. Jurisdiction │
                       │ 3. Risk Level   │
                       │ 4. Retrieve     │
                       │ 5. Clarify      │
                       │ 6. Generate     │
                       │ 7. Validate     │
                       └─────────────────┘
```

## Technology Stack

### Frontend
- **Next.js 14** (App Router)
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Zod** for runtime validation
- **Jest + React Testing Library** for testing

### Backend
- **FastAPI** with Python 3.11+
- **Pydantic v2** for validation and settings
- **Uvicorn** ASGI server
- **Pytest** for testing

### AI Services
- **Primary**: OpenAI GPT-4o-mini (chat) + text-embedding-3-small (embeddings)
- **Alternative**: Anthropic Claude 3 Haiku
- **Where AI is used**: Request classification, risk assessment, response generation, source retrieval (embeddings)

### Infrastructure
- **Development**: Local with hot reload
- **Production**: Docker-ready, deployable to Cloud Run, Fly.io, Railway, etc.
- **Repository size**: < 10 MB (no node_modules, venv, build artifacts)

## Setup Instructions

### Prerequisites
- Node.js 20+
- Python 3.11+
- OpenAI API key (or Anthropic)

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
cp ../.env.example .env.local
# Edit .env.local if needed
npm run dev
```

### Run Both (Development)
```bash
# Terminal 1
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Visit `http://localhost:3000` (frontend) and `http://localhost:8000/docs` (API docs).

## Environment Variables

See `.env.example` for all options. Required:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (or ANTHROPIC_API_KEY) |
| `SECRET_KEY` | 32+ character secret for JWT/sessions |
| `BACKEND_CORS_ORIGINS` | Comma-separated allowed origins |

Optional:
| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | gpt-4o-mini | Chat model |
| `OPENAI_EMBEDDING_MODEL` | text-embedding-3-small | Embedding model |
| `BACKEND_PORT` | 8000 | Backend port |
| `RATE_LIMIT_REQUESTS` | 30 | Requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | Rate limit window |
| `LOG_LEVEL` | INFO | Logging level |

## Running Tests

### Backend
```bash
cd backend
source .venv/bin/activate
pytest -v --cov=app --cov-report=term-missing
```

### Frontend
```bash
cd frontend
npm run test:ci
```

### All Tests
```bash
# From root
cd backend && pytest && cd ../frontend && npm run test:ci
```

## Building for Production

### Backend
```bash
cd backend
pip install -r requirements.txt
# Run with gunicorn: gunicorn -k uvicorn.workers.UvicornWorker app.main:app
```

### Frontend
```bash
cd frontend
npm run build
npm start
```

### Docker (Optional)
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "app.main:app"]

# Frontend Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --production
CMD ["npm", "start"]
```

## Security Architecture

### Implemented Protections
- **Secrets management**: Only via environment variables; `.env.example` provided; no secrets in repo
- **Rate limiting**: 30 requests/minute per IP (configurable)
- **Input validation**: Pydantic v2 on all endpoints; max payload 1MB
- **Security headers**: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **CORS**: Restricted to configured origins only
- **Prompt injection mitigation**: System prompts not overridable; user input sanitized
- **Error handling**: No stack traces or internal details in responses
- **Dependency scanning**: `pip-audit` / `npm audit` in CI

### AI Safety
- System prompts separated from user content
- Output validation against schema
- Fabrication prevention: explicit instructions not to invent laws/citations
- Uncertainty acknowledgment in all responses
- High-risk escalation pathways

## Accessibility

WCAG 2.1 AA compliance:
- **Semantic HTML** — Proper heading hierarchy, landmarks, roles
- **Keyboard navigation** — All interactive elements reachable and operable
- **Focus management** — Visible focus indicators, logical tab order
- **Screen reader support** — ARIA labels, live regions, descriptive text
- **Color contrast** — 4.5:1 minimum for text, 3:1 for UI components
- **Touch targets** — Minimum 44×44px
- **Responsive design** — Works on mobile, tablet, desktop
- **Reduced motion** — Respects `prefers-reduced-motion`
- **High contrast** — Supports `prefers-contrast: high`

## Limitations

1. **Not legal advice** — This platform provides general legal information only
2. **AI-generated content** — May contain inaccuracies; always verify with official sources
3. **Jurisdiction coverage** — Limited to configured jurisdictions; others fall back to general info
4. **Source database** — Uses curated verified sources; not exhaustive legal research
5. **No document upload** — Cannot review user-provided documents (future enhancement)
6. **No persistent sessions** — Conversation state not stored (future enhancement)
7. **English only** — Single language support (future enhancement)
8. **No real-time data** — Legal information current as of model training cutoff

## Responsible AI / Legal Disclaimer

> **This platform provides general legal information only and does not constitute legal advice. The information provided is generated by AI and may contain inaccuracies. For legal matters that could significantly affect your rights, liberty, or finances, please consult with a qualified attorney licensed in your jurisdiction. No attorney-client relationship is created by using this service.**

The AI is instructed to:
- Never fabricate laws, statutes, cases, citations, or sources
- Clearly distinguish between user-provided facts, general information, verified sources, and AI-generated explanations
- Acknowledge uncertainty and limitations
- Escalate high-risk situations to professional legal help
- Not make legal conclusions or predictions about outcomes

## Future Improvements

- [ ] Document upload and analysis
- [ ] Persistent conversation history with encryption
- [ ] Multi-language support (Spanish, French, etc.)
- [ ] Integration with legal aid organization directories
- [ ] Real-time legal data feeds (court calendars, statute updates)
- [ ] User accounts with saved queries
- [ ] Offline-first PWA support
- [ ] Advanced RAG with vector database (Pinecone, Weaviate)
- [ ] Fine-tuned legal domain model
- [ ] A/B testing framework for response quality
- [ ] Admin dashboard for feedback analysis
- [ ] Webhook integration for legal aid partners

## Repository Hygiene

- `.gitignore` excludes: `node_modules`, `.venv`, `.env`, build artifacts, caches
- `.env.example` provided with all configuration options
- No secrets, credentials, or private keys in repository
- Repository size < 10 MB (verified)

## License

MIT License — See LICENSE file for details.

## Contributing

This is a hackathon submission. For production use, please:
1. Conduct independent security audit
2. Verify all legal information with qualified attorneys
3. Implement proper data retention and privacy policies
4. Add comprehensive monitoring and alerting
5. Perform load testing and capacity planning