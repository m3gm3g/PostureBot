#!/usr/bin/env python3
"""PostureBot: a tiny 8-bit bot that bobs in your terminal and says
"Hey <name>, just reminding you to check your posture. Love you!" every N minutes.

Run it in a split pane next to Claude Code (or any terminal). It speaks
for as long as it's running. Press q (or Ctrl+C) to stop.

  python3 posture_bot.py                      # uses saved settings, asks on first run
  python3 posture_bot.py --name Meg --minutes 20
  python3 posture_bot.py --voice Samantha --rate 165

Keys:  q quit   n remind me now   + / - change minutes   m mute voice   b bot color   c change name   r my reminder
"""
import argparse
import fcntl
import json
import os
import platform
import select
import shutil
import subprocess
import sys
import time

CONFIG = os.path.expanduser("~/.posture-bot.json")
DEFAULTS = {"name": "", "minutes": 30, "voice": "Samantha", "rate": None, "color": "periwinkle", "custom": ""}

BODY = "\033[38;2;156;168;255m"   # periwinkle
ACCENT = "\033[38;2;255;182;213m"  # blush
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG) as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG, "w") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


def message(cfg):
    """The custom reminder if the user wrote one, else the default posture check."""
    custom = (cfg.get("custom") or "").strip()
    if custom:
        return custom
    who = f"Hey {cfg['name']}," if cfg["name"] else "Hey,"
    return f"{who} just reminding you to check your posture. Love you!"


def speak(text, voice, rate):
    """Start speech without blocking. Returns the Popen handle (or None)."""
    system = platform.system()
    try:
        if system == "Darwin":
            cmd = ["say", "-v", voice] + (["-r", str(rate)] if rate else []) + [text]
            return subprocess.Popen(cmd)
        for tts in ("espeak-ng", "espeak", "spd-say"):
            if shutil.which(tts):
                return subprocess.Popen([tts, text])
    except OSError:
        pass
    return None


# --- the bot -------------------------------------------------------------

# name -> (body, legs); legs are a shade darker so the body reads as in front
PALETTES = {
    "periwinkle": ((156, 168, 255), (118, 130, 226)),
    "butter": ((255, 236, 153), (226, 196, 104)),
}
INK_RGB = (38, 38, 78)
BLUSH_RGB = (255, 182, 213)
BLUSH_TALK_RGB = (255, 150, 190)
SPRITE_W = 14
SPRITE_ROWS = 9               # terminal rows (2 pixels each)


def sprite_grid(blink, talking, happy, sunk, color="periwinkle"):
    """The bot as a grid of RGB pixels (None = transparent).
    Solid periwinkle face, big dark eyes, blush cheeks, no mouth.
    Drawn on a pixel grid (2 pixels per terminal row) so the bob is half a row:
    the legs are painted first and the body, in front, sinks one pixel over them.
    While talking the cheeks pulse; during a reminder the eyes smile shut."""
    BODY_RGB, LEG_RGB = PALETTES.get(color, PALETTES["periwinkle"])
    W, H = SPRITE_W, SPRITE_ROWS * 2
    grid = [[None] * W for _ in range(H)]

    def fill(x0, x1, y0, y1, rgb, dy=0):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                grid[y + dy][x] = rgb

    # legs (behind): 2 pixels tall, below the body
    fill(2, 4, 15, 16, LEG_RGB)
    fill(9, 11, 15, 16, LEG_RGB)

    # body (in front), shifted down half a row when sunk
    d = 1 if sunk else 0
    cheek = BLUSH_TALK_RGB if talking else BLUSH_RGB
    fill(2, 2, 1, 1, BODY_RGB, d)        # ears
    fill(11, 11, 1, 1, BODY_RGB, d)
    fill(0, 13, 3, 14, BODY_RGB, d)      # solid face
    if blink:
        fill(2, 4, 8, 8, INK_RGB, d)
        fill(9, 11, 8, 8, INK_RGB, d)
    elif happy:
        fill(2, 4, 7, 7, INK_RGB, d)
        fill(9, 11, 7, 7, INK_RGB, d)
    else:
        fill(2, 4, 6, 9, INK_RGB, d)
        fill(9, 11, 6, 9, INK_RGB, d)
    fill(1, 3, 10, 11, cheek, d)
    fill(10, 12, 10, 11, cheek, d)

    return grid


def sprite(blink, talking, happy, sunk, color="periwinkle"):
    """Terminal rows for the bot: pairs of grid pixels drawn with half-blocks."""
    grid = sprite_grid(blink, talking, happy, sunk, color)
    W = SPRITE_W
    margin = "  "
    rows = []
    for r in range(SPRITE_ROWS):
        line = ""
        for x in range(W):
            t, u = grid[2 * r][x], grid[2 * r + 1][x]
            if t is None and u is None:
                line += " "
            elif u is None:
                line += "\033[38;2;%d;%d;%dm▀%s" % (*t, RESET)
            elif t is None:
                line += "\033[38;2;%d;%d;%dm▄%s" % (*u, RESET)
            elif t == u:
                line += "\033[48;2;%d;%d;%dm %s" % (*t, RESET)
            else:
                line += "\033[38;2;%d;%d;%dm\033[48;2;%d;%d;%dm▀%s" % (*t, *u, RESET)
        rows.append(margin + line + margin)
    return rows


def fmt_clock(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


_last_size = None
PANEL_TEXT_W = 16


def wrap(text, width=PANEL_TEXT_W):
    """Word-wrap to a thin column; words longer than the column are split."""
    lines, line = [], ""
    for w in text.split(" "):
        while len(w) > width:
            if line:
                lines.append(line)
                line = ""
            lines.append(w[:width])
            w = w[width:]
        if len(line) + len(w) + (1 if line else 0) > width:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w) if line else w
    lines.append(line)
    return lines


def render(cfg, remaining, t, talking, muted, flash, editing=None):
    cols, rows = shutil.get_terminal_size((60, 20))
    bob = int(t / 1.6) % 2                    # slow breathe: flips every 1.6s
    blink = (int(t * 10) % 40) == 0
    lines = sprite(blink, talking, flash, bob, cfg.get("color", "periwinkle"))
    sw = 18                                    # sprite width
    left = max(0, cols - sw - 2)               # sit on the right edge

    global _last_size
    out = ["\033[?25l\033[?7l"]                # hide cursor, no auto-wrap
    if _last_size != (cols, rows):             # pane resized: wipe stale frames
        out.append("\033[2J")
        _last_size = (cols, rows)
    canvas = [""] * (rows - 1)
    bubble_rows = {}

    def put(row, text, col=left):
        if 0 <= row < len(canvas):
            plain = bubble_rows.get(row, "")
            pad = " " * max(1, col - len(plain))
            colored = f"{ACCENT}{plain}{RESET}" if plain else ""
            canvas[row] = colored + (pad if plain else " " * col) + text

    top = 2
    for i, ln in enumerate(lines):
        put(top + i, ln)

    status = "voice muted" if muted else "voice on"
    put(top + 11, f"{DIM}  next in {RESET}{BOLD}{fmt_clock(remaining)}{RESET}", left)
    put(top + 12, f"{DIM}  every {cfg['minutes']:g} min{RESET}", left)
    put(top + 14, f"{DIM}  {status}{RESET}", left)
    keys = ("q  quit", "n  remind now", "+  longer", "-  shorter", "m  mute",
            "b  bot color", "c  change name", "r  my reminder")
    for i, note in enumerate(keys):
        put(top + 15 + i, f"{DIM}  {note}{RESET}", left)
    base = top + 24
    if editing is not None:
        field, buf = editing
        put(base, f"{ACCENT}  {'your name' if field == 'name' else 'your reminder'}:{RESET}", left)
        typed = wrap(buf + "▌")[-6:]
        for i, ln in enumerate(typed):
            put(base + 1 + i, f"{BOLD}  {ln}{RESET}", left)
        row = base + 2 + len(typed)
        hints = ["enter  save", "esc  cancel"]
        if field == "custom":
            hints += [""] + wrap("empty = posture check")
        for i, h in enumerate(hints):
            put(row + i, f"{DIM}  {h}{RESET}", left)
    elif flash:
        # what she's saying, in the column under the key notes
        for i, ln in enumerate(wrap(message(cfg))):
            put(base + i, f"{ACCENT}  {ln}{RESET}", left)

    for i, c in enumerate(canvas):             # absolute rows: nothing can scroll
        out.append(f"\033[{i + 1};1H{c}\033[K")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def read_key():
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return ""


def first_run_setup(cfg, args):
    """Thin, one-idea-per-line prompts that fit a narrow side pane."""
    if not sys.stdin.isatty():
        return
    if args.name is None and not cfg["name"]:
        try:
            print(f"{BODY}hi! what's your{RESET}\n{BODY}name?{RESET}\n{DIM}enter to skip{RESET}")
            cfg["name"] = input("> ").strip()[:14]
        except EOFError:
            pass
    if args.minutes is None and not os.path.exists(CONFIG):
        try:
            print(f"\n{BODY}remind you every{RESET}\n{BODY}how many minutes?{RESET}\n{DIM}enter for {cfg['minutes']:g}{RESET}")
            raw = input("> ").strip()
        except EOFError:
            raw = ""
        if raw:
            try:
                cfg["minutes"] = max(0.1, float(raw))
            except ValueError:
                pass


def main():
    ap = argparse.ArgumentParser(description="Cute posture reminder bot.")
    ap.add_argument("--name", help="what the bot calls you")
    ap.add_argument("--minutes", type=float, help="reminder interval in minutes")
    ap.add_argument("--voice", help="macOS voice name (try: say -v '?')")
    ap.add_argument("--rate", type=int, help="speech rate, words/min (macOS); default is the voice's own speed")
    args = ap.parse_args()

    lock = open(os.path.expanduser("~/.posture-bot.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit("posture-bot is already running in another pane - close that one first.")

    cfg = load_config()
    first_run_setup(cfg, args)
    for k in ("name", "minutes", "voice", "rate"):
        v = getattr(args, k)
        if v is not None:
            cfg[k] = v
    save_config(cfg)

    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    sys.stdout.write("\033[?1049h\033[2J")    # alternate screen: leaves no scrollback junk

    muted = False
    editing = None          # None, or the name being typed
    proc = None
    flash_until = 0
    start = time.time()
    deadline = start + cfg["minutes"] * 60
    try:
        while True:
            now = time.time()
            key = read_key()
            if editing is not None:
                field, buf = editing
                limit = 14 if field == "name" else 140
                if key in ("\n", "\r"):
                    cfg[field] = buf.strip()
                    save_config(cfg)
                    editing = None
                elif key == "\x1b":
                    editing = None
                elif key in ("\x7f", "\x08"):
                    editing = (field, buf[:-1])
                elif key and key.isprintable() and len(buf) < limit:
                    editing = (field, buf + key)
                elif key == "\x03":
                    break
                key = ""
            elif key == "b":
                names = list(PALETTES)
                cfg["color"] = names[(names.index(cfg.get("color")) + 1) % len(names)] if cfg.get("color") in names else names[0]
                save_config(cfg)
                key = ""
            elif key == "c":
                editing = ("name", cfg["name"])
                key = ""
            elif key == "r":
                editing = ("custom", cfg.get("custom", ""))
                key = ""
            if key in ("q", "\x03"):
                break
            if key == "m":
                muted = not muted
            if key in ("+", "="):
                cfg["minutes"] += 5
                deadline = now + cfg["minutes"] * 60
                save_config(cfg)
            if key in ("-", "_"):
                cfg["minutes"] = max(1, cfg["minutes"] - 5)
                deadline = now + cfg["minutes"] * 60
                save_config(cfg)

            if now >= deadline or key == "n":
                if not muted:
                    proc = speak(message(cfg), cfg["voice"], cfg["rate"])
                flash_until = now + 8
                deadline = now + cfg["minutes"] * 60

            talking = bool(proc and proc.poll() is None and int((now - start) * 6) % 2)
            render(cfg, deadline - now, now - start, talking, muted, now < flash_until, editing)
            select.select([sys.stdin], [], [], 0.1)   # wake instantly on a keypress
    except KeyboardInterrupt:
        pass
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
        termios.tcsetattr(fd, termios.TCSANOW, old)
        sys.stdout.write(f"\033[?7h\033[?25h\033[?1049l{BODY}bye! sit tall ♡{RESET}\n")


if __name__ == "__main__":
    main()
