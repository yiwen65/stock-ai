# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: FastAPI app (`main.py`) with core logic in `app/` (`api/v1`, `engines`, `agents`, `services`, `models`, `tasks`).
- `backend/tests/`: `unit/`, `integration/`, and `e2e/` pytest suites.
- `frontend/`: Vite + React + TypeScript UI. Main code is in `frontend/src/` (`components`, `pages`, `services`, `stores`, `types`).
- `frontend/e2e/`: Playwright browser tests.
- `docs/`: implementation plans and phase/task tracking. `docker-compose*.yml` and `nginx/` handle local/prod infrastructure.

## Build, Test, and Development Commands
- Backend setup: `cd backend && pip install -r requirements.txt`
- Run backend API: `cd backend && uvicorn main:app --host 0.0.0.0 --port 8001 --reload`
- Backend tests + coverage: `cd backend && pytest tests/ --cov=app --cov-report=xml`
- Frontend setup: `cd frontend && npm ci`
- Run frontend dev server: `cd frontend && npm run dev` (Vite on `http://localhost:3000`)
- Frontend lint: `cd frontend && npm run lint`
- Frontend build: `cd frontend && npm run build`
- Frontend e2e tests: `cd frontend && npx playwright test`
- Local services: `docker-compose up -d` (PostgreSQL, Redis, InfluxDB, Celery, Flower)

## Coding Style & Naming Conventions
- Python: 4-space indentation, PEP 8 naming (`snake_case` functions/modules, `PascalCase` classes). Keep API schemas in `app/schemas` and business logic in `app/services` or `app/engines`.
- TypeScript/React: 2-space indentation, `PascalCase` component files (e.g., `StockTable.tsx`), `camelCase` for variables/functions, `.module.css` for scoped styles.
- Linting: backend uses `ruff check .` (CI); frontend uses ESLint (`npm run lint`).

## Testing Guidelines
- Backend: write pytest tests under `backend/tests/<unit|integration|e2e>/` with names like `test_<feature>.py`.
- Frontend: place Playwright specs in `frontend/e2e/` as `*.spec.ts`.
- For changes touching behavior, add or update tests and run relevant suites before opening a PR.

## Commit & Pull Request Guidelines
- Follow Conventional Commit style used in history: `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`.
- Keep commits focused and descriptive; avoid ambiguous messages.
- PRs should include:
  - concise summary and rationale,
  - linked issue/task (if available),
  - test evidence (commands + result),
  - UI screenshots for frontend changes.

## Security & Configuration Tips
- Copy `.env.example` to `.env` for local setup; never commit real secrets.
- Validate API, DB, and token settings before running Celery or deployment workflows.
