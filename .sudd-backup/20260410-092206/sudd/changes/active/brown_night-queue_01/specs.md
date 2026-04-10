# Specifications: brown_night-queue_01

## Functional Requirements

### FR-1: `sudd auto` Command
- Given: sudd-go binary is built and installed
- When: User runs `sudd auto` (or `sudd auto --target /path/to/project`)
- Then:
  - Read sudd.yaml for auto config
  - Build or resume a queue of changes
  - Launch a separate CLI agent subprocess per change
  - After each change completes, pick up the next
  - After all changes processed (or budget hit), write report and exit

### FR-2: Queue Building
- Given: `sudd auto` starting (no existing auto_session)
- When: Queue is built
- Then:
  - Priority 1: Resume `state.json.active_change` if exists and phase != "complete"
  - Priority 2: Scan `changes/active/*/proposal.md` — include entries where the line after `## Status` reads `proposed`. Exclude the active_change (already in Priority 1). Sort by file modification time per `auto.priority_order` (default: oldest_first).
  - Priority 3: If `auto.vision_last` is true (default) AND `vision.md` exists AND is non-empty → append one green-mode entry at end of queue
  - Queue is built ONCE (no mid-session re-scan)
  - Queue is persisted immediately to `state.json.auto_session.queue_remaining`
  - If queue is empty: write empty report ("No changes to process"), exit 0

### FR-3: CLI Agent Detection
- Given: sudd.yaml tiers configuration
- When: Determining which CLI to launch
- Then:
  - If `auto.cli_override` is non-empty → use that value as the binary name
  - Else read `sudd.yaml → tiers.mid.cli` → map: `claude-code` → `claude`, `opencode` → `opencode`
  - Verify binary exists on PATH (`which` / `where`)
  - If not found: error "CLI agent '{name}' not found on PATH. Install it or set auto.cli_override."

### FR-4: Per-Change Subprocess Launch
- Given: A change is dequeued
- When: Go binary dispatches it
- Then:
  - Build command based on mode:
    - Brown (proposed): `{cli} -p "/sudd:run brown {change-id}" {cli_flags}`
    - Brown (resume): `{cli} -p "/sudd:run" {cli_flags}`
    - Green (vision): `{cli} -p "/sudd:run green" {cli_flags}`
  - Set working directory to project root
  - Launch as subprocess with:
    - stdout/stderr piped to terminal AND log file (`auto-reports/{date}/{change-id}.log`)
    - context.WithTimeout set to `auto.per_change_timeout_hours`
  - Wait for subprocess exit
  - On exit code 0: normal completion
  - On timeout: kill process, record as STUCK (timeout)
  - On any other exit: record as STUCK (error)

### FR-5: Outcome Detection
- Given: CLI agent subprocess has exited
- When: Go binary determines what happened
- Then:
  - Read `state.json` for updated fields
  - Check filesystem:
    - `changes/archive/{id}_DONE/` exists → outcome = DONE
    - `changes/archive/{id}_STUCK/` exists → outcome = STUCK
    - Neither → outcome = UNKNOWN (subprocess may have crashed before archiving)
  - For green mode: read `state.json.active_change` to discover the generated change-id (green mode generates IDs dynamically in run.md Step 2)
  - Record outcome in `auto_session.changes_processed`

### FR-6: Session Time Budget
- Given: `sudd.yaml.auto.max_hours` configured (default: 8)
- When: A change completes, before starting next
- Then:
  - Elapsed = now - auto_session.started_at
  - If elapsed >= max_hours: stop, write report
  - Budget checked BETWEEN changes only — never kills a running subprocess (per-change timeout handles that)

### FR-7: Session Change Limit
- Given: `sudd.yaml.auto.max_changes` configured (default: 5)
- When: A change completes
- Then:
  - If len(changes_processed) >= max_changes: stop, write report

### FR-8: Stop on Stuck
- Given: `auto.stop_on_stuck` configured (default: false)
- When: A change completes with outcome STUCK
- Then:
  - If stop_on_stuck == true: stop session, write report
  - If stop_on_stuck == false: continue to next change

### FR-9: State Cleanup Between Changes
- Given: A change just completed
- When: Before launching next change subprocess
- Then:
  - Verify `state.json.active_change` is null (done.md clears it)
  - If not null (abnormal exit): clear it, set phase to inception, reset retry/gate/test fields
  - Verify git status is clean
  - If dirty: `git add -A && git commit -m "chore(sudd-auto): cleanup after {change-id}"`

### FR-10: Crash Recovery
- Given: `state.json.auto_session` is non-null when `sudd auto` starts
- When: Previous session was interrupted
- Then:
  - Log: "Resuming auto session from {started_at}. {N} changes remaining."
  - Do NOT re-process entries in `changes_processed`
  - If `active_change` is set: first queued change resumes it
  - Continue with `queue_remaining`

### FR-11: Morning Report
- Given: Auto session ending (any reason)
- When: Go binary writes report
- Then:
  - Create directory `sudd/auto-reports/{YYYY-MM-DD}/` if not exists
  - Write `sudd/auto-reports/{YYYY-MM-DD}/summary.md` with:
    - Session start/end times, total elapsed
    - CLI agent used
    - Stop reason (queue_empty / time_limit / change_limit / stuck_stop / signal)
    - Per-change table: change_id, outcome, elapsed time, tasks completed/total
    - Remaining queue (changes not started)
    - Action items (for STUCK changes: read reason from archive STUCK.md)
  - Per-change log files already in `auto-reports/{date}/{change-id}.log`
  - If summary.md already exists: rename existing to summary-1.md, write new

### FR-12: Signal Handling
- Given: Process receives SIGINT or SIGTERM
- When: During the process loop
- Then:
  - First signal: set "stopping" flag. Wait for current subprocess to finish. Then write report and exit.
  - Second signal: kill current subprocess immediately. Write partial report. Exit.
  - Log: "Signal received. Finishing current change, then stopping."

### FR-13: Thin Slash Command `/sudd:auto`
- Given: User types `/sudd:auto` in a CLI agent session
- When: Command is loaded
- Then:
  - Instruct the CLI agent to run `sudd auto` via Bash tool
  - The slash command does NOT contain queue/scheduling logic
  - It is a bridge: "Run `sudd auto` in the terminal to start fully autonomous mode."

### FR-14: Cross-Platform Build
- Given: `make build-all` in sudd-go/
- When: Building the binary
- Then:
  - `sudd auto` compiles and works on darwin/amd64, darwin/arm64, linux/amd64, windows/amd64
  - No CGO dependencies
  - No runtime dependencies beyond the CLI agent binary

### FR-15: Backward Compatibility
- Given: User runs `/sudd:run` (single-change mode)
- When: No auto_session in state.json
- Then: Behavior identical to current. `auto_session` field ignored.

## Non-Functional Requirements

### NFR-1: Zero LLM Cost for Scheduling
- Constraint: The Go binary uses zero LLM tokens for queue management, budget checks, outcome detection, and report writing
- Rationale: Scheduling is deterministic logic, not AI work

### NFR-2: Fresh Context Per Change
- Constraint: Each change runs in a separate CLI agent subprocess with a fresh context window
- Rationale: Context accumulation across changes causes degradation and token waste

### NFR-3: No Modification to run.md
- Constraint: run.md is NOT modified by this change
- Rationale: The Go binary orchestrates externally; the CLI agent follows existing run.md instructions

### NFR-4: Graceful Budget Enforcement
- Constraint: Session budgets (time, count) only prevent the NEXT change from starting. Per-change timeout is the only mid-change kill mechanism.
- Rationale: Aborting mid-change leaves dirty state

### NFR-5: Report Always Written
- Constraint: Morning report is written even on signal, crash recovery, or empty queue
- Rationale: Developer needs to know what happened

### NFR-6: Single Binary Distribution
- Constraint: `sudd auto` ships in the same `sudd` binary as `sudd init`/`sudd status`
- Rationale: No additional installation steps. Same binary, new subcommand.

## Consumer Handoffs

### Handoff 1: Queue Builder → Process Loop
- Format: `[]QueueEntry{ID, Mode, Source}`
- Validation: each ID has a valid proposal.md or is "green:vision"

### Handoff 2: Process Loop → State (per change)
- Format: `auto_session.changes_processed[]` entry in state.json
- Schema: `{change_id, outcome, elapsed_seconds, tasks_completed, tasks_total, exit_code}`

### Handoff 3: State → Morning Report
- Format: Read state.json + archive/ STUCK.md files
- Output: Markdown report + per-change log files

## Out of Scope
- Parallel change execution
- Dollar-based cost tracking
- External notifications (Slack, email, webhook)
- Remote trigger / cron scheduling
- Change dependency ordering
- Mid-session queue modification
- Modifying run.md or any micro commands
