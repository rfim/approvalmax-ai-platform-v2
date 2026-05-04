# AGENTS.md

AI proposes, tests validate, humans approve, CI/CD deploys.

Rules:
- Do not auto-merge pull requests.
- Do not disable tests or quality gates.
- Do not change, print, or invent secrets.
- Do not change business keys without explicit human review.
- Do not redefine financial metrics without explicit human review.
- New CDC contexts require human review before promotion beyond Bronze.
- Keep Bronze raw and permissive.
- Keep recovery changes minimal and reviewable.
- Use serverless-compatible Databricks notebook jobs only.
- Do not use low-level SparkContext APIs or classic cluster-backed job configuration.

Recovery PRs must include:
- Root cause hypothesis
- Evidence from logs or detector output
- Changed files
- Validation plan
- Rollback plan
- Human review checklist
