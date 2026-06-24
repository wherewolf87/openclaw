# Review Council / Gangster Gate

Use this protocol when a loop is non-trivial, medium-risk, high-risk, write-capable, user-facing, money-adjacent, production-adjacent, or long-running.

## Roles

- Planner: outcome, primitive choice, state, permissions, and one-action-per-wake design.
- Builder: runbook, harness surfaces, launch prompt, implementation feasibility.
- Skeptic: safety, prompt injection, cost, scope drift, external action, rollback, and approval gates.
- Verifier: readiness score, evidence, forward tests, proof path, and independent checker.

## Closed Verdicts

- APPROVED: no blocking findings.
- CHANGES_NEEDED: blocker exists; include the exact required fix.
- BLOCKED: cannot continue safely without user input or external state.

## Required Receipt Shape

Every final contract must record the roles exactly enough for the readiness checker to parse them:

```text
Required roles and final verdicts:
- Planner: APPROVED
- Builder: APPROVED
- Skeptic: APPROVED
- Verifier: APPROVED

Plan review receipt:
- Planner/APPROVED/no blockers/no fix//root/.openclaw/workspace/reports/example-plan-proof.md
- Builder/APPROVED/no blockers/no fix//root/.openclaw/workspace/reports/example-plan-proof.md
- Skeptic/APPROVED/no blockers/no fix//root/.openclaw/workspace/reports/example-plan-proof.md
- Verifier/APPROVED/no blockers/no fix//root/.openclaw/workspace/reports/example-plan-proof.md

Final review receipt:
- Planner/APPROVED/no blockers/no fix//root/.openclaw/workspace/reports/example-final-proof.md
- Builder/APPROVED/no blockers/no fix//root/.openclaw/workspace/reports/example-final-proof.md
- Skeptic/APPROVED/no blockers/no fix//root/.openclaw/workspace/reports/example-final-proof.md
- Verifier/APPROVED/no blockers/no fix//root/.openclaw/workspace/reports/example-final-proof.md

Consensus status: UNANIMOUS APPROVED
Review timestamp: 2026-06-24T00:00:00Z
Freshness TTL: 30 days

Reviewer identities:
- planner_reviewer_id: OpenClaw
- builder_reviewer_id: Cody
- skeptic_reviewer_id: Sandy
- verifier_reviewer_id: Gemmy
```

Simple `Role: APPROVED` lines are required for verdict identity, but they are not sufficient for strict-mode approval by themselves. Plan and final receipts must also include structured `role/verdict/finding/fix/proof` rows. Any missing role, missing structured receipt row, conditional approval, `CHANGES_NEEDED`, `BLOCKED`, `REJECTED`, majority approval, partial approval, stale approval, expired freshness TTL, pending approval, or ambiguous prose is not approval.

## Consensus Loop

1. Run plan review before the contract is finalized.
2. Revise any `CHANGES_NEEDED` findings.
3. Run final review on the exact contract body and support files.
4. Final approval requires all required roles to return exactly `APPROVED`.
5. Final consensus must say exactly `UNANIMOUS APPROVED`.
6. Final receipts must include a UTC `Review timestamp` and `Freshness TTL`; expired receipts are stale and not approval.
7. Conditional approvals such as `APPROVED if...` or `UNANIMOUS APPROVED if...` are not approval.
8. If any role returns `CHANGES_NEEDED`, revise and rerun final review.
9. If any role returns `BLOCKED`, stop and report what authorization, access, or external state is needed.
10. Save a review receipt with reviewer, verdict, finding, fix, proof path, timestamp, and TTL.

Proof path validation confirms path syntax, existence, and approved proof roots. It does not prove semantic relevance by itself; each reviewer must ensure the proof artifact actually supports the finding and fix it is cited for. Do not cite unrelated reports as proof.

Do not claim real-world public figures approved the build unless they actually did. This is an internal review council protocol.
