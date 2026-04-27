# Design: brown_gate-pb-integration_01

## Metadata
sudd_version: 3.3
architecture_ref: persona-browser-agent/docs/architecture-proposal-v3.md

## Architecture Overview

```
GATE WORKFLOW (revised)
═══════════════════════

Step 0: Macro-wiring check (unchanged)
Step 1: Identify consumers (unchanged)

Step 2a: CODE-ANALYZER PIPELINE (NEW — SUDD-side, runs once per gate)
  ┌──────────────────┐    ┌──────────────────┐
  │ code-analyzer-fe │    │ code-analyzer-be │
  │ (Haiku)          │    │ (Haiku)          │
  │ reads frontend   │    │ reads backend    │
  └────────┬─────────┘    └────────┬─────────┘
           │  IN PARALLEL          │
           └──────────┬────────────┘
                      ▼
           ┌──────────────────────┐
           │ code-analyzer-       │
           │ reviewer (Sonnet)    │
           │ merges, cross-       │
           │ validates, generates │
           │ draft rubric         │
           └──────────┬───────────┘
                      ▼
           ┌──────────────────────┐
           │ rubric-adversary     │──── critique ──→ reviewer revises
           │ (Haiku, 2 rounds)   │──── critique ──→ reviewer finalizes
           └──────────┬───────────┘
                      │
                      ▼
           codeintel.json + manifest.json + rubric.md (hardened)

Step 2b: BROWSER TESTING (gate owns lifecycle)
  ┌─────────────────────────────────────────┐
  │ Gate starts dev server (ONCE)           │
  │ Gate saves CDP port for later           │
  │                                         │
  │ FOR EACH persona (can be parallel):     │
  │   persona-test --persona ... --output   │
  │   → browser-reports/{name}.json         │
  │                                         │
  │ Chrome instance stays alive             │
  └─────────────────────┬───────────────────┘
                        │
Step 2c + 2d: AGENTS READ REPORTS (parallel)
  ┌──────────────────────┐  ┌───────────────────────────────┐
  │ persona-validator    │  │ ux-tester                     │
  │ (reads report ONLY)  │  │ (reads report +               │
  │                      │  │  Playwright-over-CDP:          │
  │ No browser.          │  │  - spot check (2-3 PASS +     │
  │ No Playwright.       │  │    1 FAIL random verify)       │
  │ No browser-use.      │  │  - console errors              │
  │                      │  │  - accessibility audit         │
  │ Provides:            │  │  - design system CSS           │
  │ - 1st person verdict │  │                               │
  │ - EXEMPLARY/STRONG   │  │ Provides:                     │
  │ - critical assessment│  │ - spot_check_results[]         │
  │ - deal-breaker check │  │ - technical_issues[]           │
  │ - objective walkthru │  │ - confidence                   │
  └──────────┬───────────┘  └──────────┬────────────────────┘
             │     PARALLEL            │
             └────────────┬────────────┘
                          ▼
Step 2e: UNIFIED SCORING (gate applies formula)
  ┌────────────────────────────────────────┐
  │ pb_score >= 98                         │
  │ consumer_score >= 98                   │
  │ verification_score == 100              │
  │ No deal-breakers (HIGH confidence)     │
  │ No API 500                             │
  │ Auth flow verified                     │
  │ Manifest coverage 100%                 │
  │ persona-validator == EXEMPLARY         │
  │ spot check passed                      │
  │ + penalties: network, manifest, exp    │
  └────────────────┬───────────────────────┘
                   ▼
Step 3: PASS/FAIL (unchanged logic)
Step 3b: CRITICAL ASSESSMENT (preserved, references PB report)
Step 4: ESCALATION (unchanged)

  Gate kills dev server + Chrome after Step 2e.
```

## Component: code-analyzer-fe

### Responsibility
Read frontend source code and extract structured ground truth for browser testing.

### Dependencies
- Frontend source code accessible via file system
- specs.md, design.md for context

### Interface
- Input: frontend source files, specs.md, design.md
- Output: `changes/{id}/fe_codeintel.json`

### Implementation Notes
- Agent markdown file at `sudd/agents/code-analyzer-fe.md`
- Model: Haiku (cheap, focused on pattern extraction)
- Extracts: routes, components per page, form fields + validation, error message strings, CSS/design tokens, accessibility attributes, frontend API call sites
- Must handle: React Router, Vue Router, Next.js App Router, plain HTML
- Confidence tagging: HIGH (explicit patterns) / MEDIUM (inferred) / LOW (guesswork)

## Component: code-analyzer-be

### Responsibility
Read backend source code and extract API contracts, auth config, and data flows.

### Dependencies
- Backend source code accessible via file system
- specs.md for context

### Interface
- Input: backend source files, specs.md
- Output: `changes/{id}/be_codeintel.json`

### Implementation Notes
- Agent markdown file at `sudd/agents/code-analyzer-be.md`
- Model: Haiku (cheap, focused on pattern extraction)
- Extracts: API endpoints (method, path, handler, middleware), request/response schemas, auth config (mechanism, token/cookie details, protected routes), backend validation, data writes/reads
- Must handle: Express, FastAPI, Django, plain Node.js
- Confidence tagging same as FE

## Component: code-analyzer-reviewer

### Responsibility
Merge FE+BE codeintel, cross-validate wiring, trace data flows, generate manifest + draft rubric + merged codeintel.

### Dependencies
- fe_codeintel.json, be_codeintel.json
- specs.md, design.md, personas/*.md

### Interface
- Input: fe_codeintel.json, be_codeintel.json, specs.md, design.md, personas/*.md
- Output: `changes/{id}/codeintel.json`, `changes/{id}/manifest.json`, `changes/{id}/rubric.md` (draft)

### Implementation Notes
- Agent markdown file at `sudd/agents/code-analyzer-reviewer.md`
- Model: Sonnet (reasoning for cross-validation)
- Cross-validates: FE endpoint URLs match BE routes, field names match, status codes match
- Traces: data flows from write endpoints → DB → read endpoints
- Generates: verification tasks from data flows, auth_flow from auth config, manifest pages from routes
- Draft rubric: Must Pass / Should Pass / Deal-Breaker per page from specs + code
- Flags uncertainties with `"confidence": "low"`
- Also called for rubric revision (receives adversary critique, outputs revised rubric)

## Component: rubric-adversary

### Responsibility
Adversarially review auto-generated consumer rubric for quality and completeness.

### Dependencies
- Draft rubric.md from code-analyzer-reviewer
- specs.md, design.md, task objectives

### Interface
- Input: rubric.md (draft or v2), specs.md, design.md, objectives
- Output: structured critique (gaps, vague criteria, untestable items, priority mismatches)

### Implementation Notes
- Agent markdown file at `sudd/agents/rubric-adversary.md`
- Model: Haiku (cheap, critique-focused)
- Runs twice: once on draft, once on v2
- Checks: specificity, completeness, testability, priority correctness, contradictions, over-specification
- Output format: numbered list of issues with severity (CRITICAL/IMPORTANT/MINOR) and suggested fix

## Component: persona-validator (Revised)

### Responsibility
Impersonate the consumer and judge whether the PB report evidence shows the output delivers value.

### Dependencies
- browser-reports/{name}.json (from PB)
- personas/*.md (persona research)
- specs.md, design.md, tasks.md (context)

### Interface
- Input: PB report JSON, persona research, change context
- Output: {score, level, objectives_met, critical_assessment, confidence}

### Implementation Notes
- REWRITE of existing `sudd/agents/persona-validator.md`
- Remove: ALL Playwright references, ALL browser-use subprocess calls, ALL dev server starting, ALL screenshot taking, entire "Browser-Based Validation" section, entire "Run browser-use persona simulation" section
- Keep: first-person narrative, EXEMPLARY/STRONG scoring, critical assessment, handoff contract check, deal-breaker check, objective walkthrough, traceability check
- Add: reading from PB report JSON fields (consumer_criteria, experience, deal_breakers, network_verification, verification_tasks, manifest_coverage)
- Add: citing PB report evidence in objective walkthrough (e.g., "PB report shows criterion X: PASS with evidence Y")
- Add: incorporating network_verification issues and verification_task failures into deal-breaker check
- cli_override stays claude-code (needs full context for judgment, but no browser tools needed)

## Component: ux-tester (Revised)

### Responsibility
Spot-check PB's findings via Playwright and run technical checks that PB can't do.

### Dependencies
- browser-reports/{name}.json (from PB)
- Chrome CDP port (from PB's browser instance, saved by gate)
- design-system/MASTER.md (if exists)

### Interface
- Input: PB report JSON, CDP connection info, design system reference
- Output: {verdict, score, spot_check_results[], technical_issues[], confidence}

### Implementation Notes
- REWRITE of existing `sudd/agents/ux-tester.md`
- Remove: browser-use subprocess calls, own intuitiveness framework (discoverability/cognitive load/flow/error recovery sections), own scoring formula (40/30/30 split)
- Keep: console error detection, accessibility quick check, design system compliance, screenshot strategy for evidence
- Add: Playwright-over-CDP connection (`chromium.connect_over_cdp(cdp_url)`)
- Add: PB spot check logic:
  1. Parse PB report pb_criteria + consumer_criteria
  2. Filter to Playwright-verifiable criteria (element counts, visibility, text content, form submission, error state triggers)
  3. Random select: 2-3 from PASS results, 1 from FAIL results
  4. Execute Playwright assertions for each
  5. Compare results, output spot_check_results[] with {criterion_id, pb_result, playwright_result, match}
- Add: fallback if CDP connection fails → launch own Playwright instance (degraded, flag in output)
- cli_override stays claude-code (needs Playwright MCP tools)

## Component: gate.md (Revised)

### Responsibility
Orchestrate the entire validation pipeline from code analysis through scoring.

### Implementation Notes
- REWRITE Steps 2-3b of existing `sudd/commands/micro/gate.md`
- Steps 0-1 unchanged
- New Step 2a: Code-analyzer pipeline dispatch (sequential: FE+BE parallel → reviewer → adversary loop)
- New Step 2b: Dev server lifecycle + PB call per persona
- New Step 2c: persona-validator dispatch (reads report)
- New Step 2d: ux-tester dispatch (reads report + Playwright-over-CDP)
- Step 2c and 2d run in parallel
- New Step 2e: Unified scoring formula from sudd.yaml
- Step 3: PASS/FAIL (unchanged logic, but references new scoring)
- Step 3b: Critical assessment (preserved, now references PB report evidence)
- Step 4: ESCALATION (unchanged)
- Add: pre-flight checklist before Step 2b (PB installed? API key? dev server? manifest? rubric? codeintel?)
- Add: dev server start/stop lifecycle management
- Add: CDP port capture and passing to ux-tester
- Add: non-UI change detection (skip Steps 2a-2d for non-UI changes, use existing flow)

## Component: sudd.yaml (Updated)

### Implementation Notes
- Add new agents to agents section:
  ```yaml
  code-analyzer-fe:     { tier: low, context: curated }
  code-analyzer-be:     { tier: low, context: curated }
  code-analyzer-reviewer: { tier: mid, context: full }
  rubric-adversary:     { tier: low, context: curated }
  ```
- Add to browser_use section:
  ```yaml
  navigator:
    max_steps: 50
    timeout_seconds: 120
    app_domains: []
  rubric_threshold:
    pb: 98
    consumer: 98
    verification: 100
  scoring:
    must_pass_weight: 1.0
    should_pass_weight: 0.5
    manifest_missing_penalty: 10
    experience_low_penalty: 5
    network_error_penalty: 15
    verification_fail_penalty: 20
    spot_check_mismatch_penalty: 15
  deal_breaker_policy: "instant_fail"
  ```
- Add safety section:
  ```yaml
  safety:
    max_cost_per_change: 5.00
    identical_failure_stuck_after: 3
  ```
- Update model to `google/gemini-2.5-flash` (not `-preview`, per PoC findings)

## Data Flow

```
Frontend code ──→ code-analyzer-fe ──→ fe_codeintel.json ──┐
                                                            ├──→ code-analyzer-reviewer
Backend code ───→ code-analyzer-be ──→ be_codeintel.json ──┘          │
                                                          ┌───────────┘
                                                          ▼
                                               codeintel.json
                                               manifest.json
                                               rubric.md (draft)
                                                          │
                                                          ▼
                                               rubric-adversary
                                               (2 iterations)
                                                          │
                                                          ▼
                                               rubric.md (hardened)
                                                          │
                     ┌────────────────────────────────────┘
                     ▼
              persona-browser-agent
              (per persona, saves report)
                     │
                     ├──→ browser-reports/{name}.json
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  persona-       ux-tester     gate Step 2e
  validator      (spot check   (unified
  (reads         + technical    scoring
   report)        checks)       formula)
        │            │            │
        └────────────┴────────────┘
                     │
                     ▼
              PASS / FAIL + action items
```

## File Changes

### New Files
- `sudd/agents/code-analyzer-fe.md` — Frontend code analysis agent prompt
- `sudd/agents/code-analyzer-be.md` — Backend code analysis agent prompt
- `sudd/agents/code-analyzer-reviewer.md` — Cross-validation + artifact generation agent prompt
- `sudd/agents/rubric-adversary.md` — Adversarial rubric review agent prompt

### Modified Files
- `sudd/commands/micro/gate.md` — Steps 2-3b rewrite (code-analyzer pipeline, dev server lifecycle, report-reading pattern, unified scoring, pre-flight checklist)
- `sudd/agents/persona-validator.md` — Remove all browser access, add report-reading logic
- `sudd/agents/ux-tester.md` — Remove browser-use + intuitiveness framework, add spot check + Playwright-over-CDP
- `sudd/sudd.yaml` — Add new agents, scoring formula, navigator config, safety section, fix model ID

### Unchanged Files
- `sudd/commands/micro/gate.md` Steps 0, 1, 3 (PASS/FAIL logic), 4 (escalation)
- `sudd/standards.md`
- `sudd/vision.md`
- All other agents (coder, architect, qa, etc.)
