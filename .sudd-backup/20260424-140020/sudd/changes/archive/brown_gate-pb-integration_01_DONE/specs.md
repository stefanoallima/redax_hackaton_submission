# Specifications: brown_gate-pb-integration_01

## Functional Requirements

### FR-1: Code-Analyzer Pipeline (gate.md Step 2a)
- Given: A change with frontend and/or backend code, specs.md, design.md, personas/*.md
- When: Gate reaches Step 2a (before browser testing)
- Then:
  - Dispatch code-analyzer-fe (Haiku) reading frontend source → fe_codeintel.json
  - Dispatch code-analyzer-be (Haiku) reading backend source → be_codeintel.json
  - FE and BE run in parallel (independent codebases)
  - Dispatch code-analyzer-reviewer (Sonnet) merging FE+BE → codeintel.json + manifest.json + draft rubric.md
  - Dispatch rubric-adversary (Haiku) critiquing draft rubric against specs + design + objectives → critique
  - code-analyzer-reviewer revises rubric → rubric v2
  - rubric-adversary critiques v2 → critique
  - code-analyzer-reviewer finalizes → rubric.md (hardened)
  - All artifacts written to changes/{id}/
  - Re-runs on retry if code changed since last run (git SHA check)
  - Skip code-analyzer-be if no backend code detected
  - Skip entire pipeline if no UI change detected (non-UI changes skip to existing gate flow)

### FR-2: Dev Server Lifecycle (gate.md Step 2b)
- Given: A UI change requiring browser testing
- When: Gate reaches Step 2b
- Then:
  - Gate starts the dev server using the project's dev command (from config or auto-detected)
  - Gate waits for server ready (health check or timeout)
  - Dev server stays alive through Steps 2b-2e
  - Gate kills dev server after Step 2e aggregation completes
  - If server crashes mid-pipeline: gate detects, attempts restart, if restart fails → mark as ERROR

### FR-3: Single PB Call Per Persona (gate.md Step 2b)
- Given: Dev server running, codeintel.json + manifest.json + rubric.md available
- When: Gate dispatches browser testing
- Then:
  - Call persona-browser-agent ONCE per persona:
    ```
    persona-test \
      --persona changes/{id}/personas/{name}.md \
      --url {dev_server_url} \
      --objectives "{from persona ## Objectives}" \
      --manifest changes/{id}/manifest.json \
      --rubric changes/{id}/rubric.md \
      --codeintel changes/{id}/codeintel.json \
      --scope gate \
      --max-steps 50 \
      --timeout 120 \
      --screenshots-dir changes/{id}/screenshots/gate/{name}/ \
      --output changes/{id}/browser-reports/{name}.json
    ```
  - Status handling: DONE → continue, SKIP → technical-checks-only (cap 90), ERROR → -5 penalty
  - Personas CAN be tested in parallel (independent browser sessions)
  - PB's Chrome instance CDP port saved for ux-tester Playwright-over-CDP connection

### FR-4: Persona-Validator Reads Report (gate.md Step 2c)
- Given: browser-reports/{name}.json exists
- When: persona-validator is dispatched
- Then:
  - Reads from report: consumer_criteria, experience, deal_breakers, network_verification, verification_tasks, manifest_coverage
  - Does NOT launch any browser (no Playwright, no browser-use subprocess)
  - Does NOT start any dev server
  - Does NOT take any screenshots
  - Provides: first-person narrative, EXEMPLARY/STRONG scoring, critical assessment, handoff contract check, deal-breaker check, objective walkthrough
  - All evidence cited from the PB report JSON, not from live browser observation
  - If report missing for an objective → mark UNTESTABLE (do NOT fall back to browser)

### FR-5: UX-Tester Spot Check + Technical Checks (gate.md Step 2d)
- Given: browser-reports/{name}.json exists, PB Chrome instance CDP port available
- When: ux-tester is dispatched
- Then:
  - Reads PB report: pb_criteria, features_detected, discrepancies
  - Connects Playwright to PB's Chrome via CDP (`chromium.connect_over_cdp`)
  - **Spot check**: selects 2-3 random Playwright-verifiable criteria from PB PASS results + 1 from FAIL results
  - For each spot check criterion: executes Playwright assertion to independently verify
  - Compares spot check results against PB's reported results
  - **Technical checks** (via same Playwright-over-CDP connection):
    - Console error detection (JavaScript exceptions)
    - Accessibility quick audit (tab navigation, focus states, labels, contrast)
    - Design system CSS compliance (if design-system/MASTER.md exists)
    - Items flagged by Score Reconciler as "needs technical verification"
  - Does NOT have its own intuitiveness framework
  - Does NOT call persona_browser.cli
  - If Playwright-over-CDP connection fails: fall back to launching own Playwright instance (degraded)

### FR-6: Spot Check Outcome Handling
- Given: ux-tester completed spot check with comparison results
- When: Gate processes ux-tester output in Step 2e
- Then:
  - All match PB → high confidence, proceed normally
  - 1 mismatch on non-critical → -15 penalty + flag `pb_spot_check: partial_mismatch` for morning review
  - 1+ mismatch on critical/deal-breaker → gate FAIL with reason `PB reliability concern`
  - FAIL criterion was actually PASS → flag `pb_false_fail_detected`, remove false penalty
  - 2+ mismatches → gate FAIL, mark `PB UNRELIABLE`, require full Playwright validation on retry (score capped at 90)

### FR-7: Unified Scoring Formula (gate.md Step 2e)
- Given: PB report, persona-validator output, ux-tester output (with spot check)
- When: Gate aggregates scores
- Then: Apply unified formula from sudd.yaml:
  ```
  pb_score = pb_pass_rate * 100
  consumer_score = consumer_pass_rate * 100 (Must Pass 100%, Should Pass 50%)
  verification_score = verification_pass_rate * 100
  network_penalty = -15 per API error, instant 0 on 500 or auth handover fail
  manifest_penalty = -10 per missing page
  experience_factor = -5 if satisfaction < 5, -10 if "would not recommend"
  spot_check_penalty = -15 per mismatch (or gate FAIL on critical)
  ```
  All must pass:
  - pb_score >= 98, consumer_score >= 98, verification_score == 100
  - No deal-breakers at HIGH confidence
  - No API 500 during normal flow
  - Auth flow verified, manifest coverage 100%
  - persona-validator level == EXEMPLARY
  - ux-tester spot check passed

### FR-8: Critical Assessment Preserved (gate.md Step 3b)
- Given: All scores pass Step 2e
- When: Gate runs critical assessment
- Then:
  - persona-validator re-reads PB report in critical-assessment mode
  - Checks: weaknesses, wow factor, gut check — same as current Step 3b
  - References PB report evidence (network_verification issues, verification_task results, discrepancies)
  - Can downgrade EXEMPLARY → STRONG if report evidence reveals issues not caught by formula

### FR-9: Lightweight Circuit Breakers (sudd.yaml)
- Given: sudd.yaml safety section configured
- When: Gate runs retries
- Then:
  - max_cost_per_change: pause and mark STUCK if exceeded (tracks PB + code-analyzer costs)
  - identical_failure_stuck_after: 3 (same criterion_id fails 3 consecutive retries → early STUCK)

## Non-Functional Requirements

### NFR-1: No Browser in persona-validator
- Constraint: persona-validator.md must contain ZERO references to Playwright, mcp__playwright__*, browser-use, dev server starting, or screenshot taking
- Rationale: D1 — all browser interaction is PB's job

### NFR-2: Backward Compatibility
- Constraint: Non-UI changes must continue working with existing gate flow (no code-analyzer, no PB)
- Rationale: SUDD handles non-UI changes (APIs, data pipelines) that don't need browser testing

### NFR-3: Cost Ceiling
- Constraint: Code-analyzer pipeline (FE + BE + reviewer + 2x adversary + 2x revision) < $0.30 per run
- Rationale: Runs once per gate, must be cheap enough for 8 retries

### NFR-4: Spot Check Speed
- Constraint: PB spot check (3-4 Playwright assertions) < 15 seconds
- Rationale: Must not significantly extend gate time

## Consumer Handoffs

### Handoff 1: code-analyzer-fe → code-analyzer-reviewer
- Format: JSON
- Schema: fe_codeintel.json (routes, components, validation, design tokens, FE API calls)
- Validation: Must include at least `pages[]` with route definitions

### Handoff 2: code-analyzer-be → code-analyzer-reviewer
- Format: JSON
- Schema: be_codeintel.json (API endpoints, auth config, middleware, data flows)
- Validation: Must include at least `api_endpoints[]` if backend code exists

### Handoff 3: code-analyzer-reviewer → rubric-adversary
- Format: Markdown
- Schema: rubric.md with Must Pass / Should Pass / Deal-Breaker sections per page
- Validation: Every page in manifest.json must have at least one criterion in rubric.md

### Handoff 4: code-analyzer-reviewer → persona-browser-agent
- Format: JSON + Markdown
- Schema: codeintel.json + manifest.json + rubric.md (per v3.1 architecture spec)
- Validation: manifest pages match codeintel pages, rubric references valid codeintel entries

### Handoff 5: persona-browser-agent → persona-validator
- Format: JSON
- Schema: browser-reports/{name}.json (v3.1 output format)
- Validation: status == DONE|SKIP|ERROR, pages[] present, consumer_criteria present

### Handoff 6: persona-browser-agent → ux-tester
- Format: JSON + CDP port
- Schema: browser-reports/{name}.json + Chrome CDP connection info
- Validation: pb_criteria present with criterion_id fields (for spot check selection)

### Handoff 7: ux-tester → gate (Step 2e)
- Format: Structured output
- Schema: {verdict, score, spot_check_results[], technical_issues[], confidence}
- Validation: spot_check_results includes comparison for each checked criterion

## Out of Scope
- persona-browser-agent code changes (separate repo)
- Full circuit breaker implementation (partial retry, cost tracking internals)
- Golden test app (PB repo Phase 3-4)
- Code-analyzer real-world testing (this defines prompts, not validates accuracy)
- Video recording configuration
