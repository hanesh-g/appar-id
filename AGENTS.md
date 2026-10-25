# Project instructions

Read README.md and docs/index.md first. Use docs/05-progress-checklist.md for current evidence, not assumptions from generated scaffolding.

## Git identity

The user requires commits authored and committed as `hanesh-g <haneshgourishetti@gmail.com>`. Set this **repository-locally** and verify it before committing. Never reuse the environment's inherited identity. Do not add other author trailers unless requested. Pushes must preserve unrelated remote work; never use an unconditional force push.

## Windows workflow

The user develops on native Windows with PowerShell. Do not require Ubuntu or WSL. Native PostgreSQL is supported; Docker is optional. Keep Python scripts and paths cross-platform. Use `uv run` rather than shell-specific virtualenv activation. Instructions may describe Linux hosting without making Linux a local prerequisite.

## Backend standards

Keep HTTP parsing, domain rules, scoped database access, encryption, and configuration in separate modules. Use typed request/response models, Alembic migrations, database constraints, explicit transactions, exact frontend origins, and secret-safe configuration. Never log credentials, raw student rows, or identifying fields. Validate with PostgreSQL integration tests, Ruff checks/formatting, and the actual application flow.

Use the existing checkout. Do not create worktrees unless requested. Keep optional consent/LLM features out of the core until their permission and negative-test gates pass. Registry results must remain visibly simulated. Only check off executed, evidenced work.
