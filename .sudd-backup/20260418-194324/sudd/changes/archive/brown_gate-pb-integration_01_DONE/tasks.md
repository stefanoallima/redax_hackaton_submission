# Tasks: brown_gate-pb-integration_01

## Implementation Tasks

- [x] T1: Create code-analyzer-fe agent
  - Files: sudd/agents/code-analyzer-fe.md
  - SharedFiles: none
  - Effort: M
  - Dependencies: none
  - Details: Agent prompt for Haiku that reads frontend source code and extracts routes, components, form fields, validation rules, error messages, design tokens, accessibility attributes, and frontend API call sites. Output schema: fe_codeintel.json. Must handle React Router, Vue Router, Next.js App Router, plain HTML. Include confidence tagging per extraction category (HIGH/MEDIUM/LOW).

- [x] T2: Create code-analyzer-be agent
  - Files: sudd/agents/code-analyzer-be.md
  - SharedFiles: none
  - Effort: M
  - Dependencies: none
  - Details: Agent prompt for Haiku that reads backend source code and extracts API endpoints (method, path, handler, middleware chain), request/response schemas, auth config (mechanism, cookie/token details, protected routes), backend validation rules, data writes/reads. Output schema: be_codeintel.json. Must handle Express, FastAPI, Django, plain Node.js. Include confidence tagging.

- [x] T3: Create code-analyzer-reviewer agent
  - Files: sudd/agents/code-analyzer-reviewer.md
  - SharedFiles: none
  - Effort: L
  - Dependencies: T1, T2
  - Details: Agent prompt for Sonnet that merges fe_codeintel.json + be_codeintel.json. Cross-validates FE↔BE wiring (endpoint URLs, field names, status codes). Traces data flows (write → DB → read). Generates: codeintel.json (merged), manifest.json (pages + auth_flow + verification_tasks), draft rubric.md (Must Pass / Should Pass / Deal-Breaker per page). Also handles rubric revision when called with adversary critique input. Include codeintel.json, manifest.json, and rubric.md output schemas in the prompt.

- [x] T4: Create rubric-adversary agent
  - Files: sudd/agents/rubric-adversary.md
  - SharedFiles: none
  - Effort: S
  - Dependencies: T3
  - Details: Agent prompt for Haiku that critiques a consumer rubric against specs, design, and task objectives. Checks: specificity (not vague), completeness (covers all features), testability (verifiable from browser), priority correctness (Must Pass vs Should Pass vs Deal-Breaker alignment), contradictions, over-specification. Output: numbered critique with severity (CRITICAL/IMPORTANT/MINOR) and suggested fix per issue.

- [x] T5: Rewrite persona-validator agent
  - Files: sudd/agents/persona-validator.md
  - SharedFiles: none
  - Effort: L
  - Dependencies: none
  - Details: Remove ALL browser launching (Playwright, browser-use subprocess calls, dev server starting, screenshot taking). Remove entire "Browser-Based Validation" section (lines 56-118 of current file). Remove "Run browser-use persona simulation" section. Keep: first-person narrative, EXEMPLARY/STRONG scoring, critical assessment, handoff contract check, deal-breaker check, objective walkthrough, traceability check, scoring guide. Add: reading from browser-reports/{name}.json (consumer_criteria, experience, deal_breakers, network_verification, verification_tasks, manifest_coverage). Add: citing PB report evidence in objective walkthrough. Add: incorporating network_verification and verification_task failures into assessment. ZERO references to Playwright, mcp__playwright__*, browser-use, or dev server remaining.

- [x] T6: Rewrite ux-tester agent
  - Files: sudd/agents/ux-tester.md
  - SharedFiles: none
  - Effort: L
  - Dependencies: none
  - Details: Remove browser-use subprocess calls. Remove own intuitiveness framework (discoverability/cognitive load/flow/error recovery — all 4 sections). Remove own scoring formula (40/30/30 split). Remove "Run Browser-Use Persona Simulation" section. Keep: console error detection, accessibility quick check, design system compliance check, screenshot strategy for evidence. Add: Playwright-over-CDP connection (`chromium.connect_over_cdp(cdp_url)`) to PB's Chrome instance. Add: PB spot check logic — parse PB report, filter to Playwright-verifiable criteria, random select 2-3 PASS + 1 FAIL, execute Playwright assertions, compare results, output spot_check_results[]. Add: fallback if CDP connection fails (launch own Playwright, flag as degraded). Add: new output format with spot_check_results section. cli_override stays claude-code.

- [x] T7: Rewrite gate.md Steps 2-3b
  - Files: sudd/commands/micro/gate.md
  - SharedFiles: none
  - Effort: L
  - Dependencies: T1, T2, T3, T4, T5, T6
  - Details: Keep Steps 0-1 unchanged. Rewrite Step 2 into 2a/2b/2c/2d/2e. Step 2a: code-analyzer pipeline dispatch (FE+BE parallel → reviewer → adversary 2x loop). Step 2b: dev server lifecycle (start once, health check, save CDP port) + single PB call per persona + status handling (DONE/SKIP/ERROR). Step 2c: persona-validator dispatch (reads report, no browser). Step 2d: ux-tester dispatch (reads report + Playwright-over-CDP spot check + technical checks). 2c+2d run in parallel. Step 2e: unified scoring formula from sudd.yaml. Add pre-flight checklist (PB installed? API key? manifest? rubric? codeintel?). Add non-UI change detection (skip 2a-2d for non-UI changes). Keep Steps 3, 3b (critical assessment references PB report), 4 unchanged in logic.

- [x] T8: Update sudd.yaml
  - Files: sudd/sudd.yaml
  - SharedFiles: sudd/sudd.yaml
  - Effort: S
  - Dependencies: T1, T2, T3, T4
  - Details: Add 4 new agents to agents section (code-analyzer-fe: low, code-analyzer-be: low, code-analyzer-reviewer: mid, rubric-adversary: low). Add navigator config (max_steps, timeout_seconds, app_domains). Add rubric_threshold (pb: 98, consumer: 98, verification: 100). Add scoring section (weights and penalties). Add deal_breaker_policy. Add safety section (max_cost_per_change: 5.00, identical_failure_stuck_after: 3). Fix model to `google/gemini-2.5-flash` (remove `-preview`).

---
Total: 8 tasks | Est. effort: 2S + 2M + 4L
