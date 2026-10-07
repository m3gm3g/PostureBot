<p align="center"><img src="assets/posturebot.png" alt="PostureBot" width="160"></p>

# PostureBot

A tiny 8-bit bot that sits in a side pane of your terminal (next to Claude Code, vim, anything), bobs gently, and says out loud every so often:

> "Hey Meg, just reminding you to check your posture. Love you!"

Free, no accounts, no dependencies. One Python file.

## Run it

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

- **`+` / `-`** change the interval by 5 minutes.
- **`b`** switches the bot between periwinkle and butter yellow.
- **`r`** sets your own reminder. The bot speaks exactly what you type instead of the posture check. Clear it and press Enter to go back to the default.

## Options

```
python3 posture_bot.py --name Meg --minutes 20
python3 posture_bot.py --voice Samantha --rate 165
```

## Requirements

- **macOS** (tested): uses the built-in `say` voice. Try `say -v '?'` for voices; the default is `Samantha`.
- **Linux** (untested): works if `espeak-ng`, `espeak` or `spd-say` is installed.
- **Windows**: not supported (it uses `termios`/`fcntl`; WSL should work).
- Python 3 (tested on 3.14) and a terminal with true-color support.

## License

MIT. Made by Meg Schmidt / [Kitschy Lemon](https://github.com/m3gm3g).
