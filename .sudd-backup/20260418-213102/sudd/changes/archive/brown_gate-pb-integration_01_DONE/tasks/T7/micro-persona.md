# Micro-Persona: T7 — Rewrite gate.md Steps 2-3b

## Consumer
**Who**: Solo developer (reads gate output in the morning)
**Role**: Reads the gate verdict, score breakdown, and action items to decide whether to ship, fix, or escalate — without re-running any tests or reading logs

## Objective
Get a reliable, unified gate verdict with clear action items. The developer needs to open one file, see PASS or FAIL, understand why in under 60 seconds, and know exactly what to fix if it failed. No ambiguity, no detective work, no "see log for details."

## Success Criteria
- [ ] Code-analyzer pipeline runs as part of the gate (codeintel.json, manifest.json, rubric.md generated before browser testing begins)
- [ ] Persona-browser is called exactly once per persona (not once per page) to minimize token cost and avoid redundant navigation
- [ ] Unified scoring formula is documented in the gate itself — weights for Must Pass, Should Pass, Deal-Breaker, and spot-check agreement are visible, not hidden in agent prompts
- [ ] Action items are categorized: Deal-Breakers (must fix before re-gate), Must-Fix (fix before ship), Should-Fix (can defer), and Info (no action needed)
- [ ] Spot check results from ux-tester are integrated into the final score — disagreements between ux-tester and persona-validator are highlighted with the discrepancy explained
- [ ] Output includes the final numeric score, the threshold for PASS (98/100), and the gap if FAIL
- [ ] Every action item includes: what failed, on which page, evidence source (persona-validator or ux-tester), and suggested fix
- [ ] Gate output is self-contained — no external file references needed to understand the verdict
