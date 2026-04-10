# Archive: brown_gate-pb-integration_01

## Outcome: DONE (design/prompt change — validated by human review)

## Summary
Aligned SUDD's gate workflow and UX agents with persona-browser-agent v3.1 architecture. Replaced redundant browser sessions with call-once-share-results pattern, added code-analyzer pipeline with adversarial rubric review, PB spot check for hallucination detection, and unified scoring formula.

## What Changed

### New Agents (4)
- `sudd/agents/code-analyzer-fe.md` — Haiku, reads frontend code → fe_codeintel.json
- `sudd/agents/code-analyzer-be.md` — Haiku, reads backend code → be_codeintel.json
- `sudd/agents/code-analyzer-reviewer.md` — Sonnet, cross-validates + generates codeintel/manifest/rubric
- `sudd/agents/rubric-adversary.md` — Haiku, adversarial rubric critique (2 iterations)

### Rewritten Agents (2)
- `sudd/agents/persona-validator.md` — removed all browser access, now reads PB reports only
- `sudd/agents/ux-tester.md` — removed browser-use + intuitiveness framework, added PB spot check via Playwright-over-CDP

### Rewritten Commands (1)
- `sudd/commands/micro/gate.md` — Steps 2a-2e rewrite: code-analyzer pipeline → PB call → report reading → unified scoring

### Updated Config (1)
- `sudd/sudd.yaml` — 4 new agents, scoring formula, navigator limits, safety/circuit breakers

## Key Design Decisions
- D1: persona-validator has NO browser access (pure report reader)
- D2: ux-tester uses Playwright-over-CDP on PB's Chrome instance
- D3: Gate owns dev server lifecycle (start once, kill after aggregation)
- D4: Critical assessment preserved as SUDD-level check on PB report
- D5: PB spot check catches hallucinations (2-3 PASS + 1 FAIL random verification)
- D6: Unified scoring formula owned by gate (defined in sudd.yaml)

## Lessons Learned
- Splitting the monolithic Reviewer into deterministic Network Verifier + LLM Score Reconciler reduces cognitive overload and makes network verification debuggable
- Adversarial rubric review (2 iterations) prevents vague/untestable criteria from reaching the scoring pipeline
- PB spot check via Playwright-over-CDP (same Chrome instance) is the cheapest way to catch false passes — ~10-15s per gate

## Dependencies
- persona-browser-agent v3.1 implementation (Phases 1-4) must complete before these agents can be tested against real PB reports
- brown_validation-rubrics_01 (already DONE — persona objectives, anchored rubrics)

## Completed: 2026-03-31
