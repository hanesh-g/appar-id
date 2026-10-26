---
type: Engineering Standard
title: Backend engineering and deployment
description: Explain the implemented backend boundaries, safety controls, verification, and remaining deployment requirements.
tags: [python, backend, engineering, deployment]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-25T18:31:21Z"}
sources:
  - resource: 02-technical-design.md
  - resource: 05-progress-checklist.md
---

# 09 — Backend engineering and deployment

## Implemented engineering practices

| Concern | Implementation |
|---|---|
| Runtime and dependencies | Python 3.12; uv lock; compatible Pydantic v2/FastAPI/SQLAlchemy; timezone data installed for Windows. |
| Application lifecycle | App factory; engine/crypto initialized in lifespan and engine disposed at shutdown. No migrations/seed run as hidden server-start side effects. |
| HTTP boundary | Strict typed input models; explicit safe output schemas for records/batches/audit; UUID parsing; paginated record/history endpoints; bounded CSV input. |
| Domain logic | Validation, identity mapping, preview, commit, counts, and lifecycle rules in `services.py`/`rules.py`, separate from HTTP handling. |
| Data access | Shared scope-aware repository helpers; SQLAlchemy parameter binding; per-request sessions. |
| Data integrity | Alembic revisions; unique enrolment/person keys; checked identity links, version, lifecycle dates; programme/batch locks; rollback on failure. |
| Repeatability | Request idempotency; canonical upsert; unchanged rows are no-ops; repeat commit returns original outcome; seed preserves existing data. |
| Authentication | Argon2 passwords; fixed-algorithm JWT verification with issuer/audience/expiry; active-account check; bounded single-process login throttling. |
| Authorisation | Explicit role capabilities and institution scope on reads/edits/exports/batches/counts. Officers cannot edit core records; separately permitted interval decisions and audit checks are bounded. |
| Personal data | AES-GCM encrypted identity/staging payloads; separate HMAC lookup key; masked IDs; no general platform-wide institution search. |
| Configuration | Pydantic settings, secret types, generated local keys, hidden inputs in configuration errors, ignored `.env`, no wildcard CORS. |
| Observability | Structured safe logs, request IDs, timings, route templates, and audit request correlation; raw access/query-string logs disabled by start commands. |
| Error handling | Stable domain/validation/conflict/unavailable responses; unexpected errors log type/code locations rather than raw exception values or SQL parameters. |
| Testing | PostgreSQL integration tests, actual Alembic upgrade/downgrade checks, rollback/concurrent commit/isolation tests, frontend tests, real-browser core smoke. |
| Automation | GitHub Actions configuration with read-only repository permissions, pinned action SHAs, independent integration/smoke databases, and frozen installs. |

The actions workflow is checked in; its remote execution must be verified after push. Local passing checks do not prove that GitHub Actions or hosted deployment passed.

## Design choices

- The core intentionally uses synchronous SQLAlchemy and sync FastAPI endpoints. Blocking database work runs in the request thread pool; we do not mix sync database calls into async route handlers.
- The app processes at most 500 CSV rows and 2 MiB per upload. It has no durable job worker or claim of 50,000-row support.
- Transactions cover mutation plus history/audit. There is no partial-success write hidden behind a failed response.
- Keys must persist across restarts and redeploys. Losing encryption/HMAC keys can make records unreadable or unmatchable. A key-rotation procedure is later work.
- The mock registry is deterministic and provider-independent. Fuzzy names are not identity proof. A real registry remains a separate approved integration.
- Frontend tokens live in memory; reload requires login. Refresh-token/revocation infrastructure is not claimed.
- The frontend uses custom CSS and accessible native controls rather than adding Tailwind/shadcn generation to the first core. Charts are loaded separately from the login bundle.

## Deploy backend to Render

`render.yaml` is a proposed blueprint for a synthetic demo. It uses the free web-service plan; verify its current cold-start and availability limitations. A reliable judged demo may need a human-approved plan change.

1. Create/select a managed PostgreSQL database. Preserve its connection credentials and follow its supported TLS/certificate settings.
2. Connect the repository and use `backend` as the Render root directory.
3. Set `DATABASE_URL`, `JWT_SECRET`, `PII_KEY`, `HMAC_KEY`, `ALLOWED_ORIGINS`, `APP_ENV=demo`, and `REGISTRY_MODE=mock` in secure backend environment settings. Encryption/HMAC keys are distinct base64 32-byte keys; retain them. `ALLOWED_ORIGINS` is the exact Vercel frontend origin.
4. Build: `pip install uv==0.12.23 && uv sync --frozen --no-dev`.
5. Run `uv run --no-sync alembic upgrade head` against the chosen database **before activating the application**. Use a release hook if the plan supports it; otherwise use an explicitly controlled migration from an authorised machine. Do not run migrations independently in each server worker.
6. Seed once using `uv run --no-sync python -m app.seed --demo` with a securely supplied `DEMO_PASSWORD`. The blueprint does not seed automatically. Remove the seed-only variable from hosted settings after use if it is no longer required.
7. Start: `uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log`.
8. Check `/api/v1/health` and a functional login/upload/commit flow. Confirm the database has migrations, not just a reachable socket.

The blueprint does not create a database, enter secrets, execute migrations, or prove deployment by existing in Git. No Render/Vercel account access has been supplied in this session.

## Deploy frontend to Vercel

1. Root directory: `frontend`.
2. Build: `npm ci` then `npm run build`; output directory: `dist`.
3. Set public `VITE_API_BASE_URL` to the backend's HTTPS URL plus `/api/v1`. Never put keys or database credentials in a `VITE_` variable.
4. Use `frontend/vercel.json` for SPA routes.
5. Redeploy after API URL changes. Test direct navigation to a nested route and exact CORS behaviour from the deployed frontend origin.

## What remains before real-data production use

This code uses production-oriented practices. It is still a synthetic prototype. A real-data release needs a separate security/policy/operations gate: approved registry access and matching rules; applicable intake policy; legal basis and consent where required; retention/deletion; managed secret storage and key rotation; backups and restore drills; distributed throttling; operational alerts; dependency/security review; capacity testing; and incident ownership. Optional consent verification is not yet implemented.

Do not label the app government-approved, compliant, tamper-proof, fraud-proof, or production-certified based on its stack or local tests.

## Optional local audit integrity

After migrating, enable the separate audit key from `backend` with `uv run --frozen python ../scripts/configure_extensions.py --enable-audit`, then restart the API. The helper only changes ignored local/demo configuration, preserves existing secrets, and generates a new audit key only when absent. Enter the equivalent `AUDIT_CHAIN_ENABLED`, `AUDIT_HMAC_KEY`, and `AUDIT_KEY_ID` values securely on hosting; do not put them in frontend variables.

The migration creates genesis without needing a seed script. Schema-only test setups also bootstrap on first write. Once signing starts, retain the key and enabled setting; losing/changing them blocks new signed mutations. Key rotation is a separately planned migration, not regenerating a file. An officer can verify the chain under Activity history. The consistent snapshot reports its checked watermark and explicitly limits legacy/rollback claims. No external anchor, KMS, production audit certification, or hosted pass is implied.
