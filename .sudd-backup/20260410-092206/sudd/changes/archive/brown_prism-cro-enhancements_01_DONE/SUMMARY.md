# Archive: brown_prism-cro-enhancements_01

## Outcome: DONE (quick wins + ME3 applied; ME1/ME2 deferred to PB implementation)

## Summary
Integrated high-value ideas from Project Prism and UX/CRO research. Added deterministic Web Vitals + z-index obscuration checks to ux-tester, enriched PB rubric FORMS criteria, and created a CRO rubric template.

## Applied

### QW1: Web Vitals in ux-tester
- Added LCP (<2500ms), CLS (<0.1), and interaction CLS delta checks
- Deterministic via Playwright `performance` API, zero LLM cost
- File: `sudd/agents/ux-tester.md`

### QW2: Z-index obscuration check
- Added `document.elementFromPoint()` verification for all interactive elements
- Catches cookie banners, modals, third-party overlays blocking CTAs
- File: `sudd/agents/ux-tester.md`

### QW3: Enriched PB rubric FORMS
- Added: `forms.labels_not_placeholder_only`, `forms.multi_step_progress`, `forms.privacy_text_clear`, `forms.cta_benefit_oriented`
- File: `persona-browser-agent/rubrics/pb-feature-rubric.md`

### ME3: CRO rubric template
- Created opt-in rubric for marketing/conversion projects
- Covers: landing pages, pricing, signup/onboarding, lead forms, persuasion (Cialdini + Fogg)
- File: `persona-browser-agent/rubrics/cro-rubric-template.md`

## Deferred (PB repo code changes, track separately)
- **ME1**: Style Verifier (`style_verifier.py`) — deterministic design token verification via CDP
- **ME2**: Diff-aware manifest on retry — `--changed-pages` flag + cached report merging

## Completed: 2026-03-31
