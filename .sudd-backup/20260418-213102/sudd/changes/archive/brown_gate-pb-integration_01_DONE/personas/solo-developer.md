# Persona: Solo Developer (Overnight Runner)

**Role**: Solo developer using SUDD autonomously overnight
**Context**: Kicks off `/sudd:run` before bed, expects quality-gated results in the morning

## Goals
1. Gate catches real bugs — not false positives from bad codeintel or PB hallucinations
2. Gate doesn't burn through retries on the same unfixable issue (circuit breakers work)
3. Morning review is fast — reports are clear, action items are specific and categorized
4. Costs are predictable — no runaway LLM spending from loops

## Frustrations
1. Gate says PASS but the feature is broken (false pass — silent, dangerous)
2. Gate fails 8 times on the same codeintel extraction error (waste)
3. Report says "fix the UI" with no specific page, criterion, or evidence
4. Persona-validator and ux-tester both launch browsers for the same test (waste)

## Deal-Breakers
1. Redundant browser sessions — if PB already navigated, no agent should re-navigate
2. Silent false PASSes — if PB says PASS but the form doesn't actually work, that's unacceptable
3. Scattered scoring — if persona-validator says 98 and ux-tester says 72 on the same evidence, trust is broken

## Objectives
1. Run a gate on a UI change and verify: PB called once per persona, no redundant browser sessions
2. Review the gate report and verify: unified scoring formula applied, action items categorized by [WIRING]/[FRONTEND]/[BACKEND]/[AUTH]
3. Verify spot check caught a planted mismatch (PB reports PASS on a criterion that Playwright shows FAIL)
4. Verify persona-validator output contains zero Playwright/browser-use references
