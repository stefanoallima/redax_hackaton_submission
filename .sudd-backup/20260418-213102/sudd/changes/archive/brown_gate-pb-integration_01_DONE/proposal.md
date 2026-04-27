# Change: brown_gate-pb-integration_01

## Status
proposed

## Summary
Align SUDD's gate workflow and UX agents (persona-validator, ux-tester) with the persona-browser-agent v3.1 architecture. Replace redundant browser sessions with call-once-share-results pattern, add code-analyzer pipeline with adversarial rubric review, add PB spot check for hallucination detection, and implement unified scoring formula.

## Motivation
The v3.1 architecture for persona-browser-agent was designed and validated (PoCs confirmed — see `persona-browser-agent/docs/architecture-proposal-v3.md` and `phase-0-feasibility-and-risk-mitigations.md`). But the SUDD-side agents still operate on the pre-v3.1 model:

**Problem 1: Redundant browser sessions** — Both persona-validator AND ux-tester independently call `persona_browser.cli`, launching 2-3 separate browser sessions per persona. Same app, same persona, same navigation, different output files. Wastes 1-3 minutes per persona and doubles cost.

**Problem 2: persona-validator still launches browsers** — The agent has a full "Browser-Based Validation" section where it starts dev servers, navigates via Playwright, takes screenshots, and calls browser-use. v3.1 says: persona-validator reads the saved PB report. No browser.

**Problem 3: ux-tester duplicates PB's work** — ux-tester has its own intuitiveness framework (discoverability, cognitive load, flow, error recovery) which overlaps with PB's feature-based rubric criteria (FORMS, NAVIGATION, CTA). Redundant assessment.

**Problem 4: No code-analyzer pipeline** — Gate goes straight from macro-wiring check to persona validation. No code intelligence extraction, no manifest generation, no adversarial rubric review.

**Problem 5: Scoring formula is scattered** — persona-validator has its own rubric levels, ux-tester has its own formula (40/30/30 split), gate just checks "all EXEMPLARY". v3.1 defines one unified scoring formula owned by SUDD.

**Problem 6: No PB reliability verification** — PB reports per-criterion PASS/FAIL but nothing independently verifies those findings. False PASSes are silent and the most dangerous failure mode. A solo developer running overnight needs confidence that PB isn't hallucinating.

**Problem 7: Missing verification in gate** — Current gate doesn't check API contract compliance, auth flow integrity, data persistence, or cross-page consistency. v3.1 adds network verification, verification tasks, and manifest coverage as gate requirements.

## Scope

### Included

**gate.md rewrite:**
- Step 2a: Code-analyzer pipeline (3 agents + adversarial rubric review)
  - code-analyzer-fe (Haiku) + code-analyzer-be (Haiku) run in parallel
  - code-analyzer-reviewer (Sonnet) merges, cross-validates, generates draft rubric
  - rubric-adversary (Haiku) critiques draft (2 iterations) → hardened rubric
  - Outputs: codeintel.json, manifest.json, rubric.md
- Step 2b: Browser testing — gate starts dev server ONCE, calls PB once per persona, saves report
  - Gate owns dev server lifecycle (start once, keep alive through all steps, kill after 2e)
  - PB's Chrome instance stays alive for ux-tester's Playwright-over-CDP connection
- Step 2c: persona-validator reads PB report (no browser)
- Step 2d: ux-tester reads PB report + runs PB spot check + technical checks via Playwright-over-CDP
- Step 2e: Unified scoring formula (pb_score, consumer_score, verification_score, network_penalty, spot_check)
- Step 3b: Critical assessment (kept as SUDD-level check on top of PB report)

**persona-validator.md rewrite:**
- Remove ALL browser launching (Playwright, browser-use subprocess calls)
- Read `browser-reports/{name}.json` for evidence: consumer_criteria, experience, deal_breakers, network_verification, verification_tasks, manifest_coverage
- Keep: first-person narrative, EXEMPLARY/STRONG scoring, critical assessment, handoff contract check, deal-breaker check, objective walkthrough
- All judgment from report evidence, not live browser interaction

**ux-tester.md rewrite:**
- Remove browser-use subprocess calls
- Remove own intuitiveness framework (PB's feature-based criteria replace it)
- Add PB spot check: randomly verify 2-3 PASS + 1 FAIL criteria via Playwright-over-CDP (same Chrome instance PB used)
- Keep technical checks via Playwright-over-CDP: console errors, accessibility audit, design system CSS compliance, Score Reconciler-flagged items
- New output section: spot_check_results with PB-vs-Playwright comparison

**New agent files:**
- `sudd/agents/code-analyzer-fe.md` — Haiku, reads frontend code, outputs fe_codeintel.json
- `sudd/agents/code-analyzer-be.md` — Haiku, reads backend code, outputs be_codeintel.json
- `sudd/agents/code-analyzer-reviewer.md` — Sonnet, merges FE+BE, cross-validates, generates manifest + draft rubric + codeintel
- `sudd/agents/rubric-adversary.md` — Haiku, adversarial rubric review (2 iterations)

**sudd.yaml updates:**
- `browser_use.navigator.max_steps`, `timeout_seconds`, `app_domains`
- `browser_use.rubric_threshold.pb`, `.consumer`, `.verification`
- `browser_use.scoring.*` (unified formula weights and penalties)
- `safety.max_cost_per_change`, `safety.identical_failure_stuck_after` (lightweight circuit breakers)

### NOT Included
- persona-browser-agent code changes (separate repo, separate phases 1-4)
- Full circuit breaker implementation (partial retry, cost tracking — deferred to later change)
- Golden test app (lives in PB repo, Phase 3-4)
- Code-analyzer implementation/testing against real codebases (this change defines the agent prompts; real-world validation is Phase 5 work)

## Design Decisions

### D1: persona-validator has NO browser access
All browser interaction is PB's job. persona-validator reads the saved report and provides first-person narrative judgment from evidence. If the report lacks evidence for a specific objective, the persona-validator marks it UNTESTABLE — it does not fall back to launching a browser.

### D2: ux-tester uses Playwright-over-CDP on PB's Chrome instance
ux-tester connects Playwright to the same Chrome instance that PB navigated. Same page state, same cookies, same session. This ensures spot checks and technical checks see exactly what PB saw. No separate browser session.

### D3: Gate owns dev server lifecycle
Gate starts the dev server once at Step 2b, keeps it alive through PB + ux-tester, kills it after Step 2e. One start/stop cycle. If server crashes mid-pipeline, gate detects and handles restart.

### D4: Critical assessment stays as SUDD-level check
PB's triangulation (text + visual + network) provides evidence. The critical assessment (Step 3b) adds a SUDD-level "is this genuinely EXEMPLARY?" check. This is the human-judgment layer on top of PB's automated evidence.

### D5: PB spot check for hallucination detection
After PB produces its report, ux-tester picks 2-3 criteria from PB's PASS results and 1 from FAIL results. It independently verifies them via Playwright-over-CDP. Outcome matrix:

| Spot Check Result | Action |
|---|---|
| All match PB | High confidence. Proceed normally. |
| 1 mismatch on non-critical | -15 penalty + flag for morning review. Proceed. |
| 1+ mismatch on critical/deal-breaker | Gate FAIL. Reason: "PB reliability concern." |
| FAIL was actually PASS | Flag "pb_false_fail_detected". Remove false penalty. |
| 2+ mismatches | Gate FAIL. Mark "PB UNRELIABLE". Full Playwright fallback on retry, score capped at 90. |

Only Playwright-verifiable criteria are eligible for spot check (element counts, visibility, text content, form submission — not color matching or spatial assessment).

### D6: Unified scoring formula in gate
SUDD owns one formula applied to PB's per-criterion evidence:

```
pb_score = pb_pass_rate * 100 (deal-breaker → instant 0)
consumer_score = consumer_pass_rate * 100 (Must Pass 100%, Should Pass 50%)
verification_score = verification_pass_rate * 100 (threshold: 100%)
network_penalty = -15 per API error, instant 0 on 500 or auth handover fail
manifest_penalty = -10 per missing page
experience_factor = -5 if satisfaction < 5, -10 if "would not recommend"
spot_check_penalty = -15 per mismatch (or gate FAIL on critical)

ALL must pass:
  pb_score >= 98
  consumer_score >= 98
  verification_score == 100
  No deal-breakers at HIGH confidence
  No API 500 during normal flow
  Auth flow verified
  Manifest coverage = 100%
  persona-validator level == EXEMPLARY
  ux-tester spot check passed
```

## Success Criteria
- [ ] gate.md has Step 2a (code-analyzer pipeline + adversarial rubric review)
- [ ] gate.md has Step 2b with dev server lifecycle management and single PB call per persona
- [ ] gate.md has Step 2c/2d/2e with report-reading pattern
- [ ] gate.md has unified scoring formula with all penalty types
- [ ] persona-validator.md has ZERO browser/Playwright/browser-use references
- [ ] persona-validator.md reads from `browser-reports/{name}.json`
- [ ] ux-tester.md has PB spot check (2-3 PASS + 1 FAIL random verification)
- [ ] ux-tester.md uses Playwright-over-CDP (same Chrome instance as PB)
- [ ] ux-tester.md has NO intuitiveness framework (replaced by PB feature criteria)
- [ ] 4 new agent files exist: code-analyzer-fe, code-analyzer-be, code-analyzer-reviewer, rubric-adversary
- [ ] sudd.yaml has browser_use.scoring section with unified formula
- [ ] sudd.yaml has safety section with max_cost_per_change
- [ ] Critical assessment (Step 3b) preserved and references PB report evidence

## Dependencies
- persona-browser-agent v3.1 architecture (docs complete, PoCs confirmed)
- brown_validation-rubrics_01 (persona objectives, anchored rubrics — already DONE)

## Files Modified
- `sudd/commands/micro/gate.md` — major rewrite
- `sudd/agents/persona-validator.md` — major rewrite
- `sudd/agents/ux-tester.md` — major rewrite
- `sudd/sudd.yaml` — add scoring + safety sections

## Files Created
- `sudd/agents/code-analyzer-fe.md`
- `sudd/agents/code-analyzer-be.md`
- `sudd/agents/code-analyzer-reviewer.md`
- `sudd/agents/rubric-adversary.md`

## Risk
- **Code-analyzer agents are untested against real codebases** — this change defines the prompts but real-world validation happens when PB Phase 5 is implemented. Mitigation: prompts are conservative, confidence gating prevents bad codeintel from causing false failures.
- **PB spot check adds gate time** — ~10-15s per gate for 3-4 Playwright assertions. Acceptable for the confidence it provides.
- **Playwright-over-CDP connection may have edge cases** — browser-use's Chrome instance may not always be connectable. Mitigation: if Playwright-over-CDP fails, ux-tester falls back to launching its own Playwright instance (degraded but functional).

## Reference
- Architecture: `persona-browser-agent/docs/architecture-proposal-v3.md`
- PoC findings: `persona-browser-agent/poc/FINDINGS.md`
- Phase 0 risks: `persona-browser-agent/docs/phase-0-feasibility-and-risk-mitigations.md`
- Status: `sudd2/fork_sudd_persona_browse_status.md`
