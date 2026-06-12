# cs2-demo-input-viewer

Transparent overlay that shows which keys and mouse buttons a player was hitting while you watch a CS2 demo. Demos get chewed through offline by an ETL pass that builds an indexed cache. At playback time a separate process talks to CS2 over its telnet console, lines up the current tick (subtick-accurate), and paints the inputs on top of the game.

Works on Windows and Linux. macOS isn't tested and probably won't work.

## Setup

You'll need Python 3.10-3.12 and CS2 launched with `-netconport 2121 -insecure` so the overlay can read the tick from the console.

```bash
git clone <repo-url>
cd cs2-demo-input-viewer
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Main deps are PyQt6, demoparser2, psutil. Full list in `requirements.txt`.

## Modes

Three modes, picked with `--mode`. Run `python src/main.py --help` for the rest.

### dev

No CS2 needed. Mock data sources, fake ticks. Use it to poke at the overlay or while hacking on code.

```bash
python src/main.py --mode dev
```

### auto

Finds your CS2 install, hooks up to the telnet console, waits for you to type `playdemo <name>` ingame, then follows whoever you're spectating. Parses the demo and builds the cache on the fly if it isn't there yet. This is what you want 95% of the time.

```bash
# launch CS2 with -netconport 2121 -insecure first
python src/main.py --mode auto
```

### prod

Manual. You point it at a `.dem` file (and optionally a Steam ID). Cache has to exist already, so run the ETL first.

```bash
python -m src.parsers.etl_pipeline --demo demos/match.dem
python src/main.py --mode prod --demo demos/match.dem
# or pin a specific player:
python src/main.py --mode prod --demo demos/match.dem --player STEAM_1:0:123456789
```

## Notes

Config lives in `config.json` (telnet host/port, polling interval, overlay position, opacity, cache dir, defaults for prod mode). Generate a fresh template:

```bash
python src/main.py --generate-config
cp config.example.json config.json
```

CLI flags `--demo`, `--player`, `--debug` override whatever's in the config file.

Gotchas worth knowing:

- prod mode bails out if there's no cache for the demo. Run the ETL step.
- The telnet port (2121) has to match what you put in `-netconport`. If you changed one, change the other.
- Overlay is a click-through window. If it doesn't show up, double-check `overlay_x`/`overlay_y` aren't off-screen.

## Docs

More detail in [docs/README.md](docs/README.md) (architecture, ETL, telnet protocol, auto-mode internals, etc).

## License

MIT, see [LICENSE](LICENSE).
