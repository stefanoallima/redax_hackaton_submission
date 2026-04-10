# Change: brown_prism-cro-enhancements_01

## Status
proposed

## Summary
Integrate high-value ideas from Project Prism (white-box + black-box convergence) and UX/CRO best practices research into SUDD + persona-browser-agent. Adds deterministic checks that bypass LLMs (Web Vitals, z-index obscuration, design token math), enriches PB rubrics, and introduces diff-aware retry optimization.

## Motivation
Two research documents identified opportunities to make the validation pipeline faster, cheaper, and more accurate:

1. **Project Prism** showed that many visual checks currently done by LLMs (color matching, spacing, element visibility) can be done deterministically via CDP in <15ms. Our visual scorer spends tokens asking "does the button color match?" when `CSS.getComputedStyleForNode` gives the exact answer for free.

2. **UX/CRO best practices** research identified form UX patterns, CRO techniques, and Web Vitals thresholds that our PB rubric doesn't cover. Adding these means catching more real-world UX failures.

3. **Retry efficiency** — currently PB re-tests ALL pages on every retry even when only 1 file changed. Diff-aware manifests could cut retry time by 50-70%.

## Scope

### Quick Wins (minimal effort, high value)

**QW1: Web Vitals in ux-tester technical checks**
- Add 3 performance checks via Playwright `performance` API:
  - LCP (Largest Contentful Paint) < 2.5s
  - CLS (Cumulative Layout Shift) < 0.1
  - No layout shifts during user interaction
- Deterministic, zero LLM cost, ~2s per page
- Repo: sudd2 (`sudd/agents/ux-tester.md`)

**QW2: Z-index obscuration check in ux-tester**
- Via Playwright `document.elementFromPoint(x, y)` on every interactive element (buttons, links, inputs)
- Verify the top-most element at those coordinates IS the expected element
- Catches: cookie banners, modals, sticky headers blocking CTAs, third-party overlays
- Deterministic, zero LLM cost, ~1s per page
- Repo: sudd2 (`sudd/agents/ux-tester.md`)

**QW3: Enrich PB rubric FORMS criteria**
- Add from UX research:
  - "Labels are above inputs, not placeholder-only" (placeholder-only labels disappear on focus)
  - "Multi-step forms have visible progress indicator"
  - "CTA text is benefit-oriented, not generic ('Get started' not 'Submit')"
  - "Privacy/consent text is clear and non-intimidating near forms"
- Repo: persona-browser-agent (`rubrics/pb-feature-rubric.md`)

### Medium Effort (worth doing)

**ME1: Deterministic design token verification (Style Verifier)**
- New deterministic module in PB: `persona_browser/style_verifier.py`
- Uses CDP `CSS.getComputedStyleForNode` to extract computed CSS values for elements
- Compares against codeintel `design_tokens`: exact color match (hex), font-family, border-radius, spacing
- Replaces LLM visual scorer for these specific checks — math instead of vision
- Runs in parallel with scorers (like network_verifier)
- Visual scorer still handles spatial layout, visual hierarchy, overall aesthetics — things math can't assess
- Cost: $0.00 per check (deterministic). Saves ~$0.01-0.03 per gate by offloading token-heavy color/spacing checks from visual scorer
- Repo: persona-browser-agent (new module + integration into pipeline)

**ME2: Diff-aware manifest on retry**
- When code changes between gate retries, code-analyzer-reviewer generates a `manifest_diff`:
  - Which pages/components had code changes (from `git diff`)
  - Which pages are unchanged
- PB navigator uses `--changed-pages` flag to focus on changed pages only
- Unchanged pages: reuse cached PB report from previous run
- Score Reconciler merges new results for changed pages with cached results for unchanged pages
- Saves 30-90s per retry on multi-page apps (navigator doesn't re-navigate unchanged pages)
- Repo: sudd2 (code-analyzer-reviewer, gate.md) + persona-browser-agent (navigator, pipeline)

**ME3: CRO rubric template**
- New file: `rubrics/cro-rubric-template.md` in PB repo
- Available as an optional rubric for marketing/conversion projects
- Based on Cialdini's principles + Fogg behavior model + pricing page patterns:
  - Social proof near CTAs (testimonials, logos, user counts)
  - Scarcity/urgency used ethically (not dark patterns)
  - Pricing: 3-4 tiers, recommended tier visually distinct, annual/monthly toggle
  - Value prop visible before friction (signup form below value explanation)
  - Fogg triggers: motivation + ability + prompt aligned at decision points
- NOT built into PB's universal rubric (project-specific, opt-in via `--rubric`)
- SUDD's code-analyzer-reviewer can auto-select this template when the project has marketing/pricing pages
- Repo: persona-browser-agent (`rubrics/cro-rubric-template.md`)

### NOT Included
- ONNX/YOLO edge-CV engine (too complex, LLM vision sufficient)
- HMR state injection for rapid state testing (interesting but orthogonal)
- Full CrUX/BigQuery integration (overkill for dev-time testing)
- ROI screenshot cropping (optimization for later — visual scorer handles full screenshots fine)

## Success Criteria

### Quick Wins
- [ ] ux-tester.md includes Web Vitals checks (LCP, CLS) in technical checks section
- [ ] ux-tester.md includes z-index obscuration check via `elementFromPoint`
- [ ] pb-feature-rubric.md has 4 new FORMS criteria from UX research

### Medium Effort
- [ ] style_verifier.py exists in PB repo with CDP-based color/font/spacing verification
- [ ] pipeline.py runs style_verifier in parallel with scorers
- [ ] gate.md supports diff-aware retry (changed-pages-only re-testing)
- [ ] code-analyzer-reviewer generates manifest_diff on retry
- [ ] cro-rubric-template.md exists with Cialdini + Fogg + pricing patterns

## Dependencies
- brown_gate-pb-integration_01 (DONE — gate workflow, agent rewrites)
- brown_doc-alignment_01 (PROPOSED — doc fixes, should complete first)
- PB Phases 0-4 (DONE — pipeline, scorers, reconciler, all implemented)

## Implementation Order

```
Quick wins (can do now, no code changes needed):
  QW1 + QW2: Update ux-tester.md agent prompt
  QW3: Update pb-feature-rubric.md

Medium effort (after doc-alignment):
  ME3: Create cro-rubric-template.md (no code, just rubric content)
  ME1: Build style_verifier.py + integrate into pipeline
  ME2: Diff-aware manifest (requires changes in both repos)
```

## Files Modified

### sudd2 repo
- `sudd/agents/ux-tester.md` — add Web Vitals + z-index obscuration checks (QW1, QW2)

### persona-browser-agent repo
- `rubrics/pb-feature-rubric.md` — add 4 FORMS criteria (QW3)
- `rubrics/cro-rubric-template.md` — NEW: CRO/marketing rubric template (ME3)
- `persona_browser/style_verifier.py` — NEW: deterministic design token verification (ME1)
- `persona_browser/pipeline.py` — integrate style_verifier in parallel (ME1)
- `persona_browser/cli.py` — add `--changed-pages` flag (ME2)
- `persona_browser/output_parser.py` — support partial page re-testing (ME2)
- `schemas/style-verifier-output.schema.json` — NEW: schema for style verification (ME1)

### sudd2 repo (ME2)
- `sudd/agents/code-analyzer-reviewer.md` — generate manifest_diff on retry
- `sudd/commands/micro/gate.md` — pass `--changed-pages` on retry, merge cached + new results

## Risk
- **Style Verifier CDP access**: Requires connecting to PB's Chrome instance via CDP, same pattern as ux-tester Playwright-over-CDP. If CDP session is unavailable, skip style verification (graceful degradation).
- **Diff-aware manifest accuracy**: `git diff` may not capture all affected pages (e.g., shared component changes affect multiple pages). Mitigation: err on the side of re-testing — if a shared component changed, all pages using it are marked as changed.
- **CRO rubric subjectivity**: Some CRO criteria (social proof "present and relevant") require LLM judgment. Keep criteria observable and specific.

## Reference
- Project Prism spec: `persona-browser-agent/docs/prism_brief.md`
- UX/CRO research: `persona-browser-agent/docs/ux-cro-best-practice_glm.md`
- PB architecture: `persona-browser-agent/docs/architecture-proposal-v3.md`
- SUDD gate integration: `sudd2/sudd/changes/archive/brown_gate-pb-integration_01_DONE/`
