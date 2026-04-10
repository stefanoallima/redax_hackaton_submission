# Micro-Persona: T8 — Update sudd.yaml

## Consumer
**Who**: All agents (code-analyzer-fe, code-analyzer-be, code-analyzer-reviewer, rubric-adversary, persona-validator, ux-tester, gate.md, and others)
**Role**: Read sudd.yaml config for agent dispatch tiers, scoring weights, navigator concurrency limits, safety thresholds, and model assignments

## Objective
Get a correct, complete configuration file that every agent can rely on at runtime. A missing agent registration means it never gets called. A wrong scoring weight means the gate produces misleading verdicts. A missing safety threshold means the sentinel cannot enforce limits. Every agent reads this file — a single error propagates everywhere.

## Success Criteria
- [ ] All 4 new agents are registered: code-analyzer-fe, code-analyzer-be, code-analyzer-reviewer, rubric-adversary — each with correct file path, tier assignment, and description
- [ ] Scoring section is complete: weights for Must Pass, Should Pass, Deal-Breaker, and spot-check agreement are defined and sum correctly
- [ ] Safety section is present: max retries, token budget per gate run, navigator concurrency limit, and timeout per persona-browser session
- [ ] Model ID is fixed — references the correct model identifier consistent with the escalation strategy (free tier, Sonnet, Opus)
- [ ] Existing agent registrations are preserved — no agents removed or renamed unless explicitly part of this change
- [ ] YAML is valid — parseable by standard YAML parsers without errors (no tabs, correct indentation, proper quoting)
- [ ] Scoring threshold matches the 98/100 PASS requirement documented in project memory
