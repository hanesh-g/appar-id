---
type: Playbook
title: Native Windows setup
description: Run the application with PowerShell, uv, Node.js, and native PostgreSQL without Ubuntu or WSL.
tags: [windows, powershell, setup, git]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-26T16:12:00Z"}
sources:
  - resource: "User requirement: native Windows, no Ubuntu, author hanesh-g with the supplied email"
  - resource: 02-technical-design.md
---

# 08 — Native Windows setup

## What runs on your computer

- VS Code and the official OpenAI Codex extension.
- Git for Windows.
- uv, which installs/manages Python 3.12 for this project.
- Node.js 22.12+ in the Node 22 line, or Node 24. Node 24 was used for the verified frontend build.
- Native PostgreSQL 16. Docker is an alternative, not a requirement.

No Ubuntu, WSL, Linux terminal, or Docker Desktop is required for the native path below. Render and the GitHub Actions runner can use Linux independently of your Windows setup.

## 1. Install prerequisites

Install [VS Code](https://code.visualstudio.com/) and [Git for Windows](https://git-scm.com/downloads/win). Install Node.js from its [official downloads](https://nodejs.org/en/download).

In PowerShell, install uv:

```powershell
winget install --exact --id astral-sh.uv
```

Open a new PowerShell terminal after installation. Verify:

```powershell
git --version
uv --version
node --version
npm.cmd --version
```

Use `npm.cmd` and `npx.cmd` in PowerShell. These invoke Node's Windows command wrappers directly, avoiding both PowerShell execution-policy errors and strict-mode failures in `npm.ps1` such as a missing `$MyInvocation.Statement` property. The checked-in helpers use `npm.cmd` while retaining strict mode for their own error checking. Do not change machine-wide execution policy merely to run npm.

If setup already created `.env` and then failed in `npm.ps1`, pull the helper fix and rerun `scripts/Initialize-Local.ps1`. It preserves the existing `.env` and chosen password. For an immediate manual dependency-install retry from the repository root, run `npm.cmd --prefix frontend ci`.

## 2. Get the repository and set your identity

For a new checkout:

```powershell
git clone https://github.com/hanesh-g/appar-id.git
Set-Location appar-id
code .
```

In the repository's VS Code PowerShell terminal:

```powershell
git config --local user.name "hanesh-g"
git config --local user.email "haneshgourishetti@gmail.com"
git config --local user.useConfigOnly true
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

Both identities must show the name/email above. This is repository-local, so it does not rename commits for other projects. GitHub links commits to an account using a verified email; ensure this email is verified in your GitHub settings. Author identity is separate from GitHub push authentication. Use Git for Windows' browser-based credential manager for sign-in. Never paste a token into a Codex task.

The original documentation commit was initially created with an inherited, incorrect author. The author correction rewrites that initial commit. If you cloned the old history and have local work, preserve it first and use a fresh clone for this corrected history. Do not use a destructive reset on your only copy of local changes.

## 3. Initialise dependencies and private local settings

From the repository root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\Initialize-Local.ps1
```

This session-only policy permits the checked-in PowerShell helpers. The initializer verifies tools, sets this repository's author identity, installs Python/backend/frontend dependencies from lockfiles, and creates an ignored `.env` only if none exists.

Choose a local demo password of at least 12 characters when prompted. It is used for the three synthetic demo accounts. Keys and the application database password are generated without printing their values. Keep `.env` private; do not commit it or paste its contents into a chat. A repeated initialization preserves the existing `.env`.

## 4. Install native PostgreSQL and create isolated databases

Use the installer linked from [PostgreSQL's Windows download page](https://www.postgresql.org/download/windows/). Select PostgreSQL 16, use port 5432, and remember the password chosen for the local `postgres` administrator. The installer may require Windows administrator permission.

After its Windows service is running, execute from the project root:

```powershell
uv run --project backend python scripts/create_local_database.py
```

Enter the local PostgreSQL administrator password when prompted. It stays local and is not printed. The helper creates an `apaar_app` login plus `apaar` and `apaar_test` databases. It refuses to replace an existing role or database. It does not drop data or need the PostgreSQL command-line tools on PATH.

If those names already exist, use your existing authorised database settings in `.env`, or create a fresh target with your administrator. Do not delete an existing database to make setup pass. This helper is for the default local host/port; a managed database or custom port needs an explicitly configured `DATABASE_URL` and dedicated test URL.

## 5. Apply migrations and seed synthetic accounts

```powershell
Set-Location backend
uv run --frozen alembic upgrade head
uv run --frozen python -m app.seed --demo
Set-Location ..
```

Seed preserves existing accounts, passwords, programmes, and admissions. Accounts are:

| Email | Access |
|---|---|
| `collegea@example.test` | First institution administrator. |
| `collegeb@example.test` | Second institution administrator. |
| `officer@example.test` | Cross-institution read access. |

Use the demo password you chose during initialization. Changing `DEMO_PASSWORD` after accounts have been seeded does not reset an existing password. The seed intentionally preserves existing accounts. No password-reset endpoint is implemented; use a new disposable demo database or an explicitly reviewed administrator operation if a demo password is lost.

For the new correction, audit, student, and verifier features, follow [the safe update and complete demo walkthrough](12-demo-walkthrough.md). It adds extension keys, migrates, and creates four additional synthetic accounts while preserving existing data/passwords.

## 6. Start both applications

VS Code terminal 1, from the repository root:

```powershell
.\scripts\Start-Backend.ps1
```

VS Code terminal 2, from the repository root:

```powershell
.\scripts\Start-Frontend.ps1
```

Open the frontend address shown by Vite in your browser. Sign in as the first institution. With `APP_ENV=local`, the backend supports both `http://localhost:5173` and `http://127.0.0.1:5173` when either is configured. This also supports older generated `.env` files after updating the code and restarting the backend. Hosted mode does not expand its explicit allowlist. `VITE_API_BASE_URL` defaults to the local backend's `/api/v1` route prefix.

If sign-in reports that the API cannot be reached, keep the backend terminal open and check readiness from another PowerShell terminal with `Invoke-RestMethod http://127.0.0.1:8000/api/v1/health`. A connection failure means no reachable API at that address; an HTTP 503 means its database readiness check failed. A healthy response with a browser-only failure calls for checking the browser origin and frontend API URL. Do not change passwords or regenerate keys to troubleshoot a browser connection error.

## 7. Walk through the demo

1. Confirm programmes are present.
2. Upload `fixtures/intake-65.csv` for `2026-27`.
3. Inspect the five missing-identity warnings and the intake preview.
4. Commit acceptable rows.
5. Overview must show 65 active admissions, five identity gaps, and five above the basic limit of 60.
6. Upload `fixtures/corrections.csv` and commit. No new admissions should be created.
7. Open an enrolment and its history. Optionally record a withdrawal with a valid end date.
8. Check activity history. Sign in as the second institution to see that the first institution's records are absent.

Other files in `fixtures/` demonstrate identity mismatches, malformed rows, duplicate keys, and the maximum supported local batch.

To demonstrate outage recovery locally: set `MOCK_REGISTRY_OUTAGE=true` in your private `.env`, restart only the backend, upload `identity-cases.csv`, then commit. Restore `false`, restart the backend, and use the identity retry action. Use a fresh demo dataset when exact fixture counts matter.

## 8. Run checks

Backend integration tests **reset the dedicated database named in `TEST_DATABASE_URL`**. It must end in `_test` and contain no data you need. The normal `apaar` database is not the test target.

```powershell
Set-Location backend
uv run --frozen ruff check app migrations tests
uv run --frozen ruff format --check app migrations tests
uv run --frozen pytest -q
Set-Location ../frontend
npm.cmd run lint
npm.cmd run format:check
npm.cmd run test -- --run
npm.cmd run build
```

For the browser smoke, keep both servers running and use the synthetic seeded accounts:

```powershell
npx.cmd playwright install chromium
npm.cmd run smoke
```

The smoke mutates the synthetic first-institution dataset. It expects a fresh synthetic dataset plus both extension flags, their retained keys, all migrations, and seven seeded accounts. It must not be pointed at a real-data deployment. A run changes admission/case/review/consent history, so repeating exact-count tests needs another explicitly disposable database; do not reset shared data.

## 9. Continue with Codex

Install the official Codex extension from OpenAI in the Windows VS Code workspace. Follow the [official IDE setup](https://developers.openai.com/codex/ide). Point it to `AGENTS.md`, `docs/index.md`, and the current checklist.

```text
Read AGENTS.md, README.md, docs/index.md, and the current checklist.
Inspect the implementation before changing it.
Continue with the next verified-priority task.
Use native Windows/PowerShell instructions; do not require WSL or Ubuntu.
Verify repository-local author and committer are
hanesh-g <haneshgourishetti@gmail.com> before any commit.
Use production backend practices and run relevant checks.
Do not mark hosted deployment or optional features complete without evidence.
```

## Validation boundary

The application and PostgreSQL tests were executed in the cloud development machine. The PowerShell scripts and native PostgreSQL instructions are supplied for Windows but have not been executed on a Windows machine in this session. Record any Windows-specific failure with its command and error; never share `.env` or credential values.
