# Micro-Persona: T1 — Create code-analyzer-fe agent

## Consumer
**Who**: code-analyzer-reviewer agent
**Role**: Reads fe_codeintel.json produced by code-analyzer-fe to cross-validate against be_codeintel.json and generate the unified codeintel.json, manifest.json, and rubric.md

## Objective
Receive a well-structured fe_codeintel.json that accurately catalogs the frontend codebase: routes, components, form validation rules, design tokens, and their relationships. The reviewer needs this artifact to be machine-parseable, confidence-tagged, and comprehensive enough to generate a meaningful validation rubric without reading the source code itself.

## Success Criteria
- [ ] JSON schema is fully documented inside the agent prompt so the agent produces consistent output without guessing field names
- [ ] Every extracted item carries a confidence tag (high/medium/low) so the reviewer knows what to trust vs. what to spot-check
- [ ] Agent handles React, Vue, Next.js, and plain HTML projects — detection logic is explicit in the prompt, not assumed
- [ ] Routes include path, component mapping, guard/auth requirements, and any dynamic segments
- [ ] Components list props, emitted events, slot usage, and parent-child relationships
- [ ] Form validation rules capture field name, rule type, error message, and whether validation is client-only or mirrors a backend rule
- [ ] Design tokens capture color palette, typography scale, spacing units, and breakpoints with source file references
- [ ] Output is a single fe_codeintel.json file (not split across multiple files) so the reviewer has one artifact to ingest
