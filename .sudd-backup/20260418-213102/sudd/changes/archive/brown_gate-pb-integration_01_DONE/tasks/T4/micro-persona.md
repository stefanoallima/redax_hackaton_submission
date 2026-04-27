# Micro-Persona: T4 — Create rubric-adversary agent

## Consumer
**Who**: code-analyzer-reviewer agent
**Role**: Receives the adversary's critique and uses it to revise the rubric.md, tightening vague criteria, adding missing coverage, and correcting priority assignments before the rubric reaches the persona-browser-agent

## Objective
Receive actionable critique that strengthens the rubric without bloating it. The reviewer needs specific, fixable problems — not vague complaints. Every issue raised must include enough context for the reviewer to make the fix in one pass without re-analyzing the codebase.

## Success Criteria
- [ ] Critique identifies vague criteria — items where a tester could not determine pass/fail without subjective judgment — and suggests concrete rewording
- [ ] Critique identifies missing features — functionality visible in codeintel.json that has no corresponding rubric item — with the specific codeintel path cited
- [ ] Critique identifies untestable items — rubric entries that cannot be verified through browser interaction alone (e.g., "database is normalized") — and recommends removal or replacement
- [ ] Critique identifies priority mismatches — items marked Must Pass that are cosmetic, or Deal-Breakers marked Should Pass — with rationale for re-classification
- [ ] Each critique item is structured with: rubric line reference, issue type, explanation, and suggested fix so the reviewer can apply changes mechanically
- [ ] Critique does not introduce new rubric items directly — it only recommends additions for the reviewer to validate and add
- [ ] Adversary checks that every page in manifest.json has at least one Must Pass rubric item
