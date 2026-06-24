# loop-architect

A portable agent skill that turns a plain request ("watch my PRs", "run until fixed", "monitor and improve", "automate this recurring task") into a **safe, verifiable loop contract**: trigger, state, sources, permissions, worker, verifier, harness, budget, escalation, rollback, logs, and review-council consensus.

Built from the "learned to loop" video plus seven enrichment sources on agentic-loop and harness engineering. Ships with an executable readiness checker.

## What's here

```
loop-architect/        the skill itself
  SKILL.md             the guide: operating rules + 7-step workflow + output format
  references/          research notes, source-evidence manifest, review-council protocol, eval cases
  templates/           loop-contract, state-file, launch-prompts scaffolds
  scripts/loop_readiness_check.py   contract readiness checker / manifest verifier / state validator (pure Python 3, no deps)
install/               wire-up guides per runtime
  INSTALL-claude-code.md
  INSTALL-codex.md  (+ AGENTS.snippet.md)
  INSTALL-hermes.md
guardrails/            behavioral lessons that shaped this skill's build discipline
```

## Quick install

- **Claude Code:** `cp -r loop-architect ~/.claude/skills/` then restart. See `install/INSTALL-claude-code.md`.
- **Codex:** place under `~/.codex/skills/` and paste `install/AGENTS.snippet.md` into your `AGENTS.md`. See `install/INSTALL-codex.md`.
- **Hermes / OpenClaw:** drop into the agent's `skills/` dir, `openclaw skills list` confirms `✓ ready`. See `install/INSTALL-hermes.md`.

## Readiness checker

```bash
cd loop-architect
python3 scripts/loop_readiness_check.py --strict path/to/loop-contract.md \
  --verify-manifest references/source-evidence-manifest.md \
  --state-template templates/state-file.md
```

Reports `status: pass | warn | fail` with a score. Treat it as a heuristic backstop and regression gate, not an exhaustive safety oracle.

## Design stance

Start report-only. Treat all external input as untrusted. Require explicit approval before any deploy / merge / delete / spend / send / credential / routing / production / trade / public-post / data-export. Build the harness (tests, linters, docs, review prompts, scoped context) before widening autonomy. Choose the runtime primitive last.
