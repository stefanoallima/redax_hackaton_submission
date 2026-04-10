# Change: brown_v33-agents-md-migration_01

## Status
DONE

## Summary
Migrate target repo config from CLAUDE.md to CLI-agnostic AGENTS.md and bump all SUDD version strings from 3.2 to 3.3.

## Motivation
Two problems with the v3.2 installer:
1. **CLAUDE.md overwrites project context** — `sudd init` drops a SUDD-only CLAUDE.md into target repos, erasing any project-specific guidance. The file should describe the *project*, not SUDD.
2. **CLI lock-in** — CLAUDE.md is Claude Code-specific. Users working with OpenCode, Crush, or Gemini CLI get a file named for the wrong tool.
3. **Version drift** — the v3.3 branch bumped Go binary versions but missed all 30+ markdown/yaml version identifiers still saying 3.2.

## What Was Done

### AGENTS.md Migration
- Deleted `sudd-go/cmd/sudd/templates/CLAUDE.md`
- Created `sudd-go/cmd/sudd/templates/AGENTS.md` — minimal SUDD integration reference (not a full manual)
- Renamed `InstallCLAUDEMD()` → `InstallAGENTSMD()` in `installer.go`
- Updated all references in `main.go` (live install, embedded install, status check)
- Updated `init.md` (3 copies) — Step 7 now creates AGENTS.md, won't overwrite existing project configs
- Updated `port.md` (2 copies) — broadened to check AGENTS.md / CLAUDE.md / GEMINI.md for conventions
- Updated `monitor.md` (2 copies) — budget reference
- Updated `.opencode/command/sudd-run.md` — reads AGENTS.md first
- Updated `sudd-go/README.md` — tree diagram
- Added AGENTS.md detection to `DetectContext()`

### Version Bump to 3.3
Top-level version identifiers updated:
- `sudd/standards.md` — header + state schema example
- `sudd/state.schema.json` — default value
- `sudd/commands/micro/plan.md` — design template
- `sudd/sudd.yaml` — file header

Feature "introduced in" annotations (e.g., `v3.2 — Process Dispatch`) kept as-is — they mark when features were first added.

### Target Repo Fix (persona-browser-agent)
- Ran `sudd init` with new binary — installed AGENTS.md + updated 53 sudd files + generated 12 skills
- Removed old SUDD-only CLAUDE.md

### Merge
- Branch `feat/sudd-v3.3-universal-installer` (11 commits) merged to master via `--no-ff`

## Verification
- Go binary compiles clean
- All tests pass (`cmd/sudd`, `internal/installer`)
- `sudd init` successfully installs to persona-browser-agent target repo
- `.sudd-version` shows `3.3.0` with correct git hash

## Files Changed (this session)
18 files in commit `c7f2452`:
- `CLAUDE.md` (repo's own)
- `sudd-go/cmd/sudd/main.go`
- `sudd-go/cmd/sudd/templates/AGENTS.md` (new)
- `sudd-go/cmd/sudd/templates/CLAUDE.md` (deleted)
- `sudd-go/internal/installer/installer.go`
- `sudd-go/README.md`
- `sudd-go/.opencode/command/sudd-run.md`
- `sudd-go/cmd/sudd/templates/.claude/commands/sudd/init.md`
- `sudd-go/cmd/sudd/templates/sudd/agents/monitor.md`
- `sudd-go/cmd/sudd/templates/sudd/commands/macro/port.md`
- `sudd-go/cmd/sudd/templates/sudd/commands/micro/init.md`
- `sudd/agents/monitor.md`
- `sudd/commands/macro/port.md`
- `sudd/commands/micro/init.md`
- `sudd/commands/micro/plan.md`
- `sudd/standards.md`
- `sudd/state.schema.json`
- `sudd/sudd.yaml`

---

# Next Steps for SUDD v3.3

## Immediate (before using on new projects)

1. **Update other target repos** — any project besides persona-browser-agent that has SUDD installed still runs v3.2 with the old CLAUDE.md. Run:
   ```
   sudd update <path>
   ```
   Then manually remove the old SUDD-only CLAUDE.md if present.

2. **Add `sudd.exe` to PATH** — currently lives at `sudd-go/bin/sudd.exe`. Either:
   - Run `go install ./cmd/sudd/` to put it in `$GOPATH/bin`
   - Or manually copy to a directory on PATH

## Short-term

3. **Cross-compilation** — `bin/sudd.exe` is Windows-only. For Mac/Linux:
   ```
   cd sudd-go
   GOOS=darwin GOARCH=arm64 go build -o bin/sudd-darwin-arm64 ./cmd/sudd/
   GOOS=linux GOARCH=amd64 go build -o bin/sudd-linux-amd64 ./cmd/sudd/
   ```
   Or use `make build-all` once `make` is available.

4. **Installer auto-cleanup of old CLAUDE.md** — currently the installer creates AGENTS.md but doesn't remove old SUDD-only CLAUDE.md files. Could add detection: if CLAUDE.md exists and contains `<!-- SUDD` markers or starts with `# SUDD —`, offer to remove it.

## Medium-term

5. **Distribution pipeline** — GitHub releases with pre-built binaries so other machines don't need Go installed.

6. **`sudd doctor`** — a diagnostic command that checks:
   - Version alignment (installed vs binary)
   - Missing agents/commands
   - Stale state.json
   - Orphaned active changes

7. **Template versioning** — embedded templates in the binary are frozen at build time. If using live source mode, this doesn't matter. But for embedded mode, the binary must be rebuilt after any sudd/ change.
