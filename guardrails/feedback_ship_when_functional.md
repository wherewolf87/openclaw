---
name: feedback_ship_when_functional
description: "Anti-rabbit-hole ship gate — completion is functional+clean+one review, NOT an ever-receding adversarial bar"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 30b4096c-13bc-4147-adfb-1b26b2e1fb9a
---

When building or hardening a skill, tool, script, or guard, the completion bar is: **functional + scan-clean + passes its own test suite + ONE review-council pass.** Ship at that point.

Do NOT treat an ever-receding adversarial-review bar as the completion criterion. If each review round only surfaces a NEW edge/obfuscation variant ("could be bypassed by another separator / leetspeak / unicode trick"), that is a moving goalpost — declare done and ship. Defense-in-depth perfection on a HELPER/guard script is never a ship-blocker. Cap re-hardening at ONE round, then ship.

**Why:** On 2026-06-24, building `loop-architect`, I burned 40+ iterations (v12→v48) re-hardening the readiness checker's risky-action regex. Each gangster review found one more obfuscation bypass, flipping "unanimous 3/3" back to "stale, re-review." I treated that self-created moving goalpost as the finish line, went silent for 982s then 2608s, and cost the Operator 4 nudges + a "i never want this painful experience again." See [[2026-06-24-loop-architect-applied]].

**How to apply:** When a review returns only "a new variant could bypass"-class findings (no real correctness/safety/structural blocker), stop, ship, and say so. Never re-open a shipped artifact to chase obfuscation completeness. Related: [[feedback_no_midtask_stops]], [[feedback_no_hang_commands]].
