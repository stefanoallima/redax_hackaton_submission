# Tasks: brown_night-queue_01

## Implementation Tasks

- [x] T1: Add auto config to sudd.yaml + auto_session to state.json
  - Files: sudd/sudd.yaml, sudd/state.json
  - SharedFiles: sudd/sudd.yaml, sudd/state.json
  - Effort: S
  - Dependencies: none
  - Completed: 2026-03-31

- [x] T2: Implement config parser (internal/auto/config.go)
  - Files: sudd-go/internal/auto/config.go, sudd-go/internal/auto/config_test.go
  - SharedFiles: none
  - Effort: S
  - Dependencies: none
  - Completed: 2026-03-31
  - Tests: 6 pass

- [x] T3: Implement queue builder (internal/auto/queue.go)
  - Files: sudd-go/internal/auto/queue.go, sudd-go/internal/auto/queue_test.go
  - SharedFiles: none
  - Effort: M
  - Dependencies: none
  - Completed: 2026-03-31
  - Tests: 9 pass

- [x] T4: Implement state manager (internal/auto/state.go)
  - Files: sudd-go/internal/auto/state.go, sudd-go/internal/auto/state_test.go
  - SharedFiles: none
  - Effort: M
  - Dependencies: none
  - Completed: 2026-03-31
  - Tests: 8 pass

- [x] T5: Implement CLI runner (internal/auto/runner.go)
  - Files: sudd-go/internal/auto/runner.go, sudd-go/internal/auto/runner_test.go
  - SharedFiles: none
  - Effort: L
  - Dependencies: T2
  - Completed: 2026-03-31
  - Tests: 13 pass

- [x] T6: Implement morning report (internal/auto/report.go)
  - Files: sudd-go/internal/auto/report.go, sudd-go/internal/auto/report_test.go
  - SharedFiles: none
  - Effort: M
  - Dependencies: none
  - Completed: 2026-03-31
  - Tests: 10 pass

- [x] T7: Wire autoCmd in main.go + auto.go orchestrator
  - Files: sudd-go/cmd/sudd/main.go, sudd-go/cmd/sudd/auto.go
  - SharedFiles: sudd-go/cmd/sudd/main.go
  - Effort: L
  - Dependencies: T2, T3, T4, T5, T6
  - Completed: 2026-03-31

- [x] T8: Create thin auto.md slash command + sync
  - Files: sudd/commands/macro/auto.md, sudd/sync.sh
  - SharedFiles: sudd/sync.sh
  - Effort: S
  - Dependencies: T7
  - Completed: 2026-03-31

---
Total: 8/8 tasks complete | 46 tests passing
Build: go build OK | go vet OK | cross-platform (darwin/linux/windows)
