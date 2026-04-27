# Micro-Persona: T3 — Create code-analyzer-reviewer agent

## Consumer
**Who**: persona-browser-agent
**Role**: Receives the unified codeintel.json, manifest.json, and rubric.md to know what pages to visit, what to verify on each page, and how to score results

## Objective
Receive cross-validated artifacts that accurately represent the full-stack codebase. The persona-browser-agent has no access to source code — it relies entirely on these artifacts to navigate the application and judge whether it works. Any mismatch between artifacts and reality causes the browser agent to test the wrong things or miss critical functionality.

## Success Criteria
- [ ] Cross-validation catches FE-to-BE mismatches: endpoints referenced in frontend but missing in backend, request/response schema disagreements, auth requirements that differ between layers
- [ ] Data flows are traced end-to-end from UI action through API call to database operation, with discrepancies flagged
- [ ] Verification tasks are auto-generated from the cross-validated data — not hand-written — so coverage is systematic rather than ad hoc
- [ ] rubric.md categorizes every verification item as Must Pass, Should Pass, or Deal-Breaker with clear rationale for the priority level
- [ ] rubric.md items are organized per page/route so the browser agent can work through them in navigation order
- [ ] manifest.json lists every visitable page with URL, prerequisite state (logged in, specific data seeded), and expected elements
- [ ] codeintel.json merges FE and BE data into a single unified structure with cross-references intact
- [ ] Low-confidence items from FE/BE analysis are flagged for manual review rather than silently promoted to high-confidence
