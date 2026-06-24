# loop-architect — Claude Code install

Native Claude Code skill. `SKILL.md` already uses `${CLAUDE_SKILL_DIR:-.}`, so it is Claude-Code-aware out of the box.

## Install (personal, all projects)

```bash
mkdir -p ~/.claude/skills
cp -r loop-architect ~/.claude/skills/
```

## Install (single project only)

```bash
mkdir -p .claude/skills
cp -r loop-architect .claude/skills/
```

## Verify

- Start (or restart) Claude Code in that scope.
- The skill auto-registers from its `SKILL.md` YAML frontmatter (`name: loop-architect`).
- Ask Claude something like "turn 'watch my PRs and report' into a safe loop" — it should invoke loop-architect.

## What it does

Turns a plain request ("watch my PRs", "run until fixed", "automate this recurring task") into a safe, verifiable loop contract: state, sources, permissions, verifier, harness, budget, approval gates, rollback, logs, and review-council consensus.

## Readiness checker (optional, standalone)

```bash
python3 ~/.claude/skills/loop-architect/scripts/loop_readiness_check.py --strict path/to/loop-contract.md \
  --verify-manifest ~/.claude/skills/loop-architect/references/source-evidence-manifest.md \
  --state-template ~/.claude/skills/loop-architect/templates/state-file.md
```

Pure Python 3, no dependencies. Exit/JSON reports `status: pass|warn|fail` with a score.

## Contents

- `SKILL.md` — the guide (operating rules + 7-step workflow + output format)
- `references/` — research notes, source-evidence manifest, review-council protocol, eval cases
- `templates/` — loop-contract, state-file, launch-prompts scaffolds
- `scripts/loop_readiness_check.py` — contract readiness checker / manifest hash verifier / state-template validator
