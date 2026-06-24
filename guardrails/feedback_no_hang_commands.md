---
name: feedback_no_hang_commands
description: Never run unbounded/disk-wide/heavy commands in foreground — they hang the turn and trip the silence watchdog
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 30b4096c-13bc-4147-adfb-1b26b2e1fb9a
---

Never run a command that can hang the turn: no disk-wide scans (`find /`), no unbounded heavy suites, no long external-model/CLI runs in the blocking foreground without a cap. Every potentially-slow command gets an explicit `timeout`. Anything that may exceed ~60s runs in the **background** and is **actively polled within the same turn** (do not background-and-end-turn).

This refines [[feedback_no_midtask_stops]]: short commands stay foreground so output isn't lost; only genuinely-long ops go to background, and you keep polling them until done — you never leave the turn with work in flight.

**Why:** On 2026-06-24 a `find / -name quick_validate.py` scanned the whole disk and a 265-check verification suite ran >2min, each hanging the turn mid-task. Combined with rabbit-holing, this produced multi-minute silences that tripped the continuity watchdog and made the Operator think I was broken. See [[2026-06-24-loop-architect-applied]].

**How to apply:** Target exact paths instead of `find /`. Prefer the fast discriminating check (good-input passes / bad-input fails) over re-running an exhaustive suite. Bound every slow command; background + poll the rest. Related: [[feedback_ship_when_functional]].
