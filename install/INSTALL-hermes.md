# loop-architect — Hermes (OpenClaw agent) install

Hermes runs on OpenClaw, which uses the same skill format as this bundle (a `SKILL.md` directory). A ready skill only needs to live in Hermes's `skills/` path; the Skill Workshop is for proposing/reviewing new skills and is not required for a drop-in of an already-built one.

## 1. Drop into Hermes's skills dir

From Hermes's workspace root (the dir that contains its `skills/` folder):

```bash
cp -r loop-architect <hermes-workspace>/skills/
```

If you are unsure of the path, find it on Hermes's box:

```bash
openclaw skills path 2>/dev/null || ls -d ~/.openclaw/*/skills ~/.openclaw/workspace/skills 2>/dev/null
```

## 2. Register / verify

```bash
openclaw skills list | grep loop-architect
```

Expect `✓ ready  loop-architect`. If it does not appear, restart Hermes's gateway or run `openclaw skills reindex` (or `openclaw doctor --non-interactive`).

## 3. Optional: route through the Skill Workshop instead

If you prefer Hermes to review-then-apply (rather than a raw drop-in):

```bash
openclaw skills workshop import ./loop-architect      # create a proposal from this dir
openclaw skills workshop list                         # find the new proposal id
openclaw skills workshop apply <proposal-id> --json   # apply (CLI route; the MCP apply can hang)
```

Then verify the same way: `openclaw skills list | grep loop-architect`.

## Readiness checker (standalone)

`SKILL.md` uses `${CLAUDE_SKILL_DIR:-.}` which falls back to `.` when unset, so run from the skill dir or pass absolute paths:

```bash
cd <hermes-workspace>/skills/loop-architect
python3 scripts/loop_readiness_check.py --strict /path/to/loop-contract.md \
  --verify-manifest references/source-evidence-manifest.md \
  --state-template templates/state-file.md
```

Pure Python 3, no dependencies.

## Contents

Same skill core as the other bundles: `SKILL.md`, `references/`, `templates/`, `scripts/`.
