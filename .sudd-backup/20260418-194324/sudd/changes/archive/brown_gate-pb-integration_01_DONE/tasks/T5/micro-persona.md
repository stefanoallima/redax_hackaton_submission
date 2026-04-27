# Micro-Persona: T5 — Rewrite persona-validator agent

## Consumer
**Who**: gate.md (Steps 2-3b gate logic)
**Role**: Reads persona-validator output to compute the per-persona score and the overall gate verdict (PASS/FAIL/STUCK)

## Objective
Get a first-person persona judgment based purely on persona-browser report evidence. The gate needs a structured, evidence-backed verdict from the persona's perspective — not a technical audit. Every claim must trace back to a specific finding in the browser-reports JSON so the gate can verify the judgment is grounded, not hallucinated.

## Success Criteria
- [ ] Zero browser/Playwright/CDP references in the output — the persona-validator speaks as the persona, not as a test engineer
- [ ] Every positive or negative judgment cites specific evidence from the browser-reports JSON (report ID, page, finding)
- [ ] Objective walkthrough is complete — every page listed in manifest.json has a corresponding judgment, no pages silently skipped
- [ ] Output includes a numeric score (0-100) with breakdown by rubric category so the gate can apply its scoring formula
- [ ] Deal-Breaker items that failed are explicitly called out as blockers, separate from Should Pass / Must Pass failures
- [ ] The persona's voice matches their persona definition (tech-savvy user sounds different from first-time visitor)
- [ ] Output format is structured JSON or structured markdown that gate.md can parse programmatically, not free-form prose
