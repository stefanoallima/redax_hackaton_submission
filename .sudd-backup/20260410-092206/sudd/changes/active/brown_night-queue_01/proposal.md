# Change: brown_night-queue_01

## Status
proposed

## Summary
Add `sudd auto` — a fully autonomous mode that processes multiple change proposals in sequence without human intervention. Built as a Go subcommand in `sudd-go/`, it launches separate CLI agent sessions for each change, manages budgets, handles crashes, and produces a morning report. Installs as a single cross-compiled binary on any machine.

## Motivation

**The gap**: `/sudd:run` operates on ONE change. After it archives (DONE or STUCK), it updates state.json, prints a session summary, and the CLI agent session ends. If there are 3 proposals in the backlog, the developer has to manually start each one. Three nights for three changes.

**The execution model problem**: `/sudd:run` is a markdown instruction set interpreted by a CLI agent within a single conversation session. After processing one change (potentially 100+ tool calls, multiple agent dispatches, code reviews, gate retries), the context window is exhausted. There is no persistent process to pick up the next change. A markdown-based outer loop can't survive context window boundaries.

**The solution**: A real process — a Go binary — that sits outside the CLI agent. It builds a queue, launches `claude -p "/sudd:run brown {id}"` as a subprocess per change, waits for completion, reads the outcome from state.json/archive, and loops. Each change gets a fresh context window. The scheduler itself uses zero LLM tokens.

**Portability**: The Go binary cross-compiles to darwin/linux/windows via the existing `make build-all`. Install on any machine, any CI runner, any server. No Python, no Node, no runtime dependencies. One binary.

## Scope

### Included

**New Go subcommand: `sudd auto`**
- Builds a queue from `changes/active/*/proposal.md` (status: proposed) + optional vision.md
- Launches a separate CLI agent session per change (`claude -p "/sudd:run ..."` or `opencode -p ...`)
- Waits for each to complete, reads outcome from filesystem
- Enforces session-level budgets (time, change count)
- Handles crashes via persisted state in state.json
- Writes morning report to `sudd/auto-reports/{date}.md`
- Cross-compiles to darwin/linux/windows (existing `make build-all`)

**Thin slash command: `/sudd:auto`**
- Bridge command that tells the CLI agent to run `sudd auto` in the terminal
- NOT an orchestrator — just launches the Go binary

**Queue logic:**
- Priority 1: Resume `state.json.active_change` if in progress
- Priority 2: All `changes/active/*/proposal.md` with status `proposed`, sorted oldest-first
- Priority 3: `vision.md` if non-empty (green mode, runs last)
- Queue built once at session start, persisted to state.json for crash recovery

**Session budgets:**
- `auto.max_hours`: wall-clock time limit (default: 8)
- `auto.max_changes`: maximum changes to process (default: 5)
- `auto.per_change_timeout_hours`: kill a runaway change (default: 4)
- `auto.stop_on_stuck`: stop session when any change goes STUCK (default: false)
- Budgets enforced between changes only — never aborts mid-change

**Morning report**: `sudd/auto-reports/{date}.md`
```markdown
# Auto Report — 2026-03-31

Session: 23:00 → 06:47 (7h 47m)
CLI: claude-code
Changes: 3 queued, 2 done, 1 stuck

## Changes Processed
| # | Change | Outcome | Time | Tasks |
|---|--------|---------|------|-------|
| 1 | brown_doc-alignment_01 | DONE | 1h 12m | 4/4 |
| 2 | brown_gate-pb-integration_01 | DONE | 3h 45m | 8/8 |
| 3 | green_signup-feature_01 | STUCK (retry 8) | 2h 50m | 3/6 |

## Remaining Queue
- (empty)

## Action Items
- green_signup-feature_01: STUCK on T4 (auth middleware). See archive.

## Logs
- Full session logs: sudd/auto-reports/2026-03-31/
```

**State management:**
- New field `auto_session` in state.json (object or null)
- Persisted after each change completes — crash recovery point
- On restart, `sudd auto` detects existing session, resumes from queue

**sudd.yaml additions:**
```yaml
auto:
  max_hours: 8
  max_changes: 5
  per_change_timeout_hours: 4
  stop_on_stuck: false
  priority_order: "oldest_first"
  vision_last: true
  cli_override: ""          # empty = auto-detect from tiers
  cli_flags: "--max-turns 200"
```

### NOT Included
- Parallel change execution (sequential only — shared codebase)
- External notifications (Slack/email) — future enhancement
- Dollar-based cost tracking (use time budgets; token counting not yet in state.json)
- Remote trigger / cron scheduling — future enhancement
- Change dependency ordering

## Design Decisions

### D1: Go binary, not markdown instructions
The queue scheduler is a process management problem, not an LLM problem. Building a queue from filesystem state, launching subprocesses, reading JSON outcomes, enforcing time limits, writing a report — none of this needs an LLM. A Go binary does it deterministically, costs $0, and survives context window boundaries.

### D2: Each change gets a fresh CLI session
The Go binary launches a new CLI agent subprocess per change. Each gets a clean context window. No accumulation across changes. If one change fills the context and checkpoints, the next change starts fresh.

### D3: Auto-detect CLI agent
Read `sudd.yaml → tiers.mid.cli` to determine which CLI tool to use. Map: `claude-code` → `claude`, `opencode` → `opencode`. Override with `auto.cli_override` if needed. This means the same binary works with any SUDD-compatible CLI agent.

### D4: Sequential, not parallel
Changes modify the same codebase. Each change commits and merges to main before the next starts. Parallel execution creates merge conflicts.

### D5: Time-based budgets only (v1)
Dollar-based cost tracking requires token counting in state.json, which doesn't exist yet. Wall-clock time is reliable, simple, and sufficient. Per-change timeout (default 4h) prevents one runaway change from eating the entire session.

### D6: Per-change timeout via context.WithTimeout
The Go binary wraps each subprocess in a context with a timeout. If the CLI agent session exceeds `per_change_timeout_hours`, the subprocess is killed, the change is recorded as STUCK (timeout), and the loop continues. This catches infinite retry loops that the in-process budget system might miss.

### D7: Signal handling for graceful shutdown
SIGINT/SIGTERM (Ctrl+C): on first signal, wait for current change to finish, then stop and write report. On second signal, kill subprocess immediately, write partial report, exit. The developer always gets a report.

### D8: Crash-resumable via state.json
`auto_session` field in state.json persists the queue and progress. If power fails or the machine reboots, `sudd auto` on restart detects the existing session and resumes from the current position.

### D9: Single binary, zero dependencies
`make build-all` already cross-compiles sudd-go for darwin/linux/windows. The `sudd auto` command ships in the same binary. Install on a CI server, a cloud VM, or a teammate's machine — no runtime dependencies.

## Success Criteria
- [ ] `sudd auto` processes 3+ proposals in sequence without human intervention
- [ ] Each change runs in a fresh CLI agent session (separate subprocess)
- [ ] After each change: committed, merged, archived (DONE or STUCK)
- [ ] Morning report exists at `sudd/auto-reports/{date}.md`
- [ ] Time ceiling stops session gracefully
- [ ] Per-change timeout kills runaway changes
- [ ] Crash recovery: kill mid-session, restart `sudd auto`, resumes correctly
- [ ] Signal handling: Ctrl+C waits for current change, writes report
- [ ] Cross-compiles and runs on darwin/linux/windows
- [ ] Existing `/sudd:run` behavior unchanged
- [ ] Works with both claude-code and opencode CLI agents

## Dependencies
- sudd-go/ existing infrastructure (Cobra, YAML, cross-compilation)
- A SUDD-compatible CLI agent installed (claude-code or opencode)

## Files Created
- `sudd-go/cmd/sudd/night.go` — Cobra subcommand entry point
- `sudd-go/internal/night/queue.go` — queue building from filesystem
- `sudd-go/internal/night/runner.go` — subprocess launch + monitoring
- `sudd-go/internal/night/report.go` — morning report generation
- `sudd-go/internal/night/state.go` — auto_session state management
- `sudd-go/internal/night/config.go` — auto config from sudd.yaml
- `sudd-go/internal/night/*_test.go` — unit tests
- `sudd/commands/macro/auto.md` — thin slash command (bridge to binary)

## Files Modified
- `sudd-go/cmd/sudd/main.go` — register nightCmd
- `sudd/sudd.yaml` — add `auto:` section
- `sudd/state.json` — add `auto_session` field
- `sudd/sync.sh`, `sudd/sync.bat` — sync auto.md

## Risk
- **CLI agent API changes**: `claude -p "prompt"` flag could change between versions. Mitigation: make the command template configurable in `auto.cli_flags`.
- **Subprocess output capture**: Different CLI agents may format stdout/stderr differently. Mitigation: don't parse CLI output — read state.json and archive/ for outcomes.
- **Per-change timeout kills a change that was about to pass gate**: Mitigation: generous default (4h). If a change needs more, adjust `per_change_timeout_hours` in sudd.yaml.

## Reference
- sudd-go CLI: `sudd-go/cmd/sudd/main.go`
- Existing subcommands: `init`, `status`, `update`, `setup`
- Cross-compilation: `sudd-go/Makefile` → `make build-all`
- Current run.md: `sudd/commands/macro/run.md`
