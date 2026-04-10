# Persona: Solo Developer (Fully Autonomous Operator)

**Role**: Solo developer using SUDD fully autonomously
**Context**: Has a backlog of 3-5 change proposals. Runs `sudd auto` before bed or before leaving for work. Expects results when they return.

## Goals
1. Wake up to multiple completed changes, not just one
2. Clear morning report tells me exactly what happened — no detective work
3. Time budget is respected — session stops before my machine runs all day
4. Install the binary on my CI server or a teammate's machine with zero setup

## Frustrations
1. Running `/sudd:run`, coming back to one change done, having to manually start the next
2. Context window fills up after one big change — no way to continue to the next
3. A runaway change burns 6 hours on retries while 3 easy changes sit in the queue
4. No summary — have to check git log, archive folders, and state.json manually
5. Can't easily share the tool — requires installing an entire dev environment

## Deal-Breakers
1. `sudd auto` corrupts state.json or leaves dirty git state between changes
2. Time limit is ignored (session runs past 8 hours because nobody checks)
3. A crash mid-session means all queue progress is lost
4. Auto mode modifies how single changes are processed (breaks existing /sudd:run)
5. Requires Python/Node/runtime dependencies beyond the CLI agent itself

## Objectives
1. Queue 3 proposals, run `sudd auto`, return to a morning report showing 3 changes processed
2. Set max_hours to 2 and verify the session stops after the time limit (finishes current change, then stops)
3. Have one change go STUCK and verify the session skips it and processes the next
4. Kill the process mid-session (Ctrl+C twice), restart with `sudd auto`, verify it resumes
5. Verify each change ran in a separate CLI session (check log files in auto-reports/)
6. Run `make build-all`, copy the binary to a different machine, run `sudd auto` — works
7. Verify `/sudd:run` (without auto) still works identically
