---
description: "Analysis remediation loop: correct every statement carrying the same claim, check the other instances of each defect class, and re-verify on a clean independent pass."
---

# Analysis remediation loop

Apply this whenever an analysis or a review reports
findings. It fires as a mandatory `after_analyze` hook in skills mode and
mirrors the constitution's rerun rule at the analysis stage.

Remediation is complete only when all of the following hold:

1. **Every statement carrying a corrected claim is fixed in the same
   pass.** Each fix is grepped across the whole artifact set (spec, plan,
   research, data-model, contracts, tasks, quickstart) and every other
   statement carrying the same claim is corrected too; a corrected
   statement beside a stale copy of the claim is a new defect, not a
   partial fix.
2. **The other instances of each defect class are checked.** For each
   finding, the sibling instances of the same class (the other knobs,
   other unpinned thresholds, other claims without tasks, other missing
   record fields) are enumerated and checked in the same pass; fixing one
   instance while leaving the others schedules the next finding for a
   later pass.
3. **A clean re-verification closes the loop.** A fresh, independent
   analysis pass, run with the findings and their fixes as context, reports
   every issue resolved and no new findings. A fix applied without the
   clean re-pass leaves the loop open.

If the analysis reported no findings, the loop is closed by that pass.
