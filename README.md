# APAAR Student Data Platform — build pack

An AI-assisted SIH 2026 prototype with a Python FastAPI backend, PostgreSQL, and a React/TypeScript frontend. Native Windows development uses PowerShell. Ubuntu and WSL are not required. Deployment targets are Vercel and Render.

**Current state:** local core implemented and verified with PostgreSQL integration tests, frontend tests/build, and a real-browser journey. Hosted deployment is not yet configured or verified. APAAR checks are simulated; all provided student fixtures are synthetic. See the [current evidence](docs/05-progress-checklist.md).

## Start on Windows

Follow the [native Windows setup](docs/08-windows-setup.md). It covers tools, your Git identity, dependency installation, native PostgreSQL, migrations, seed accounts, startup, and checks. Docker is optional.

Your required repository-local author and committer are `hanesh-g <haneshgourishetti@gmail.com>`. The initializer and [Git identity helper](scripts/Set-GitIdentity.ps1) set both identity fields. GitHub account attribution also requires the email to be verified on GitHub.

Implemented core: institution-scoped login, programmes, CSV validation, mock identity checks, dry-run intake preview, transactional/idempotent commit, correction upload, enrolment status/history, dashboard, and safe audit history. Student-consent verification and an LLM assistant remain optional future features.

Extension progress: explicit role capabilities, versioned deterministic rule explanations, and illustrative category counts are locally checked. Click an issue explanation in a batch to inspect its pinned rule version. After pulling schema changes, run `uv run --frozen alembic upgrade head` from `backend` before restarting the API; migrations preserve existing data. See the extension checklist for what remains.

## Read in this order

| Document | Use it to answer |
|---|---|
| [Problem and scope](docs/01-problem-and-scope.md) | What problem do we solve, for whom, and what can the demo claim? |
| [Technical design](docs/02-technical-design.md) | What do we build, with which tools, data, APIs, and deployments? |
| [Feature specification](docs/03-feature-specification.md) | What must each feature do, including failure cases? |
| [Implementation phases](docs/04-implementation-phases.md) | In which order should AI and people build and verify it? |
| [Progress checklist](docs/05-progress-checklist.md) | What is finished, what is blocked, and where is the evidence? |
| [AI development workflow](docs/06-ai-development-workflow.md) | How do we give an AI agent bounded tasks and reliable project context? |
| [OKF assessment](docs/07-okf-assessment.md) | What is Open Knowledge Format, and how do we use it without adding deployment work? |
| [Native Windows setup](docs/08-windows-setup.md) | How do I run this on Windows without Ubuntu? |
| [Backend engineering and deployment](docs/09-backend-engineering.md) | Which engineering controls exist, and what remains before hosting or real-data use? |
| [APAAR ecosystem and differentiation research](docs/10-apaar-platform-research.md) | What do public peer projects already offer, what should distinguish our workflow, and which official UI/adoption questions remain unverified? |
| [Feature extension execution plan](docs/11-feature-execution-plan.md) | In which order should we build resolution/diff, rule help, categories, overlap review, audit integrity, and consent/QR, with which release gates? |

The `docs/` directory is an [OKF v0.2 knowledge bundle](docs/index.md). Its concept files contain YAML metadata and links for people and AI assistants. It needs no running OKF service.

## Working agreement

- Build the **CORE** features first. **NEXT** features are optional extensions. **LATER** features are outside this demo.
- Treat the PDF as a design source. The explicit decisions in these documents adapt it for Python and a smaller deployment.
- Use synthetic students only. Label all registry results as simulated.
- Do not use an LLM to decide identity, compliance, permissions, or admission counts.
- Never mark a task complete without the evidence specified in the checklist.
- Record changed assumptions and API contracts before dependent work starts.

## Sources and uncertainties

Primary input: *APAAR ID Student Data Platform (SIH26263): Phase-by-Phase Build Guide*, uploaded by the user. It contains 18 pages and detailed Phases 0–3. References to later phases do not supply their full specifications. The official SIH problem statement and real APAAR integration contract have not been independently verified.

User constraints: approximately two days; AI-assisted development; Python backend; Vercel frontend; Render backend.

The user supplied `GoogleCloudPlatform/knowledge-catalog`. Its frozen `okf/` copy points to the canonical `GoogleCloudPlatform/open-knowledge-format` repository. **OKF means Open Knowledge Format.** The inspected specification is v0.2. The reviewed sources do not establish a direct code dependency on a specific LLM-Wiki implementation. See the [pinned-source assessment](docs/07-okf-assessment.md). The format is used for these documents; the reference agent is not a core runtime dependency.

These documents are a proposed implementation baseline for review. They do not establish government approval, legal compliance, production security, or live deployment.
