# PostureBot

Free, MIT, single-file Python terminal app by Megan "Meg" Schmidt (Kitschy Lemon). A tiny 8-bit bot sits in a side pane, bobs, and speaks a posture reminder every N minutes. Not a Godot project: pure stdlib Python 3, no dependencies. macOS tested; Linux untested (needs espeak-ng/espeak/spd-say); Windows support added in 0.1.3 but UNTESTED on a real Windows machine (msvcrt keys/lock, ANSI via SetConsoleMode, SAPI speech through PowerShell -EncodedCommand).

## Layout

- `posture_bot.py`: the whole app (4-space indent, stdlib only).
- `pyproject.toml`: PyPI packaging; `posturebot` console script -> `posture_bot:main`.
- `README.md`, `LICENSE` (MIT, Megan Schmidt), `assets/posturebot.png` (transparent bot, README hero).
- `dist/`, `build/`, `*.egg-info/` are gitignored build output.

## How the app works

- **Config** in `~/.posture-bot.json` (`DEFAULTS` at top): `name`, `minutes`, `voice`, `rate` (None = voice's own speed, no `-r`), `color`, `custom`. Single-instance lock at `~/.posture-bot.lock`.
- **Message**: `message(cfg)` returns the custom reminder if non-empty, else "Hey <name>, just reminding you to check your posture. Love you!". Clearing `custom` restores the default.
- **Sprite**: `sprite_grid()` builds a 14x18 RGB pixel grid (2 pixels per terminal row); `sprite()` renders it with half-blocks. The bob is half a row: legs painted first, body in front sinks 1 pixel. `PALETTES` = periwinkle + butter (legs a darker shade). Eyes: open / blink / happy (during a reminder); cheeks pulse while talking; no mouth.
- **Render**: absolute-positioned rows, auto-wrap off, alternate screen, full clear on resize (prevents scroll junk). Right-aligned panel is 18 cols wide; text wraps at `PANEL_TEXT_W = 16`. Never let a line reach the last column.
- **Keys**: q quit, n remind now, +/- interval +-1 min (min 1), m mute, b bot color, c change name, r my reminder. Editing mode (name/reminder) swallows all keys; Esc cancels, Enter saves. Loop wakes instantly on keypress via `select`.
- **Windows branch**: `IS_WIN` gates `msvcrt` (keys, lock), `setup_windows_console()`, and the PowerShell `WIN_SPEECH` script (voice substring match, else system voice). Only mock-tested from macOS.
- **Speech**: macOS `say -v <voice>` (default Kathy at her own speed, no `--rate`).

## Testing

No test suite. Verify by driving it in a pty (`pty.fork`), **always draining output continuously** or the child blocks on write. Use an isolated `HOME` (and a stub `say` on PATH) so Meg's real config and a running copy's lock are untouched. In a pty, set the window size or rows fall back to 20.

## Release flow (GitHub + Homebrew + PyPI)

1. Bump `version` in `pyproject.toml`; commit + push.
2. `git tag -a vX.Y.Z` + push tag; `gh release create vX.Y.Z --verify-tag` (wait a few seconds after pushing the tag).
3. `curl -sL .../archive/refs/tags/vX.Y.Z.tar.gz | shasum -a 256`.
4. Update `Formula/posturebot.rb` in `m3gm3g/homebrew-tap` (url + sha256); push. Formula installs `posture_bot.py` to `libexec` with a bash launcher using `formula_opt_bin("python@3.14")`; test asserts `usage: posturebot`.
5. Verify: `brew tap m3gm3g/tap && brew install m3gm3g/tap/posturebot`, `brew test`, `brew audit --strict --online`; then `brew uninstall` + `brew untap` to leave the machine clean. (Pull the local tap clone if brew uses a stale formula.)
6. `rm -rf dist build *.egg-info && pipx run build`.
7. **Meg uploads to PyPI herself**: `pipx run twine upload ~/posture-bot/dist/*` (user `__token__`). PyPI versions are immutable. Never handle or ask for her token.

## Workflow rules

- Don't commit, push, tag, or publish unless Meg asks; she has asked for each release explicitly.
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Keep README in sync with behavior in the same commit (interval step, keys, examples use *Your name*, credit line is Megan Schmidt).

## Status (2026-10-07)

0.1.4 live on GitHub, Homebrew tap, and PyPI (0.1.3 on PyPI is a superseded older build). Old account-wide PyPI token deleted (per Meg); uploads use a project-scoped token. Open: npm `posturebot` unclaimed (optional `npx` wrapper, undecided); domains posturebot.io/.xyz looked free. Related memory: `posturebot-project.md`.
