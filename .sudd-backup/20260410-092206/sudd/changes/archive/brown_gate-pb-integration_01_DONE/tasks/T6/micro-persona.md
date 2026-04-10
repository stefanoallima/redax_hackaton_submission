# Micro-Persona: T6 — Rewrite ux-tester agent

## Consumer
**Who**: gate.md (Steps 2-3b gate logic)
**Role**: Reads spot check results and technical issue list to independently verify persona-browser findings and surface technical problems invisible to persona-based testing

## Objective
Get independent persona-browser verification via spot checks plus technical checks that catch issues personas would not notice (console errors, accessibility violations, network failures). The gate needs this as a cross-check against persona-validator scores — if the ux-tester finds critical issues the personas missed, the gate can downgrade confidence or fail the change.

## Success Criteria
- [ ] spot_check_results[] array present with at least one entry per page, each containing: the PB finding being verified, the ux-tester's independent re-check result, and agree/disagree status
- [ ] PB vs Playwright comparison is explicit — for each spot check, the ux-tester states whether the persona-browser report was accurate, optimistic, or missed something
- [ ] Console errors are captured with page URL, error message, and severity classification (blocking vs. warning)
- [ ] Accessibility audit runs against WCAG 2.1 AA with violations listed per page, including element selector and rule ID
- [ ] CDP (Chrome DevTools Protocol) connection status is verified and reported — confirms the browser agent actually had a live connection during its run
- [ ] Network request failures (4xx, 5xx, timeouts) are logged with endpoint URL, status code, and whether the failure is intermittent or consistent
- [ ] Output format is structured JSON that gate.md can parse programmatically alongside persona-validator output
