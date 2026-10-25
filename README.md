# APAAR Student Data Platform — build pack

Planning documents for an AI-assisted SIH 2026 prototype. The backend will use Python. The frontend will run on Vercel. The backend will run on Render with managed PostgreSQL.

**Current state:** documentation only. No application, dependency installation, deployment, or passing application tests are claimed. The two-day constraint sets the scope; it does not prove delivery time.

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
