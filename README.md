<p align="center"><img src="assets/posturebot.png" alt="PostureBot" width="160"></p>

# PostureBot

A tiny 8-bit bot that sits in a side pane of your terminal (next to Claude Code, vim, anything), bobs gently, and says out loud every so often:

> "Hey *Your name*, just reminding you to check your posture. Love you!"

Free, no accounts, no dependencies. One Python file.

## Install

```
brew install m3gm3g/tap/posturebot      # macOS (Homebrew)
pipx install posturebot                 # or with pipx (macOS, Linux, Windows)
posturebot
```

## Docker

```
docker run -it --rm ghcr.io/m3gm3g/posturebot
```

The bot shows up and bobs, but containers have no sound, so there is no speech. Use brew or pipx for the voice.

## Or just run it

```
git clone https://github.com/m3gm3g/PostureBot.git
python3 PostureBot/posture_bot.py
```

Open it in a split pane and leave it there. It speaks for as long as it's running; `q` quits.
The first run asks your name and how often (in minutes) to remind you. Settings are saved to `~/.posture-bot.json`.

## Keys

```
q  quit
n  remind now
+  longer
-  shorter
m  mute
b  bot color
c  change name
r  my reminder
```

- **`+` / `-`** change the interval by 1 minute (never below 1).
- **`b`** switches the bot between periwinkle and butter yellow.
- **`r`** sets your own reminder. The bot speaks exactly what you type instead of the posture check. Clear it and press Enter to go back to the default.

## Options

```
python3 posture_bot.py --name "Your name" --minutes 20
python3 posture_bot.py --voice Samantha --rate 165     # macOS
python3 posture_bot.py --voice Zira                    # Windows (part of an installed voice's name)
```

## Requirements

- **macOS** (tested): uses the built-in `say` voice. Try `say -v '?'` for voices; the default is `Kathy`.
- **Linux** (untested): works if `espeak-ng`, `espeak` or `spd-say` is installed.
- **Windows** (new, untested): needs Windows 10+ and Windows Terminal (or a recent console). Speaks with the built-in Windows voices through PowerShell. The default voice, Kathy, is a Mac voice, so Windows uses your system voice unless you pass `--voice` (e.g. `--voice Zira`). Use `python` or `py` instead of `python3`. If you try it, please tell me how it goes.
- Python 3 (tested on 3.14) and a terminal with true-color support.

## License

MIT. Made by [Megan Schmidt](https://megyschmidt.com) / [Kitschy Lemon](https://github.com/m3gm3g).
