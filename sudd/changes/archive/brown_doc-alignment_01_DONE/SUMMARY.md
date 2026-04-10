# Archive: brown_doc-alignment_01

## Outcome: DONE

## Summary
Fixed 7 documentation/config inconsistencies from the cross-document architecture review. All SUDD-side fixes applied; PB-side fixes tracked in pb-fixes-from-cross-review.md.

## Fixes Applied
- **H1**: codeintel required for UI changes in arch v3.1 error table (was "proceed without")
- **M1**: Added `cdp_port` field to PB output schema (navigator + final report)
- **M3**: Made experience_factor informational only in sudd.yaml + gate.md + arch v3.1 (was penalty)
- **M5**: Added SUPERSEDED header to v2 design doc
- **L2**: Added `Format version: 1.0` to rubric template in code-analyzer-reviewer.md
- **L3**: Added PB spot check mention to SUDD reference pointer
- **L6**: Added model capability requirements table to arch v3.1

## Files Modified
- `persona-browser-agent/docs/architecture-proposal-v3.md` (H1, M1, M3, L6)
- `persona-browser-agent/docs/superpowers/specs/2026-03-29-persona-browser-agent-v2-design.md` (M5)
- `sudd2/sudd/sudd.yaml` (M3)
- `sudd2/sudd/commands/micro/gate.md` (M3)
- `sudd2/sudd/agents/code-analyzer-reviewer.md` (L2)
- `sudd2/reference/persona-browser-agent-architecture.md` (L3)

## Completed: 2026-03-31
