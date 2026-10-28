---
type: Deployment Guide
title: Deploy the synthetic demo to Render and Vercel
description: A Windows-friendly sequence for managed PostgreSQL, the Python API, private hosted settings, and the Vite frontend.
tags: [apaar, deployment, render, vercel, windows]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-28T07:52:47Z"}
sources:
  - resource: 09-backend-engineering.md
  - resource: 12-demo-walkthrough.md
  - resource: 14-demo-video-script.md
---

# 16 — Deploy to Render and Vercel

Use **Render PostgreSQL → Render Python API → Vercel frontend → final CORS setting**. Your Windows computer needs no Ubuntu or WSL. TablePlus is a database client; a hosted API needs hosted PostgreSQL. The new cloud database starts empty: local databases/imported records are not uploaded by pushing Git.

These instructions are checked against this repository. No Render/Vercel account has been supplied, so a hosted deployment, platform UI labels, current prices and account-specific plan limits have not been executed/verified. Official hosting-documentation requests were blocked in this environment. Use the current dashboard for available plans, database expiry and idle-service behaviour. This remains a synthetic demo with simulated institution/APAAR checks.

## 1. Update Windows and generate private hosting settings

From your actual repository root:

```powershell
Set-Location D:\Projects\appar-id\appar-id
git pull --ff-only
uv run --project backend --frozen python scripts/configure_render.py
notepad .env.render
```

The helper creates an ignored **`.env.render`**, separate from your normal local `.env`. It generates a JWT secret, four independent base64 32-byte keys, and a demo password without printing them. Re-running preserves the existing file. Keep the file privately; do not commit, paste into chat, or publish its contents. Do not regenerate keys after the hosted database contains encrypted records or audit history.

Leave Notepad available privately for the next steps. The file has placeholders for the hosted database URL and frontend origin. `DEMO_PASSWORD` in this file is the password for the newly seeded hosted accounts; your old local password does not automatically apply.

## 2. Create hosted PostgreSQL on Render

1. Open [Render](https://dashboard.render.com/) and sign in. Create a **PostgreSQL** database from the New menu.
2. Name it `apaar-db`. Choose a supported PostgreSQL version (16 is covered by the local integration checks) and a region. Use that same region for the API.
3. Select the database plan shown in your account. Check its cost, retention/expiry and availability for your recording before creating it. No specific free-database entitlement is assumed.
4. Wait until the database is available. Copy its **Internal Database URL** privately from its connection details.
5. In `.env.render`, replace the entire value of `DATABASE_URL` with that internal URL. Copy the provider URL exactly; the application accepts `postgres://`, `postgresql://`, and `postgresql+psycopg://` schemes. Do not use `localhost` or the Windows database URL.
6. For now, leave the placeholder `ALLOWED_ORIGINS=https://replace-with-your-project.vercel.app`. This enables no real frontend; replace it with the actual Vercel origin in step 7. Backend health checks do not depend on browser CORS.

Use the **external** database connection details only if connecting TablePlus from Windows. Follow Render's external-access and TLS requirements for that connection. The API uses the internal URL when both services share its supported private network/region.

## 3. Create the Python web service

Create a **Web Service** on Render and connect `hanesh-g/appar-id`. Authorise repository access if prompted. Use the manual web-service form for this guide; `render.yaml` is an alternative blueprint, not a second service to create.

| Setting | Value |
|---|---|
| Name | `apaar-api`, or another available name |
| Branch | `main` |
| Runtime | Python |
| Region | Same as PostgreSQL |
| Root Directory | `backend` |
| Build Command | `pip install uv==0.12.23 && uv sync --frozen --no-dev` |
| Health Check Path | `/api/v1/health` |
| Instances | One for this initial synthetic demo |
| Auto deploy | Off while establishing and recording the demo |

In the service's environment-variable controls, use its import/add-from-`.env` option if offered, and import the edited `.env.render`. Otherwise enter the same name/value pairs privately. `.env.render` is not uploaded by Git; the imported variables provide the settings at runtime. Enter `PYTHON_VERSION=3.12.14` before the initial build so the runtime matches the repository's Python 3.12 requirement.

The required settings are:

| Variable | Value/source |
|---|---|
| `PYTHON_VERSION` | `3.12.14` |
| `APP_ENV` | `demo` |
| `DATABASE_URL` | Render's private internal connection URL |
| `ALLOWED_ORIGINS` | Temporary placeholder now; exact Vercel origin in step 7 |
| `REGISTRY_MODE` | `mock` |
| `MOCK_REGISTRY_OUTAGE` | `false` |
| `JWT_SECRET` | Generated in the private file |
| `JWT_ISSUER` | `apaar-demo` |
| `JWT_AUDIENCE` | `apaar-web` |
| `PII_KEY`, `HMAC_KEY` | Two separate generated keys |
| `AUDIT_CHAIN_ENABLED` | `true` |
| `AUDIT_HMAC_KEY` | Its separate generated key |
| `AUDIT_KEY_ID` | `audit-v1` |
| `CONSENT_ENABLED` | `true` |
| `GRANT_TOKEN_KEY` | Its separate generated key |
| `GRANT_KEY_ID` | `grant-v1` |
| `DEMO_PASSWORD` | Generated in the private file; needed for the first seed |

Do not import `TEST_DATABASE_URL`, `LOCAL_DB_PASSWORD` or any Windows/local connection URL. All secrets belong to the backend. Only the public API base URL will go into Vercel.

## 4. Initialise the new database before starting the API

For the **first deployment of this fresh, single-instance synthetic demo**, enter this explicit first-deploy **Start Command**:

```sh
uv run --no-sync alembic upgrade head && uv run --no-sync python -m app.seed --demo && exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log
```

Then create/deploy the service. The commands run sequentially: migrate the selected database, seed the seven synthetic accounts/programmes, then start the API only if both succeed. The start command is executed by Render; it is not a PowerShell command and needs no local Linux installation. This first-demo route works without requiring an interactive Render Shell.

This is a deliberate one-time setup command, not an application startup side effect or the production migration strategy. Use it only for the fresh demo with one instance. On an existing live deployment, use a supported pre-deploy/release migration or a controlled administrator operation instead. Do not seed independently in multiple workers.

Wait for the build/deployment result. The logs should indicate successful migrations, seeded synthetic accounts and a listening API. The seed preserves existing accounts/passwords if accidentally repeated and never approves colleges or imports admission CSVs. It is not a reset command.

## 5. Verify the API and restore the normal start command

Copy the service's actual HTTPS URL from Render, for example `https://apaar-api-example.onrender.com`. The exact hostname can differ.

Open:

```text
https://YOUR-ACTUAL-API-HOST.onrender.com/api/v1/health
```

Expect:

```json
{
  "status": "ok",
  "database": "ok",
  "registry": "simulated",
  "audit_chain_enabled": true,
  "consent_enabled": true
}
```

This checks API/database readiness. The seeded login in step 8 also checks the required tables/accounts.

After the successful first migration/seed, change the Render Start Command to its ordinary value and deploy the settings change:

```sh
uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log
```

Future restarts now only start the API. `DEMO_PASSWORD` can be removed from Render after initial seeding; keep your private copy to sign in. Keep every encryption/lookup/audit/grant key and the key IDs unchanged across restarts and redeploys. For later schema changes, run `uv run --no-sync alembic upgrade head` as an explicit controlled release operation before compatible application activation.

## 6. Deploy the frontend to Vercel

Open [Vercel](https://vercel.com/new), import the same repository and create a project with these settings:

| Setting | Value |
|---|---|
| Branch | `main` |
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Node.js | 22.x (22.12 or newer) |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Before deploying, add the public frontend variable for the deployment environments you intend to use:

```text
VITE_API_BASE_URL=https://YOUR-ACTUAL-API-HOST.onrender.com/api/v1
```

Use the real Render HTTPS address, with **`/api/v1` included**. This is a build-time variable: redeploy the frontend after changing it. Keep database URLs, passwords, JWT and encryption keys out of Vercel frontend variables. Anything prefixed `VITE_` is bundled for browsers.

Deploy. Keep `frontend/vercel.json`; it already supplies the SPA rewrite and response headers. Copy the actual stable **production domain** from Vercel after the deployment. A per-commit preview URL can be different. Browser API requests can remain blocked until the CORS update in step 7; finish that step before attempting login.

## 7. Allow the actual frontend origin in Render

Go to Render's API environment settings. Replace the temporary `ALLOWED_ORIGINS` with your exact Vercel production origin:

```text
ALLOWED_ORIGINS=https://YOUR-ACTUAL-FRONTEND.vercel.app
```

Use only the origin: HTTPS plus hostname, with no route such as `/login`, `/records` or `/api/v1`. Save and deploy/restart the API settings change. Update the private `.env.render` to the same value for your retained configuration.

The two addresses serve different purposes:

| Location | Setting | Example shape |
|---|---|---|
| Vercel | `VITE_API_BASE_URL` | `https://api-host.onrender.com/api/v1` |
| Render | `ALLOWED_ORIGINS` | `https://frontend-host.vercel.app` |

If recording a Vercel preview instead, explicitly allow that exact preview origin too, using comma-separated origins. There is no automatic hosted `localhost` alias or wildcard allowlist. Do not use `*`.

## 8. Sign in and prepare the hosted recording

Open the stable Vercel URL. Use the generated `DEMO_PASSWORD` from your private file for these newly seeded accounts:

| Account | Role |
|---|---|
| `collegea@example.test` | Deccan / College A administrator |
| `collegeb@example.test` | Riverdale / College B administrator |
| `officer@example.test` | Officer |
| `student1@example.test`, `student2@example.test` | Synthetic students |
| `verifier1@example.test`, `verifier2@example.test` | Demo verifiers |

Confirm login, dashboard loading, and the Institution approval page. A fresh hosted dataset has both colleges pending, zero admissions and no consent work. Do not approve/import data as unrecorded preparation if you want the [141-step walkthrough](14-demo-video-script.md) to start in its stated fresh state. That guide approves both colleges and imports all three CSVs **on screen**. Select the fixture files from your Windows computer in the hosted upload form.

Your computer can be turned off without stopping the hosted API/database, subject to the hosting plan's lifecycle. TablePlus continues to be an optional client. Local records/passwords are not copied to the cloud by deployment. Browser reload requires sign-in again because the application keeps session tokens in tab memory; records remain in PostgreSQL.

Before filming, open the API health endpoint and sign in shortly beforehand. If the chosen web-service plan idles, wait for it to wake and complete a request before recording; check the actual dashboard for its behaviour. Keep credentials private and use synthetic data only.

## Troubleshooting

| Symptom | Check |
|---|---|
| Build uses the wrong Python or says Python 3.13 is unsupported | Set `PYTHON_VERSION=3.12.14` before the build; Root Directory must be `backend`. |
| `pyproject.toml` / `uv.lock` missing | The API root must be `backend`; do not use repository root as the service root with these commands. |
| Database connection targets localhost | Replace Render's `DATABASE_URL` with the managed internal URL. Local Windows PostgreSQL is not reachable as the host's localhost. |
| Missing `users`, `institution_approvals` or other tables | Run the explicit migration against the selected hosted database; health readiness alone does not initialise tables. |
| Cannot reach API / CORS failure | Verify the public API health URL, Vercel's base URL including `/api/v1`, and Render's exact frontend origin. Save/redeploy after changing settings. |
| Login says incorrect password | Use the hosted seed's generated password. Later changing `DEMO_PASSWORD` does not reset existing accounts. |
| Student/verifier cannot sign in | Check consent enabled, the separate grant key, migrations and successful extended account seed. |
| Admissions are blocked | Institution approval is required. The officer must review the synthetic evidence for the requested year/programme; this is demonstrated during recording. |
| Nested route returns a hosting 404 | Root Directory must be `frontend` so Vercel reads its checked-in `vercel.json`; redeploy after configuration changes. |
| Existing records cannot decrypt / audit signing fails after a redeploy | Restore the original retained backend keys and IDs; do not generate another set for the same database. |
| Different behaviour on a preview URL | Allow its exact origin, or use the stable production domain chosen for recording. |

## Deployment evidence

Locally executed checks passed: the private settings helper validates against typed application settings, creates four distinct base64 32-byte keys, preserves existing files, and keeps local settings intact. The exact first-demo start command was then run against a newly created isolated PostgreSQL database: migrations reached c8, all seven accounts were seeded, college/officer/student logins worked, admissions remained empty, and both colleges remained pending. The ordinary start command was tested on a restart with the same keys and unchanged audit watermark; health, login and integrity still passed. Static checks and documentation-link checks also passed. No hosted account resources were created.

These checks do not establish a deployed site. Keep hosted completion unchecked until you perform it in your accounts:

- [ ] Render database and API created and healthy.
- [ ] Migration/seed succeeded; normal start command restored.
- [ ] Vercel frontend uses the actual API URL; backend allows its exact production origin.
- [ ] Functional login and role pages load; nested route loads directly after sign-in as required.
- [ ] Full hosted admission/correction/officer/consent/revoke workflow executed on synthetic data.
- [ ] API restart preserves encrypted records and audit/grant behaviour with retained keys.
- [ ] Hosting expiry/idle/cost behaviour checked for the presentation.
