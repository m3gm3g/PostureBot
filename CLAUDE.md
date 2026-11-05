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

## Automated release (GitHub Actions)

`.github/workflows/ci.yml` smoke-tests on Linux/macOS/Windows. `release.yml` runs on a pushed `v*` tag: checks tag == pyproject version, builds, `pipx run twine upload --skip-existing` to PyPI (secret `PYPI_API_TOKEN`, environment `pypi`), creates/updates the GitHub release, and updates the tap formula (secret `TAP_GITHUB_TOKEN`). `ghcr.yml` also fires on the tag and pushes `ghcr.io/m3gm3g/posturebot:<version>` + `:latest` (multi-arch, built from `Dockerfile`, uses `GITHUB_TOKEN`; image is visual-only, no audio). GitHub Packages has no PyPI registry, so GHCR is the fit. With this in place, steps 2-7 above are automatic after bumping the version and pushing the tag.

## Workflow rules

- Ship-it repo (listed in ~/CLAUDE.md): a request is approval to take it all the way out (commit, push, tag, release) without asking again. Never handle her tokens; she pastes secrets and runs logins herself.
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Keep README in sync with behavior in the same commit (interval step, keys, examples use *Your name*, credit line is Megan Schmidt).

## Status (2026-10-08)

0.1.5 live on PyPI, GitHub, Homebrew tap, and ghcr.io, all published by Actions from a `v*` tag (secrets `PYPI_API_TOKEN`, `TAP_GITHUB_TOKEN` set; `GITHUB_TOKEN` covers ghcr). Old account-wide PyPI token deleted (per Meg). No local Docker (MacBook Neo); containers only via CI. Open: npm wrapper (undecided), posturebot.io/.xyz domain, Windows/Linux untested, `TAP_GITHUB_TOKEN` expires in about a year (renew). Related memory: `posturebot-project.md`.

## Next feature

Meg says what she wants; build it in `posture_bot.py`, test in a pty (see Testing), update README + this file in the same commit, then ship: bump `pyproject.toml`, push, tag `vX.Y.Z`. Actions does the rest. Verify PyPI/GitHub/tap after.

## Running it on Meg's Mac mini (added 2026-11-05)

PostureBot was built and tested on Meg's MacBook Neo. Her older Mac mini (Macmini9,1, macOS 26.5.1, 1920x1080) needs these steps for it to look and run right:

- **Python 3.14, not the system `python3`.** There, plain `python3` resolves to Xcode's bundled Python 3.9. Run the bot with Homebrew's `/opt/homebrew/bin/python3.14` (`brew install python@3.14`; 3.14.10 as of this note). Permanent clone: `~/posture-bot`.
- **Always a narrow side pane, never its own full-size window.** Claude Code runs in Apple Terminal, which can't put a second program in a split pane, and tmux isn't installed. Open a new Terminal window and dock it flush against the right edge of the Claude Code window, at the same top and bottom and about 240 px (~29 cols) wide. The panel is 18 cols, so it needs at least ~20.
- **Opaque Terminal profile.** The mini's default profile, "Clear Dark", is translucent with blur. The face is drawn as background-colored cells and the edges as opaque `▀`/`▄` glyphs, so under a translucent profile the face looks washed out and the edges stay solid, giving a striped, "splitty" bot that doesn't match `assets/posturebot.png`. Set the bot's tab to "Basic" (opaque). The sprite code itself is unchanged.
- **`brew install m3gm3g/tap/posturebot` is blocked** on the mini until the Command Line Tools are updated. Brew says: "Your Command Line Tools (CLT) does not support macOS 26." Meg has to update them herself, since that needs sudo (Software Update, or `sudo rm -rf /Library/Developer/CommandLineTools && sudo xcode-select --install`). Until then, run from the clone with python3.14.

Launch recipe (AppleScript, Claude Code window id from `tell application "Terminal" to get {id, bounds} of every window`):

```applescript
tell application "Terminal"
  set cb to bounds of window id CLAUDE_WINDOW_ID
  set w to do script "clear; /opt/homebrew/bin/python3.14 ~/posture-bot/posture_bot.py"
  delay 0.5
  set win to (first window whose selected tab is w)
  set current settings of w to settings set "Basic"
  set bounds of win to {(item 3 of cb) + 2, item 2 of cb, (item 3 of cb) + 242, item 4 of cb}
  set custom title of w to "PostureBot"
end tell
```

Possible future fix in code: paint solid cells with a full block `█` in the foreground color instead of a background-colored space, so the bot looks right even in translucent profiles.
