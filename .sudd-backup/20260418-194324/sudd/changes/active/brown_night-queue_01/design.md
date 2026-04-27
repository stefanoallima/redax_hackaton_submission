# Design: brown_night-queue_01

## Metadata
sudd_version: 3.3

## Architecture Overview

```
User runs: sudd auto
═════════════════════

sudd-go binary (Go, no LLM, $0 cost)
  │
  ├─ PHASE 1: INIT + QUEUE
  │    Read sudd.yaml → auto config
  │    Read state.json → crash recovery check
  │    Detect CLI agent (claude / opencode)
  │    Scan changes/active/ → build queue
  │    Persist auto_session to state.json
  │
  ├─ PHASE 2: PROCESS LOOP
  │    FOR each queued change:
  │    │
  │    │  ┌─────────────────────────────────┐
  │    │  │ Check: time limit? change limit? │
  │    │  │ If exceeded → BREAK to Phase 3  │
  │    │  └──────────────┬──────────────────┘
  │    │                 │
  │    │  ┌──────────────▼──────────────────┐
  │    │  │ Launch subprocess:              │
  │    │  │   claude -p "/sudd:run brown X" │
  │    │  │                                 │
  │    │  │ Fresh context window            │
  │    │  │ Stdout → terminal + log file    │
  │    │  │ Timeout: per_change_timeout     │
  │    │  │                                 │
  │    │  │ CLI agent follows run.md:       │
  │    │  │   plan → apply → test →         │
  │    │  │   gate → done → archive         │
  │    │  └──────────────┬──────────────────┘
  │    │                 │
  │    │  ┌──────────────▼──────────────────┐
  │    │  │ Subprocess exited               │
  │    │  │ Read outcome from filesystem:   │
  │    │  │   archive/{id}_DONE → DONE      │
  │    │  │   archive/{id}_STUCK → STUCK    │
  │    │  │ Update auto_session in state    │
  │    │  │ Clean git state for next change │
  │    │  └──────────────┬──────────────────┘
  │    │                 │
  │    │  If STUCK and stop_on_stuck → BREAK
  │    │  Else → next change
  │    │
  │
  ├─ PHASE 3: MORNING REPORT
  │    Write sudd/auto-reports/{date}/summary.md
  │    Clear auto_session from state.json
  │    Print terminal summary
  │
  └─ EXIT
```

## Go Package Structure

```
sudd-go/
├── cmd/sudd/
│   ├── main.go           MODIFY — register autoCmd
│   └── auto.go           CREATE — Cobra subcommand, orchestrates phases
│
├── internal/auto/
│   ├── config.go          CREATE — parse auto section from sudd.yaml
│   ├── config_test.go     CREATE
│   ├── queue.go           CREATE — scan filesystem, build ordered queue
│   ├── queue_test.go      CREATE
│   ├── state.go           CREATE — read/write auto_session in state.json
│   ├── state_test.go      CREATE
│   ├── runner.go          CREATE — launch + monitor CLI subprocess
│   ├── runner_test.go     CREATE
│   ├── report.go          CREATE — generate morning report markdown
│   └── report_test.go     CREATE
```

## Component: config.go

### Responsibility
Parse the `auto:` section from sudd.yaml. Detect CLI agent binary.

### Types

```go
type AutoConfig struct {
    MaxHours              float64 `yaml:"max_hours"`
    MaxChanges            int     `yaml:"max_changes"`
    PerChangeTimeoutHours float64 `yaml:"per_change_timeout_hours"`
    StopOnStuck           bool    `yaml:"stop_on_stuck"`
    PriorityOrder         string  `yaml:"priority_order"`
    VisionLast            bool    `yaml:"vision_last"`
    CLIOverride           string  `yaml:"cli_override"`
    CLIFlags              string  `yaml:"cli_flags"`
}

func DefaultAutoConfig() AutoConfig {
    return AutoConfig{
        MaxHours:              8,
        MaxChanges:            5,
        PerChangeTimeoutHours: 4,
        StopOnStuck:           false,
        PriorityOrder:         "oldest_first",
        VisionLast:            true,
        CLIOverride:           "",
        CLIFlags:              "--max-turns 200",
    }
}
```

### CLI Detection Logic

```go
func DetectCLI(config AutoConfig, suddYaml map[string]interface{}) (string, error) {
    // 1. cli_override takes precedence
    if config.CLIOverride != "" {
        return verifyBinary(config.CLIOverride)
    }

    // 2. Read tiers.mid.cli from sudd.yaml
    cliName := extractTierCLI(suddYaml, "mid")

    // 3. Map to binary name
    switch cliName {
    case "claude-code":
        return verifyBinary("claude")
    case "opencode":
        return verifyBinary("opencode")
    default:
        return verifyBinary(cliName) // try as-is
    }
}

func verifyBinary(name string) (string, error) {
    path, err := exec.LookPath(name)
    if err != nil {
        return "", fmt.Errorf("CLI '%s' not found on PATH", name)
    }
    return path, nil
}
```

## Component: queue.go

### Responsibility
Scan `changes/active/` and build an ordered queue of changes to process.

### Types

```go
type QueueEntry struct {
    ID     string `json:"id"`
    Mode   string `json:"mode"`    // "brown" or "green"
    Source string `json:"source"`  // "resume", "proposal", "vision"
}
```

### Logic

```go
func BuildQueue(projectDir string, config AutoConfig, state *State) ([]QueueEntry, error) {
    var queue []QueueEntry

    // Priority 1: active in-progress change
    if state.ActiveChange != "" && state.Phase != "complete" {
        queue = append(queue, QueueEntry{
            ID: state.ActiveChange, Mode: "brown", Source: "resume",
        })
    }

    // Priority 2: proposed changes
    proposals := scanProposals(projectDir, state.ActiveChange)
    sortProposals(proposals, config.PriorityOrder) // oldest_first or newest_first
    for _, p := range proposals {
        queue = append(queue, QueueEntry{
            ID: p.ID, Mode: "brown", Source: "proposal",
        })
    }

    // Priority 3: vision.md
    if config.VisionLast && hasNonEmptyVision(projectDir) {
        queue = append(queue, QueueEntry{
            ID: "green:vision", Mode: "green", Source: "vision",
        })
    }

    return queue, nil
}

func scanProposals(projectDir, excludeID string) []Proposal {
    // Scan changes/active/*/proposal.md
    // Parse: read file, find "## Status" section, check next line == "proposed"
    // Exclude excludeID (already in queue as resume)
    // Return with modification time for sorting
}
```

## Component: state.go

### Responsibility
Read and write `auto_session` in state.json. Handle crash recovery detection.

### Types

```go
type AutoSession struct {
    StartedAt         string          `json:"started_at"`
    StopReason        string          `json:"stop_reason"` // "", "queue_empty", "time_limit", etc.
    ChangesProcessed  []ChangeResult  `json:"changes_processed"`
    QueueRemaining    []QueueEntry    `json:"queue_remaining"`
}

type ChangeResult struct {
    ChangeID       string  `json:"change_id"`
    Outcome        string  `json:"outcome"`         // "DONE", "STUCK", "UNKNOWN", "TIMEOUT"
    ElapsedSeconds float64 `json:"elapsed_seconds"`
    TasksCompleted int     `json:"tasks_completed"`
    TasksTotal     int     `json:"tasks_total"`
    ExitCode       int     `json:"exit_code"`
}

type State struct {
    Version       string       `json:"version"`
    Mode          string       `json:"mode"`
    ActiveChange  string       `json:"active_change"`
    Phase         string       `json:"phase"`
    RetryCount    int          `json:"retry_count"`
    TestsPassed   bool         `json:"tests_passed"`
    GateScore     *int         `json:"gate_score"`
    GatePassed    bool         `json:"gate_passed"`
    Stats         Stats        `json:"stats"`
    AutoSession   *AutoSession `json:"auto_session"`
    // ... other fields preserved as raw JSON
}
```

### Crash Recovery

```go
func (s *State) HasActiveAutoSession() bool {
    return s.AutoSession != nil && len(s.AutoSession.QueueRemaining) > 0
}

func (s *State) ClearChangeState() {
    s.ActiveChange = ""
    s.Phase = "inception"
    s.RetryCount = 0
    s.TestsPassed = false
    s.GateScore = nil
    s.GatePassed = false
}
```

## Component: runner.go

### Responsibility
Launch CLI agent as subprocess, monitor it, detect outcome.

### Public API

```go
func RunChange(ctx context.Context, entry QueueEntry, cfg RunConfig) ChangeResult
```

### RunConfig

```go
type RunConfig struct {
    CLIBinary   string        // "claude" or "opencode"
    CLIFlags    string        // "--max-turns 200"
    ProjectDir  string        // working directory
    LogDir      string        // where to write per-change log
    Timeout     time.Duration // per-change timeout
}
```

### Subprocess Launch

```go
func RunChange(ctx context.Context, entry QueueEntry, cfg RunConfig) ChangeResult {
    start := time.Now()

    // Build prompt
    var prompt string
    switch {
    case entry.Source == "resume":
        prompt = "/sudd:run"
    case entry.Mode == "green":
        prompt = "/sudd:run green"
    default:
        prompt = fmt.Sprintf("/sudd:run brown %s", entry.ID)
    }

    // Build command
    args := []string{"-p", prompt}
    if cfg.CLIFlags != "" {
        args = append(args, strings.Fields(cfg.CLIFlags)...)
    }

    // Create timeout context
    changeCtx, cancel := context.WithTimeout(ctx, cfg.Timeout)
    defer cancel()

    cmd := exec.CommandContext(changeCtx, cfg.CLIBinary, args...)
    cmd.Dir = cfg.ProjectDir

    // Pipe output to terminal + log file
    logFile := openLogFile(cfg.LogDir, entry.ID)
    defer logFile.Close()
    cmd.Stdout = io.MultiWriter(os.Stdout, logFile)
    cmd.Stderr = io.MultiWriter(os.Stderr, logFile)

    // Run
    err := cmd.Run()
    elapsed := time.Since(start)

    // Determine outcome
    result := ChangeResult{
        ChangeID:       entry.ID,
        ElapsedSeconds: elapsed.Seconds(),
    }

    if changeCtx.Err() == context.DeadlineExceeded {
        result.Outcome = "TIMEOUT"
        result.ExitCode = -1
    } else if err != nil {
        result.Outcome = "UNKNOWN"
        if exitErr, ok := err.(*exec.ExitError); ok {
            result.ExitCode = exitErr.ExitCode()
        }
    }

    // Read filesystem for definitive outcome
    outcome, tasks := detectOutcome(cfg.ProjectDir, entry)
    if outcome != "" {
        result.Outcome = outcome
    }
    result.TasksCompleted = tasks.Completed
    result.TasksTotal = tasks.Total

    return result
}
```

### Outcome Detection

```go
func detectOutcome(projectDir string, entry QueueEntry) (string, TaskCount) {
    changeID := entry.ID

    // For green mode, read state.json to find generated ID
    if entry.Mode == "green" {
        state := readState(projectDir)
        if state.ActiveChange != "" {
            changeID = state.ActiveChange
        }
    }

    archiveDir := filepath.Join(projectDir, "sudd", "changes", "archive")

    if dirExists(filepath.Join(archiveDir, changeID+"_DONE")) {
        return "DONE", countTasks(projectDir, changeID)
    }
    if dirExists(filepath.Join(archiveDir, changeID+"_STUCK")) {
        return "STUCK", countTasks(projectDir, changeID)
    }
    return "", TaskCount{}
}
```

## Component: report.go

### Responsibility
Generate morning report markdown from session state.

### Logic

```go
func WriteReport(session *AutoSession, projectDir string, cliBinary string) error {
    date := time.Now().Format("2006-01-02")
    reportDir := filepath.Join(projectDir, "sudd", "auto-reports", date)
    os.MkdirAll(reportDir, 0755)

    // Build markdown
    var buf bytes.Buffer
    fmt.Fprintf(&buf, "# Auto Report — %s\n\n", date)

    startTime, _ := time.Parse(time.RFC3339, session.StartedAt)
    elapsed := time.Since(startTime)
    fmt.Fprintf(&buf, "Session: %s → %s (%s)\n",
        startTime.Format("15:04"), time.Now().Format("15:04"),
        formatDuration(elapsed))
    fmt.Fprintf(&buf, "CLI: %s\n", cliBinary)
    fmt.Fprintf(&buf, "Stop reason: %s\n\n", session.StopReason)

    // Per-change table
    fmt.Fprintln(&buf, "## Changes Processed")
    fmt.Fprintln(&buf, "| # | Change | Outcome | Time | Tasks |")
    fmt.Fprintln(&buf, "|---|--------|---------|------|-------|")
    for i, c := range session.ChangesProcessed {
        fmt.Fprintf(&buf, "| %d | %s | %s | %s | %d/%d |\n",
            i+1, c.ChangeID, c.Outcome,
            formatDuration(time.Duration(c.ElapsedSeconds)*time.Second),
            c.TasksCompleted, c.TasksTotal)
    }

    // Remaining queue
    if len(session.QueueRemaining) > 0 {
        fmt.Fprintln(&buf, "\n## Remaining Queue")
        for _, q := range session.QueueRemaining {
            fmt.Fprintf(&buf, "- %s (%s)\n", q.ID, q.Source)
        }
    }

    // Action items from STUCK changes
    stuckItems := collectStuckReasons(projectDir, session.ChangesProcessed)
    if len(stuckItems) > 0 {
        fmt.Fprintln(&buf, "\n## Action Items")
        for _, item := range stuckItems {
            fmt.Fprintf(&buf, "- %s: %s\n", item.ChangeID, item.Reason)
        }
    }

    // Write
    reportPath := filepath.Join(reportDir, "summary.md")
    return os.WriteFile(reportPath, buf.Bytes(), 0644)
}
```

## Component: auto.go (Cobra Command)

### Responsibility
Wire everything together. Entry point for `sudd auto`.

### Logic

```go
var autoCmd = &cobra.Command{
    Use:   "auto [target]",
    Short: "Fully autonomous mode — process all queued changes",
    Long:  `Launches separate CLI agent sessions for each proposed change.
Each change gets a fresh context window. Stops on time limit,
change limit, or empty queue. Writes a morning report.`,
    Args: cobra.MaximumNArgs(1),
    Run:  runAuto,
}

func runAuto(cmd *cobra.Command, args []string) {
    projectDir := resolveTarget(args)

    // 1. Load config
    autoConfig := night.LoadConfig(projectDir)
    suddYaml := loadSuddYaml(projectDir)

    // 2. Detect CLI
    cliBinary, err := night.DetectCLI(autoConfig, suddYaml)
    handleErr(err)

    // 3. Load or resume state
    state := night.LoadState(projectDir)

    var session *night.AutoSession
    if state.HasActiveAutoSession() {
        session = state.AutoSession
        fmt.Printf("Resuming auto session from %s. %d changes remaining.\n",
            session.StartedAt, len(session.QueueRemaining))
    } else {
        queue, err := night.BuildQueue(projectDir, autoConfig, state)
        handleErr(err)
        if len(queue) == 0 {
            night.WriteReport(&night.AutoSession{
                StartedAt: time.Now().Format(time.RFC3339),
                StopReason: "queue_empty",
            }, projectDir, cliBinary)
            fmt.Println("No changes to process.")
            return
        }
        session = &night.AutoSession{
            StartedAt:      time.Now().Format(time.RFC3339),
            QueueRemaining: queue,
        }
        state.AutoSession = session
        night.SaveState(projectDir, state)
    }

    // 4. Banner
    fmt.Println("═══════════════════════════════════════")
    fmt.Println("  SUDD FULLY AUTONOMOUS MODE")
    fmt.Println("═══════════════════════════════════════")
    fmt.Printf("  CLI:     %s\n", cliBinary)
    fmt.Printf("  Queue:   %d changes\n", len(session.QueueRemaining))
    fmt.Printf("  Budget:  %gh / %d changes max\n",
        autoConfig.MaxHours, autoConfig.MaxChanges)
    fmt.Println("═══════════════════════════════════════")

    // 5. Signal handling
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()

    // 6. Process loop
    startTime, _ := time.Parse(time.RFC3339, session.StartedAt)

    for len(session.QueueRemaining) > 0 {
        // Budget checks
        elapsed := time.Since(startTime)
        if elapsed.Hours() >= autoConfig.MaxHours {
            session.StopReason = "time_limit"
            break
        }
        if len(session.ChangesProcessed) >= autoConfig.MaxChanges {
            session.StopReason = "change_limit"
            break
        }
        // Signal check
        if ctx.Err() != nil {
            session.StopReason = "signal"
            break
        }

        entry := session.QueueRemaining[0]
        fmt.Printf("\n▶ Starting change: %s (%s)\n", entry.ID, entry.Mode)

        // Run
        result := night.RunChange(ctx, entry, night.RunConfig{
            CLIBinary:  cliBinary,
            CLIFlags:   autoConfig.CLIFlags,
            ProjectDir: projectDir,
            LogDir:     filepath.Join(projectDir, "sudd", "auto-reports", time.Now().Format("2006-01-02")),
            Timeout:    time.Duration(autoConfig.PerChangeTimeoutHours * float64(time.Hour)),
        })

        fmt.Printf("  ✓ %s: %s (%s)\n", entry.ID, result.Outcome,
            formatDuration(time.Duration(result.ElapsedSeconds)*time.Second))

        // Update session
        session.ChangesProcessed = append(session.ChangesProcessed, result)
        session.QueueRemaining = session.QueueRemaining[1:]
        state.AutoSession = session
        night.SaveState(projectDir, state) // crash recovery point

        // Clean state for next change
        state = night.LoadState(projectDir) // re-read (run.md may have changed it)
        state.ClearChangeState()
        state.AutoSession = session
        night.SaveState(projectDir, state)

        // Git clean check
        night.EnsureGitClean(projectDir, entry.ID)

        // Stop on stuck?
        if result.Outcome == "STUCK" && autoConfig.StopOnStuck {
            session.StopReason = "stuck_stop"
            break
        }
    }

    if session.StopReason == "" {
        session.StopReason = "queue_empty"
    }

    // 7. Report
    night.WriteReport(session, projectDir, cliBinary)
    state.AutoSession = nil
    night.SaveState(projectDir, state)

    // 8. Summary
    done := countOutcome(session, "DONE")
    stuck := countOutcome(session, "STUCK")
    fmt.Println("\n═══════════════════════════════════════")
    fmt.Println("  SUDD AUTO SESSION COMPLETE")
    fmt.Println("═══════════════════════════════════════")
    fmt.Printf("  Changes: %d/%d done, %d stuck\n",
        done, len(session.ChangesProcessed), stuck)
    fmt.Printf("  Time:    %s\n", formatDuration(time.Since(startTime)))
    fmt.Printf("  Report:  sudd/auto-reports/%s/summary.md\n",
        time.Now().Format("2006-01-02"))
    fmt.Println("═══════════════════════════════════════")
}
```

## Component: sudd.yaml (Updated)

### New Section

```yaml
auto:
  max_hours: 8
  max_changes: 5
  per_change_timeout_hours: 4
  stop_on_stuck: false
  priority_order: "oldest_first"
  vision_last: true
  cli_override: ""
  cli_flags: "--max-turns 200"
```

## Component: state.json (Updated)

### New Field

```json
{
  "auto_session": null
}
```

When active:
```json
{
  "auto_session": {
    "started_at": "2026-03-31T23:00:00Z",
    "stop_reason": "",
    "changes_processed": [],
    "queue_remaining": [
      {"id": "brown_doc-alignment_01", "mode": "brown", "source": "proposal"},
      {"id": "green:vision", "mode": "green", "source": "vision"}
    ]
  }
}
```

## Component: auto.md (Thin Slash Command)

```markdown
---
name: sudd:auto
description: Fully autonomous mode — process all queued changes
phase: all
macro: true
---

Fully autonomous mode. Processes all proposed changes in sequence,
each in a fresh CLI session.

## HOW TO RUN

Run in your terminal (not as a slash command):

    sudd auto

Or with a target project:

    sudd auto /path/to/project

The `sudd` binary manages the queue and launches separate CLI sessions
per change. Each change gets a fresh context window.

## CONFIGURATION

Set in sudd.yaml under `auto:`:

    auto:
      max_hours: 8              # session time limit
      max_changes: 5            # max changes per session
      per_change_timeout_hours: 4  # kill runaway changes
      stop_on_stuck: false      # continue after STUCK changes

## WHAT IT DOES

1. Scans changes/active/ for proposals with status: proposed
2. Launches `claude -p "/sudd:run brown {id}"` per change
3. Waits for completion, reads outcome from archive/
4. Writes morning report to sudd/auto-reports/{date}/summary.md
```

## Data Flow

```
sudd auto
  │
  ├── Read sudd/sudd.yaml → auto config
  ├── Read sudd/state.json → crash recovery check
  ├── Detect CLI binary (claude / opencode)
  ├── Scan changes/active/*/proposal.md → build queue
  ├── Persist auto_session to state.json
  │
  ├── LOOP: for each queued change
  │     │
  │     ├── Budget check (time, count)
  │     ├── Launch: claude -p "/sudd:run brown {id}"   ← SUBPROCESS
  │     │     └── CLI agent follows run.md (unmodified)
  │     │         └── plan → apply → test → gate → done
  │     ├── Wait for subprocess exit
  │     ├── Read outcome from archive/
  │     ├── Update auto_session in state.json  ← CRASH RECOVERY POINT
  │     ├── Clean state + git for next change
  │     └── Check stop_on_stuck
  │
  ├── Write sudd/auto-reports/{date}/summary.md
  ├── Clear auto_session from state.json
  └── Print terminal summary
```

## File Changes

### New Files (sudd-go/)
- `cmd/sudd/auto.go` — Cobra subcommand
- `internal/auto/config.go` + test
- `internal/auto/queue.go` + test
- `internal/auto/state.go` + test
- `internal/auto/runner.go` + test
- `internal/auto/report.go` + test

### New Files (sudd/)
- `sudd/commands/macro/auto.md` — thin slash command

### Modified Files
- `sudd-go/cmd/sudd/main.go` — register autoCmd
- `sudd/sudd.yaml` — add `auto:` section
- `sudd/state.json` — add `auto_session: null`
- `sudd/sync.sh`, `sudd/sync.bat` — sync auto.md

### Unchanged Files
- `sudd/commands/macro/run.md` — NOT modified
- All micro commands, all agent files — NOT modified
