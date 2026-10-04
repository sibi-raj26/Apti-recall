# APTIRECALL

AI-Powered Aptitude Learning, Solving & Recall Platform

## Technology Stack

- Backend: Python 3.11 + Django 5 + Django REST Framework
- Database: PostgreSQL (production), SQLite (development)
- Auth: JWT (djangorestframework-simplejwt)
- Task Queue: Celery + Redis
- Frontend: React 19 + Vite + TypeScript
- Mobile: React Native + Expo (SDK 57)
- OCR: Tesseract / PaddleOCR (Phase 7+)
- Math: SymPy (Phase 6+)
- AI: Ollama / OpenAI-compatible LLM (Phase 8+)
- TTS: edge-tts (Phase 9+)

## Repository Structure

```
aptirecall/
├── backend/          # Django REST Framework API
├── frontend/         # React + Vite + TypeScript web app
├── mobile/           # React Native + Expo Android app
├── shared/           # Shared types/constants/utils
├── docs/             # Project documentation
├── tests/            # Cross-cutting integration tests
├── scripts/          # Utility scripts
├── ARCHITECTURE.md   # Full system architecture
├── .env.example      # Environment variable template
├── .gitignore
├── requirements.txt  # Python dependencies
└── manage.py         # Django entry point
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+
- PostgreSQL 15+ (for production)
- Redis (for Celery, Phase 5+)

## Backend Setup

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r ..\requirements.txt
python ..\manage.py migrate
python ..\manage.py runserver
```

The backend runs at `http://localhost:8000`.

Health check: `GET http://localhost:8000/api/health/`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Mobile Setup

```bash
cd mobile
npx expo install
npx expo start
```

Use Expo Go app or run `npx expo run:android` for a development build.

## Environment Configuration

Copy `.env.example` to `.env` and update values for your environment. Do not commit `.env`.

Key variables:
- `DJANGO_SECRET_KEY` — Django secret key
- `DATABASE_URL` — Database connection (PostgreSQL recommended for production)
- `AI_PROVIDER` — `ollama` or `openai`
- `OLLAMA_BASE_URL` — Local Ollama URL
- `OLLAMA_MODEL` — Model name for Ollama

## Current Development Phase

Phase 6: Mathematical Verification Engine

## Solving Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/solve/text/ | Yes | Solve an aptitude question from text |
| GET | /api/solve/history/ | Yes | Get current user's solve history |
| POST | /api/solve/verify/ | Yes | Verify a solve result deterministically |

### Solve Request

```json
{
  "question_text": "A number is increased from 200 to 250. What is the percentage increase?"
}
```

### Solve Response

```json
{
  "success": true,
  "data": {
    "question_text": "...",
    "topic": {"id": 1, "name": "Percentage"},
    "problem_type": {"id": 1, "name": "Percentage Increase"},
    "concept": "...",
    "approach": "...",
    "steps": [...],
    "final_answer": "...",
    "shortcut": "...",
    "confidence": 0.95,
    "verification_status": "VERIFIED",
    "verification_details": {"method": "PERCENTAGE_CHANGE", "confidence": 1.0, "details": "...", "checks": []},
    "source": "ai_generated",
    "attempt_id": 123
  }
}
```

### Verification Status

- `VERIFIED` — deterministic mathematical checks confirm the answer
- `FAILED` — deterministic checks found a contradiction
- `UNABLE_TO_VERIFY` — the engine could not safely verify the answer

### Verification Methods

- `DIRECT_CALCULATION` — independent arithmetic check
- `STEP_VERIFICATION` — re-performed AI steps
- `ALGEBRAIC` — SymPy substitution/simplification
- `SUBSTITUTION` — reverse-calculation check
- Strategy-specific methods: `PERCENTAGE_OF`, `PERCENTAGE_CHANGE`, `PROFIT_LOSS`, `AVERAGE`, `SIMPLE_INTEREST`, `COMPOUND_INTEREST`, `TIME_WORK`, `PIPES_CISTERNS`, `TIME_SPEED_DISTANCE`, `TRAIN`, `HCF_LCM`, `PROBABILITY`, `PERMUTATION_COMBINATION`, `RATIO`, `NUMBER_SYSTEM`, `AGES`, `DEFAULT`

## AI Configuration

Environment variables:
- `AI_PROVIDER` — `ollama` or `openai` (default: `ollama`)
- `OLLAMA_BASE_URL` — Ollama server URL (default: `http://localhost:11434`)
- `OLLAMA_MODEL` — Ollama model name (default: `llama3.1:8b`)
- `OPENAI_API_KEY` — OpenAI API key (required if `AI_PROVIDER=openai`)
- `AI_REQUEST_TIMEOUT` — LLM request timeout in seconds (default: `120`)

## Documentation

See `docs/` for detailed documentation:
- `development-progress.md` — phase-by-phase progress
- `ARCHITECTURE.md` — full system architecture

## License

College project — not licensed for redistribution.
