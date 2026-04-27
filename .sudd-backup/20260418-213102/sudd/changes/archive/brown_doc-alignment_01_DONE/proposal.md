# Change: brown_doc-alignment_01

## Status
proposed

## Summary
Fix documentation inconsistencies and design gaps identified by the cross-document architecture review (`feedback_browser_use.md`). Addresses H1, M1, M3, M5, L2, L3, L6 — all SUDD-side or architecture-doc fixes that should land before PB implementation begins.

## Motivation
A cross-document review of all 8 architecture files found 16 issues. Of these, 7 are SUDD-side documentation/config fixes that can be resolved now. The remaining 9 are PB-repo implementation issues tracked for Phase 2-4.

Fixing these before Phase 1 ensures the architecture docs are the correct source of truth when PB implementation starts.

## Scope

### Included

**H1: codeintel required vs optional (arch v3.1)**
- Error handling table says "Proceed without code verification, reduced confidence" for missing codeintel
- Phase 4 and gate.md both treat codeintel as required (fail fast)
- Fix: update error handling table to align — codeintel required for UI changes, fail if missing after code-analyzer ran

**M1: CDP port sharing unspecified (arch v3.1)**
- Gate says "save CDP port" but nobody specifies how PB communicates it
- Fix: add `cdp_port` field to PB's output JSON schema in arch v3.1

**M3: experience_factor is circular (sudd.yaml + gate.md)**
- Navigator satisfaction is LLM-fabricated — using it to penalize scores creates LLM-judging-LLM loop
- Fix: make experience_factor informational only (included in report, not in scoring formula or PASS/FAIL decision)

**M5: v2 status still says Approved (PB repo)**
- v2 design doc header says "Status: Approved" but it's fully superseded by v3.1
- Fix: add `**Status**: SUPERSEDED by architecture-proposal-v3.md` header

**L2: Consumer rubric format has no version (arch v3.1)**
- codeintel.json and final-report both have version fields, rubric.md doesn't
- Fix: add `Format version: 1.0` to rubric.md header template in code-analyzer-reviewer.md

**L3: Reference pointer omits spot check (sudd2)**
- reference/persona-browser-agent-architecture.md mentions ux-tester reading reports but omits PB spot check
- Fix: add spot check to the reference pointer

**L6: Model names may be speculative (arch v3.1)**
- "GLM 5-turbo", "Gemini 3 Flash" may not be exact IDs at implementation time
- Fix: add capability requirements (text-only, multimodal, structured output, budget) alongside model names so agents can be swapped

### NOT Included
- H2, H3, H4: PB-repo Phase 4 implementation fixes (tracked in feedback_browser_use.md disposition)
- L4: SPA fallback enhancement (PB Phase 2)
- M2: spot_check_coverage_pct (Phase 6)

## Success Criteria
- [ ] Arch v3.1 error handling table: codeintel = required for UI changes
- [ ] Arch v3.1 PB output schema includes `cdp_port` field
- [ ] sudd.yaml: experience_factor removed from scoring penalties
- [ ] gate.md: experience_factor not in CHECK ALL or penalty calculation
- [ ] v2 design doc: SUPERSEDED header added
- [ ] code-analyzer-reviewer.md rubric template: `Format version: 1.0` in header
- [ ] reference pointer: spot check mentioned
- [ ] Arch v3.1 agent details: capability requirements alongside model names

## Files Modified
- `persona-browser-agent/docs/architecture-proposal-v3.md` — H1 (error table), M1 (cdp_port), L6 (capability reqs)
- `persona-browser-agent/docs/architecture-proposal-v2.md` — M5 (SUPERSEDED header)
- `sudd2/sudd/sudd.yaml` — M3 (remove experience penalties)
- `sudd2/sudd/commands/micro/gate.md` — M3 (experience informational only)
- `sudd2/sudd/agents/code-analyzer-reviewer.md` — L2 (rubric version)
- `sudd2/reference/persona-browser-agent-architecture.md` — L3 (spot check)

## Risk
- Minimal — documentation and config fixes only. No behavioral changes to agents.

## Dependencies
- brown_gate-pb-integration_01 (DONE)
