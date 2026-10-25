---
type: Reference
title: OKF assessment
description: Explain the verified canonical project and its limited role in this prototype.
tags: [okf, knowledge, sources, architecture]
status: draft
generated: {by: codex/build-pack-v1, at: "2026-10-25T17:11:45Z"}
sources:
  - id: catalog
    resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/a8291a1a656669b8766fd4ff0f985505fb955e94/README.md
  - id: migration
    resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/a8291a1a656669b8766fd4ff0f985505fb955e94/okf/README.md
  - id: spec
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md
  - id: agent
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/README.md
  - id: license
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/LICENSE.md
---

# 07 — OKF assessment and project use

## 1. What the user's link contains

The supplied repository is [GoogleCloudPlatform/knowledge-catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog). Its root describes Knowledge Catalog tools, agents, and samples. It also states that the repository and its contents are not an official Google product.[^catalog]

Its `okf/README.md` says that **OKF now lives in its own repository**, and that the old copy is a frozen, unmaintained snapshot. It directs users to [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format).[^migration]

The expanded name is **Open Knowledge Format**. The inspected canonical specification is **v0.2**.[^spec]

The exact source snapshots inspected were:

| Repository | Commit |
|---|---|
| `GoogleCloudPlatform/knowledge-catalog` | `a8291a1a656669b8766fd4ff0f985505fb955e94` |
| `GoogleCloudPlatform/open-knowledge-format` | `ad30107c31c06aec8a7d5636e0d1058118604e6f` |

Repository contents can change. These findings apply to those snapshots. No upstream source files were copied into the application checkout.

## 2. What OKF does

An OKF bundle is a directory of Markdown files. Each concept file starts with YAML metadata. The only always-required concept field is a non-empty `type`.

Useful optional fields include a title, description, tags, sources, generation metadata, document review events, and lifecycle status. Standard links connect related concepts. An optional index helps an assistant load only the relevant files.[^spec]

Example:

```yaml
---
type: Business Rule
title: Missing APAAR identifiers
description: Keep well-formed admissions countable when their identity is unresolved.
tags: [identity, intake, demo]
status: draft
---
```

The body then states the rule, reason, examples, and related documents. The format does not require a model provider, agent framework, search service, or database.[^spec]

This is compatible with the general idea of an LLM-maintained wiki. However, the inspected README, specification, and package metadata do not establish that this project is built on a particular LLM-Wiki codebase. Do not repeat that lineage as a verified fact without an explicit source.

## 3. Format, reference agent, and Google Cloud are different things

| Item | Purpose | Required for our core? |
|---|---|---|
| OKF specification | Defines portable knowledge documents. | Adopt its lightweight structure for `docs/`. |
| Reference agent | Demonstrates generating/enriching bundles. | No. |
| Graph visualizer | Demonstrates browsing links and concepts. | No. |
| Google Cloud Knowledge Catalog service | Managed catalog capabilities, distinct from a directory format. | No. |
| Gemini/model API | Used by the reference agent's enrichment flow. | No. |
| BigQuery | Source used by the documented reference-agent workflow. | No. |

The reference package declares Python `>=3.11` and dependencies including Google ADK, BigQuery, PyYAML, Pydantic, and markdownify. Its README shows BigQuery credentials/billing configuration plus Gemini or Vertex AI credentials for the documented enrichment flow.[^agent]

Those requirements belong to that producer. They do not justify adding BigQuery, Google ADK, or Google Cloud authentication to our FastAPI backend. In particular, the documented BigQuery producer is not a drop-in PostgreSQL student-record assistant.

## 4. How we use OKF now

The `docs/` directory is the bundle:

```text
docs/
  index.md                         # bundle entry; okf_version: "0.2"
  log.md                           # documentation changes
  01-problem-and-scope.md           # Product Brief
  02-technical-design.md            # Technical Design
  03-feature-specification.md       # Feature Specification
  04-implementation-phases.md       # Implementation Plan
  05-progress-checklist.md          # Delivery Checklist
  06-ai-development-workflow.md     # Playbook
  07-okf-assessment.md              # Reference
```

Each concept has parseable frontmatter and a descriptive type. `status: draft` means the proposed content has not received human approval. Generation metadata states that AI produced it. No human `verified` marker is invented.

An assistant can read the index, open the current feature and contract, implement one task, and update the checklist with evidence. This provides useful context management without operating another service.

The documents are not automatically loaded by every AI tool. The operator or task prompt must point the coding assistant to the index and relevant files. No synchronization or automatic ingestion is claimed.

## 5. How it can help the product later

An approved rules bundle can describe:

- The meaning and correction action for each issue code.
- The source and assumptions behind an intake metric.
- API and table semantics.
- Institution onboarding procedures.
- Verification and consent rules approved for the intended use.

F14 can retrieve these approved rules and return explanations with sources. An LLM is optional. Runtime records and permission decisions remain in PostgreSQL and deterministic backend code.

OKF v0.2 also describes **Attested Computation** concepts: a declared computation, execution receipt, and deterministic check of what ran. This may later help explain exactly how a dashboard count was computed.[^spec] It does not provide our API with an automatic audit ledger, trusted SQL executor, or regulatory certification. Our core uses tested server-side metric functions; no attestation subsystem is claimed.

## 6. Constraints and risks

- A Markdown file can be stale or wrong. Track provenance and review; metadata is not proof.
- An assistant must not treat bundle text as authority to reveal secrets or execute unrelated actions.
- A bundle is not access control. Keep personal records out of it and enforce scope in the application.
- A consumer must actually honour status, freshness, and document review fields; adding them alone has no runtime effect.
- Do not auto-publish machine-generated policy as authoritative.
- If upstream code is later reused, preserve applicable license/notice obligations. The inspected repositories use Apache-2.0 licensing.[^license]

## 7. Recommendation

**Adopt the format for coding context now. Defer the reference agent and product assistant.** This gives the team structured project memory while preserving the small Vercel/Render/PostgreSQL architecture.

Source inspection and local document-structure checks are part of this documentation task. The upstream producer, visualizer, LLM calls, BigQuery access, and their operational behaviour have not been installed or run.

## Pinned references

[^catalog]: [Knowledge Catalog README at inspected commit](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/a8291a1a656669b8766fd4ff0f985505fb955e94/README.md).
[^migration]: [Frozen OKF copy and migration notice](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/a8291a1a656669b8766fd4ff0f985505fb955e94/okf/README.md).
[^spec]: [Canonical OKF v0.2 specification at inspected commit](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md).
[^agent]: [Canonical reference-agent README](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/README.md) and [package metadata](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/pyproject.toml).
[^license]: [Canonical license](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/LICENSE.md) and [Knowledge Catalog license](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/a8291a1a656669b8766fd4ff0f985505fb955e94/LICENSE.md).
