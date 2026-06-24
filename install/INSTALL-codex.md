# loop-architect — Codex (OpenAI Codex CLI) install

Codex does not auto-discover a `skills/` folder the way Claude Code does. You wire it in by (1) placing the skill on disk and (2) pointing Codex at it from `AGENTS.md`. The skill body and the readiness checker are runtime-agnostic, so nothing inside needs to change.

## 1. Place the skill

```bash
mkdir -p ~/.codex/skills
cp -r loop-architect ~/.codex/skills/
```

(Any stable path works; `~/.codex/skills/` is just a clean default.)

## 2. Wire it into AGENTS.md

Append the contents of `AGENTS.snippet.md` (in this bundle) to either:
- `~/.codex/AGENTS.md` (global, every Codex session), or
- `<your-project>/AGENTS.md` (that project only).

That snippet tells Codex when to load the skill and how to run its checker.

## 3. Verify

In a Codex session, ask: "use loop-architect to turn 'monitor the deploy and alert me' into a safe loop contract." Codex should read `~/.codex/skills/loop-architect/SKILL.md` and produce a contract ending with Readiness + Review-consensus sections.

## Readiness checker (standalone)

`SKILL.md` references `${CLAUDE_SKILL_DIR:-.}`; that env var is unset under Codex, so it falls back to `.`. Run the checker from inside the skill dir, or pass absolute paths:

```bash
cd ~/.codex/skills/loop-architect
python3 scripts/loop_readiness_check.py --strict /path/to/loop-contract.md \
  --verify-manifest references/source-evidence-manifest.md \
  --state-template templates/state-file.md
```

Pure Python 3, no dependencies.

## Contents

Same skill core as the other bundles (`SKILL.md`, `references/`, `templates/`, `scripts/`) plus `AGENTS.snippet.md` for the wire-up.
