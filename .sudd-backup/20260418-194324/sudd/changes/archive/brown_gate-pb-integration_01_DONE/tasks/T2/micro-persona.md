# Micro-Persona: T2 — Create code-analyzer-be agent

## Consumer
**Who**: code-analyzer-reviewer agent
**Role**: Reads be_codeintel.json produced by code-analyzer-be to cross-validate against fe_codeintel.json and generate the unified codeintel.json, manifest.json, and rubric.md

## Objective
Receive a well-structured be_codeintel.json that accurately catalogs the backend codebase: API endpoints, authentication configuration, data models, data flows, and error handling. The reviewer needs this artifact to trace every frontend action to its backend handler and verify that the two sides agree on contracts.

## Success Criteria
- [ ] JSON schema is fully documented inside the agent prompt so the agent produces consistent output without guessing field names
- [ ] Every extracted item carries a confidence tag (high/medium/low) so the reviewer knows what to trust vs. what to spot-check
- [ ] Agent handles Express, FastAPI, and Django projects — detection logic is explicit in the prompt, not assumed
- [ ] API endpoints include method, path, request schema, response schema, status codes, and auth requirements
- [ ] Authentication config captures strategy (JWT, session, API key, OAuth), token location, and expiration rules
- [ ] Data models list fields, types, relationships, required/optional status, and validation constraints
- [ ] Data flows trace the path from endpoint handler through service layer to database queries, noting any async operations or background jobs
- [ ] Output is a single be_codeintel.json file (not split across multiple files) so the reviewer has one artifact to ingest
