# User Guide

## CS2 Subtick Input Visualizer - Quick Start

### What is this?

This tool shows you exactly which keys a player is pressing while watching CS2 demo files. Perfect for:
- Learning from professional players
- Analyzing your own gameplay
- Creating YouTube content
- Understanding movement mechanics

---

## Installation

### Requirements

- **Python 3.10, 3.11, or 3.12**
- **CS2** installed
- **Windows/Linux** (Mac not tested but should work)

### Step 1: Install Python

Download from [python.org](https://www.python.org/downloads/)

**Important**: Check "Add Python to PATH" during installation!

### Step 2: Download This Tool

```bash
# Option A: Git
git clone <repository-url>
cd cs2-demo-input-viewer

# Option B: Download ZIP
# Extract to a folder
```

### Step 3: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

## Usage

### Quick Start (Test Mode)

Test the overlay without CS2:

```bash
python src/main.py --mode dev
```

You should see an overlay with animated keyboard/mouse inputs.

### Real Usage

#### Step 1: Prepare Demo File

Get a demo file (`.dem`) from:
- FACEIT match page (download demo)
- HLTV match page
- CS2 in-game (recorded demos)

Place it in `demos/` folder.

#### Step 2: Process Demo (ETL)

Convert demo to cache:

```bash
python -m src.parsers.etl_pipeline --demo demos/your_match.dem
```

This creates `cache/your_match_cache.json` (takes 30-60 seconds for 400MB demo).

#### Step 3: Launch CS2

**Important**: CS2 must be launched with special flags:

```bash
# Windows (Steam)
# Right-click CS2 in Steam → Properties → Launch Options:
-netconport 2121 -insecure

# Then launch CS2 normally
```

**Warning**: `-insecure` disables VAC. Only use for watching demos, never on official servers!

#### Step 4: Start Demo Playback

In CS2:
1. Open console (~)
2. Type: `playdemo demos/your_match`
3. Demo starts playing

#### Step 5: Run Visualizer

```bash
python src/main.py --mode prod --demo demos/your_match.dem
```

The overlay appears and syncs automatically!

---

## Configuration

### Config File

Copy `config.example.json` to `config.json` and edit:

```json
{
  "overlay_opacity": 0.9,    // 0.0 = invisible, 1.0 = solid
  "overlay_x": 100,          // Position on screen
  "overlay_y": 100,
  "overlay_scale": 1.0,      // Size (1.5 = 150%)
  "render_fps": 60,          // Smoothness
  "polling_interval": 0.25   // Network update speed
}
```

### Command Line

```bash
# Specify demo
python src/main.py --demo path/to/demo.dem

# Specify config
python src/main.py --config my_config.json

# Development mode (no CS2 needed)
python src/main.py --mode dev
```

---

## Controls

Currently, the overlay is **fixed position** and **click-through**.

To move it:
1. Edit `overlay_x` and `overlay_y` in `config.json`
2. Restart the visualizer

**Future**: Drag-and-drop support planned.

---

## Troubleshooting

### Issue: "Connection refused" error

**Problem**: CS2 is not running with `-netconport 2121`

**Solution**:
1. Close CS2
2. Add `-netconport 2121 -insecure` to launch options
3. Restart CS2
4. Try again

### Issue: "No module named 'demoparser2'"

**Problem**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: Overlay doesn't show

**Problem**: Overlay might be off-screen or hidden

**Solution**:
1. Check `config.json` values for `overlay_x` and `overlay_y`
2. Try setting both to `100`
3. Restart visualizer

### Issue: Inputs are delayed/wrong

**Problem**: Synchronization issue

**Solution**:
1. Pause demo in CS2
2. Restart visualizer
3. Resume demo
4. If still wrong, regenerate cache with ETL script

### Issue: "Failed to parse demo"

**Problem**: Demo file corrupted or incompatible

**Solution**:
1. Re-download demo file
2. Check file size (should be >100MB for full match)
3. Try different demo

---

## Advanced Usage

### Selecting Specific Player

By default, the tool shows inputs for the most frequently appearing player in the demo (usually the POV player).

To specify manually:

1. Run ETL and check output:
```bash
python -m src.parsers.etl_pipeline --demo demos/match.dem
# Output shows: "Player ID: STEAM_1:0:123456789"
```

2. Edit `config.json`:
```json
{
  "target_player_id": "STEAM_1:0:123456789"
}
```

### Recording Session

To record inputs to file:

```bash
python src/main.py --mode prod --demo demos/match.dem --record output.json
```

### Performance Tuning

If overlay is laggy:

```json
{
  "render_fps": 30,          // Lower FPS
  "polling_interval": 0.5    // Poll less frequently
}
```

If overlay is using too much CPU:
1. Close other applications
2. Reduce `render_fps` to 30
3. Reduce `overlay_scale` to 0.8

---

## FAQ

### Q: Is this VAC safe?

**A**: Yes, when used correctly:
- ✅ Safe: Watching demos with `-insecure` flag
- ❌ Unsafe: Using on VAC-secured servers

Always remove `-insecure` before playing online!

### Q: Does this work with GOTV demos?

**A**: Yes! Works with:
- GOTV demos
- POV demos
- FACEIT demos
- HLTV demos

### Q: Can I use this for live matches?

**A**: No, this tool is for demo playback only.

### Q: Does it show enemy inputs?

**A**: No, only shows inputs for the player you're spectating (usually the demo POV).

### Q: Can I change the colors?

**A**: Not yet in v1.0, but planned for future releases.

### Q: What about grenades/crosshair?

**A**: Planned features! Currently only shows keyboard/mouse inputs.

---

## Support

- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Discord**: [TBD]

---

## Credits

- **demoparser2**: LaihoE
- **PyQt6**: Riverbank Computing
- **CS2 Community**: For research and testing

---

## License

MIT License - Free to use and modify
