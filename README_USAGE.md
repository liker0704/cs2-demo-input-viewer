# CS2 Input Visualizer - User Guide

Complete guide for installing, configuring, and using the CS2 Input Visualizer.

## Table of Contents

- [What is This?](#what-is-this)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CS2 Setup](#cs2-setup)
- [Running the Application](#running-the-application)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [FAQ](#faq)

---

## What is This?

The CS2 Input Visualizer shows you exactly which keys and mouse buttons a player is pressing while watching CS2 demo files. Perfect for:

- **Learning from pros**: See exactly what inputs professional players use
- **Analyzing gameplay**: Review your own demos to improve mechanics
- **Creating content**: Add professional input overlays to your YouTube/Twitch videos
- **Understanding mechanics**: Learn movement techniques, counter-strafing, spray control

The overlay displays in real-time during demo playback, synchronized perfectly with the game.

---

## Installation

### Requirements

- **Python 3.10, 3.11, or 3.12** (3.12 recommended)
- **Counter-Strike 2** installed
- **Operating System**: Windows, Linux, or macOS

### Step 1: Install Python

Download Python from [python.org](https://www.python.org/downloads/)

**Important**: During installation, check "Add Python to PATH"!

Verify installation:
```bash
python --version
# Should show: Python 3.10.x or higher
```

### Step 2: Download This Project

**Option A: Using Git**
```bash
git clone https://github.com/yourusername/cs2-demo-input-viewer
cd cs2-demo-input-viewer
```

**Option B: Download ZIP**
1. Download ZIP from GitHub
2. Extract to a folder
3. Open terminal/command prompt in that folder

### Step 3: Install Dependencies

Create a virtual environment (recommended):

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Install required packages:
```bash
pip install -r requirements.txt
```

This installs:
- **PyQt6**: For the overlay window
- **demoparser2**: For parsing CS2 demo files
- **asyncio**: For async network communication

### Step 4: Verify Installation

Test that everything works:
```bash
python src/main.py --mode dev
```

You should see an overlay window with animated keyboard and mouse inputs. This is test mode running without CS2.

Press **Ctrl+C** to stop.

---

## Quick Start

### Mode 1: Development Mode (Testing Without CS2)

Run the visualizer without needing CS2:

```bash
python src/main.py --mode dev
```

This shows the overlay with simulated inputs. Great for:
- Testing the overlay appearance
- Adjusting position and opacity
- Verifying installation

### Mode 2: Production Mode (Manual Control)

Full manual control over demo selection and player tracking.

1. **Get a demo file** (`.dem` file):
   - Download from FACEIT/HLTV
   - Record your own in CS2
   - Use CS2's automatic match demos

2. **Process the demo** (create cache):
   ```bash
   python -m src.parsers.etl_pipeline --demo path/to/your_demo.dem
   ```

   This takes 30-60 seconds and creates `cache/your_demo_cache.json`

3. **Launch CS2 with special parameters**:
   ```bash
   # Windows (Steam):
   # Right-click CS2 � Properties � Launch Options:
   -netconport 2121 -insecure
   ```

4. **Start demo playback in CS2**:
   ```
   # In CS2 console (~):
   playdemo your_demo
   ```

5. **Run the visualizer**:
   ```bash
   python src/main.py --mode prod --demo path/to/your_demo.dem
   ```

The overlay will appear and sync automatically with CS2!

### Mode 3: Auto Mode (Fully Automatic) ⭐ NEW

**The easiest way to use the visualizer!** Auto mode handles everything automatically:

- Detects CS2 installation path automatically
- Monitors when you load demos in CS2
- Validates and rebuilds cache automatically
- Tracks which player you're spectating
- Updates visualization in real-time

**How to use:**

1. **Launch CS2 with network console enabled:**
   ```bash
   # Add to Steam launch options:
   -netconport 2121 -insecure
   ```

2. **Start the visualizer in auto mode:**
   ```bash
   python src/main.py --mode auto
   ```

3. **Play any demo in CS2:**
   ```
   # In CS2 console (~):
   playdemo your_demo
   ```

4. **Done!** The visualizer will:
   - Detect that you loaded a demo
   - Check if cache exists (create if needed)
   - Track which player you're spectating
   - Display their inputs automatically

**Auto Mode Workflow:**

```
[You] Launch CS2 with -netconport 2121
  ↓
[You] Run: python src/main.py --mode auto
  ↓
[Auto] Detecting CS2 installation... ✓
  ↓
[Auto] Connecting to CS2 telnet... ✓
  ↓
[Auto] Waiting for demo to be loaded...
  ↓
[You] In CS2 console: playdemo match
  ↓
[Auto] Demo detected: match.dem
  ↓
[Auto] Validating cache... (50ms)
  ↓
[Auto] Cache valid ✓ (or building new cache...)
  ↓
[Auto] Tracking spectator target...
  ↓
[Auto] Displaying inputs for: PlayerName
  ↓
[You] Switch spectator in CS2 (press Space)
  ↓
[Auto] Spectator changed, updating visualization...
```

**When to use Auto Mode:**
- ✅ Quick analysis sessions
- ✅ Reviewing multiple demos
- ✅ Switching between players frequently
- ✅ First-time users (zero configuration)

**When to use Manual Mode (prod):**
- ✅ Specific player analysis
- ✅ Recording/streaming (predictable setup)
- ✅ Custom cache locations
- ✅ Advanced configuration needs

---

## CS2 Setup

### Launch Parameters

CS2 **must** be launched with these parameters for the visualizer to work:

```
-netconport 2121 -insecure
```

**How to add launch parameters:**

**Steam (Windows/Linux):**
1. Right-click Counter-Strike 2 in library
2. Select "Properties"
3. In "Launch Options", add: `-netconport 2121 -insecure`
4. Click OK and launch CS2 normally

**Steam Deck:**
1. Select CS2 � Gear icon � Properties
2. In "Launch Options", add: `-netconport 2121 -insecure`
3. Launch game

### What These Parameters Do

- **`-netconport 2121`**: Opens a network console port that the visualizer connects to
- **`-insecure`**: Disables VAC (Valve Anti-Cheat) protection

### VAC Safety Warning

**IMPORTANT**: The `-insecure` flag disables VAC, which means:

-  **SAFE**: Watching demos with this flag
-  **SAFE**: Playing on community servers without VAC
- L **UNSAFE**: Playing on VAC-secured servers (matchmaking, official servers)

**Always remove `-insecure` before playing online!**

To remove:
1. Go back to CS2 Properties � Launch Options
2. Delete `-netconport 2121 -insecure`
3. Click OK

### Demo Playback

Load demos in CS2 console:

```
# List available demos
demo_listtimes

# Play a demo
playdemo demo_name

# Play from specific tick
playdemo demo_name 50000

# Demo controls (while playing)
demo_pause         # Pause/resume
demo_timescale 0.5 # Slow motion (0.5x speed)
demo_timescale 2   # Fast forward (2x speed)
demo_goto 100000   # Jump to tick
```

---

## Running the Application

### Basic Usage

**Development mode** (testing without CS2):
```bash
python src/main.py --mode dev
```

**Auto mode** (fully automatic with CS2):
```bash
python src/main.py --mode auto
```

**Production mode** (manual control with CS2):
```bash
python src/main.py --mode prod --demo demos/match.dem
```

### Command Line Options

```bash
python src/main.py [OPTIONS]
```

**Options:**

- `--mode {dev,prod,auto}`: Run mode (default: dev)
  - `dev`: Uses mock data, no CS2 needed
  - `prod`: Connects to CS2, requires demo file (manual control)
  - `auto`: Fully automatic mode (detects demos and players automatically)

- `--demo PATH`: Path to demo file (.dem)
  - Required for production mode
  - Example: `--demo demos/match.dem`

- `--config PATH`: Path to config file (default: config.json)
  - Example: `--config my_config.json`

- `--player STEAMID`: Specific player to visualize
  - Example: `--player STEAM_1:0:123456789`
  - Default: Auto-detect from demo

- `--generate-config`: Generate example config and exit

- `--debug`: Enable debug mode with verbose logging

### Examples

**Test the overlay appearance:**
```bash
python src/main.py --mode dev
```

**Quick start with auto mode:**
```bash
python src/main.py --mode auto
```

**Visualize specific demo (manual mode):**
```bash
python src/main.py --mode prod --demo demos/faceit_match.dem
```

**Use custom configuration:**
```bash
python src/main.py --mode prod --demo demos/match.dem --config my_config.json
```

**Visualize specific player:**
```bash
python src/main.py --mode prod --demo demos/match.dem --player STEAM_1:0:123456789
```

**Generate example config:**
```bash
python src/main.py --generate-config
```

---

## Configuration

### Configuration File

Create `config.json` in the project root:

```bash
# Generate example config:
python src/main.py --generate-config

# Copy to config.json:
cp config.example.json config.json

# Edit with your preferred editor:
notepad config.json   # Windows
nano config.json      # Linux/macOS
```

### Configuration Options

```json
{
  "cs2_host": "127.0.0.1",
  "cs2_port": 2121,
  "polling_interval": 0.25,
  "render_fps": 60,
  "overlay_opacity": 0.9,
  "cache_dir": "./cache",
  "demo_path": null,
  "target_player_id": null,
  "max_drift": 10,
  "smoothing_window": 5,
  "overlay_scale": 1.0,
  "overlay_x": 100,
  "overlay_y": 100,
  "overlay_width": 700,
  "overlay_height": 300,
  "debug_mode": false,
  "show_fps": false,
  "use_smooth_prediction": true,
  "player_tracking_interval": 1.0,
  "reconnect_attempts": 3,
  "reconnect_delay": 2.0
}
```

### Key Settings Explained

**Network Settings:**
- `cs2_host`: CS2 server address (use `127.0.0.1` for local)
- `cs2_port`: Network console port (must match `-netconport` parameter)
- `polling_interval`: How often to query CS2 in seconds (0.25 = 4 times per second)

**Rendering Settings:**
- `render_fps`: Overlay refresh rate (30-120, default 60)
- `overlay_opacity`: Transparency (0.0 = invisible, 1.0 = solid)
- `overlay_scale`: Size multiplier (1.0 = 100%, 1.5 = 150%)

**Overlay Position:**
- `overlay_x`: Horizontal position in pixels from left edge
- `overlay_y`: Vertical position in pixels from top edge
- `overlay_width`: Overlay width in pixels
- `overlay_height`: Overlay height in pixels

**Data Settings:**
- `cache_dir`: Where to store processed demo data
- `demo_path`: Default demo file to load
- `target_player_id`: Specific player Steam ID (null = auto-detect)

**Advanced Settings:**
- `max_drift`: Maximum tick difference before correction (in ticks)
- `smoothing_window`: Smoothing buffer size for prediction (in ticks)
- `use_smooth_prediction`: Enable jump/pause detection (recommended: true)
- `reconnect_attempts`: Auto-reconnect attempts on network failure
- `reconnect_delay`: Delay between reconnect attempts (seconds)

### Customizing the Overlay

**Change position:**
```json
{
  "overlay_x": 50,   // 50 pixels from left
  "overlay_y": 900   // 900 pixels from top (bottom of 1080p screen)
}
```

**Make it larger:**
```json
{
  "overlay_scale": 1.5   // 150% size
}
```

**Make it more/less transparent:**
```json
{
  "overlay_opacity": 0.7   // 70% opacity (more transparent)
}
```

**Adjust performance:**
```json
{
  "render_fps": 30,         // Lower FPS = less CPU usage
  "polling_interval": 0.5   // Poll less frequently = less network traffic
}
```

---

## Troubleshooting

### Connection Errors

**Error: `Connection refused`**

**Cause**: CS2 is not running or not launched with `-netconport 2121`

**Solution**:
1. Close CS2 completely
2. Add `-netconport 2121 -insecure` to launch options
3. Restart CS2
4. Try again

---

**Error: `Connection timeout`**

**Cause**: Firewall blocking connection or wrong port

**Solution**:
1. Check firewall settings (allow Python)
2. Verify CS2 launch options include `-netconport 2121`
3. Try different port in both launch options and config:
   ```json
   {"cs2_port": 2222}
   ```
   And launch CS2 with: `-netconport 2222 -insecure`

---

### Cache Errors

**Error: `Cache file not found`**

**Cause**: Demo hasn't been processed with ETL pipeline

**Solution**:
```bash
# Process the demo to create cache:
python -m src.parsers.etl_pipeline --demo path/to/demo.dem

# This creates: cache/demo_cache.json
# Then run the visualizer:
python src/main.py --mode prod --demo path/to/demo.dem
```

---

**Error: `Failed to parse demo`**

**Cause**: Demo file corrupted or incompatible

**Solution**:
1. Re-download the demo file
2. Verify file size (should be >100MB for full match)
3. Try a different demo to verify the tool works
4. Check demoparser2 compatibility:
   ```bash
   pip install --upgrade demoparser2
   ```

---

### Overlay Issues

**Problem: Overlay doesn't appear**

**Solutions**:
1. Check if overlay is off-screen:
   ```json
   {
     "overlay_x": 100,
     "overlay_y": 100
   }
   ```

2. Verify opacity isn't 0:
   ```json
   {
     "overlay_opacity": 0.9
   }
   ```

3. Run in dev mode to test:
   ```bash
   python src/main.py --mode dev
   ```

---

**Problem: Overlay is on wrong monitor**

**Solution**:
Adjust position to your second monitor:
```json
{
  "overlay_x": 1920,  // Start of second 1920x1080 monitor
  "overlay_y": 100
}
```

---

**Problem: Inputs are delayed or wrong**

**Cause**: Synchronization issue or cache mismatch

**Solution**:
1. Regenerate cache:
   ```bash
   python -m src.parsers.etl_pipeline --demo demo.dem
   ```

2. Restart both CS2 and visualizer

3. Increase polling interval if network is slow:
   ```json
   {
     "polling_interval": 0.5
   }
   ```

---

### Auto Mode Issues

**Problem: "Failed to detect CS2 installation"**

**Cause**: CS2 not installed or installed in non-standard location

**Solution**:
1. Verify CS2 is installed via Steam
2. If installed in custom location, use manual mode instead:
   ```bash
   python src/main.py --mode prod --demo path/to/demo.dem
   ```
3. Check if CS2 process is running:
   ```bash
   # Windows:
   tasklist | findstr cs2
   # Linux:
   ps aux | grep cs2
   ```

---

**Problem: "Failed to connect to CS2 telnet"**

**Cause**: CS2 not launched with `-netconport 2121`

**Solution**:
1. Close CS2
2. Add `-netconport 2121 -insecure` to Steam launch options
3. Restart CS2
4. Start auto mode again:
   ```bash
   python src/main.py --mode auto
   ```

---

**Problem: "Demo detected but cache building is slow"**

**Cause**: Large demo file being processed for first time

**Solution**:
This is normal! Cache is built once, then validated quickly (~50ms) on subsequent runs:
- First run: May take 30-60 seconds for full match demo
- Subsequent runs: <100ms cache validation
- Cached data is reused across sessions

---

**Problem: "Spectator tracking not working"**

**Cause**: Not in spectator mode or rapid switching

**Solution**:
1. Ensure you're in spectator mode (not freecam)
2. Wait 1 second after switching players (tracking interval)
3. Check console output for spectator changes
4. If still not working, restart in manual mode with specific player:
   ```bash
   python src/main.py --mode prod --demo demo.dem --player STEAM_1:0:123456789
   ```

---

**Problem: "Auto mode shows wrong player inputs"**

**Cause**: Cache from different version of demo file

**Solution**:
Delete cache and let it rebuild:
```bash
# Windows:
del cache\demo_name.json cache\demo_name.md5
# Linux/macOS:
rm cache/demo_name.json cache/demo_name.md5

# Then restart auto mode:
python src/main.py --mode auto
```

---

### Performance Issues

**Problem: Overlay is laggy/stuttering**

**Solutions**:

1. **Lower render FPS:**
   ```json
   {
     "render_fps": 30
   }
   ```

2. **Reduce polling frequency:**
   ```json
   {
     "polling_interval": 0.5
   }
   ```

3. **Close other applications** to free up resources

4. **Disable smooth prediction** if experiencing issues:
   ```json
   {
     "use_smooth_prediction": false
   }
   ```

---

**Problem: High CPU usage**

**Solutions**:
1. Lower FPS (see above)
2. Reduce overlay scale:
   ```json
   {
     "overlay_scale": 0.8
   }
   ```

3. Close unnecessary applications

---

### Python/Dependency Issues

**Error: `ModuleNotFoundError: No module named 'PyQt6'`**

**Solution**:
```bash
# Make sure virtual environment is activated:
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Reinstall dependencies:
pip install -r requirements.txt
```

---

**Error: `ModuleNotFoundError: No module named 'demoparser2'`**

**Solution**:
```bash
pip install demoparser2
# Or reinstall all:
pip install -r requirements.txt
```

---

## Advanced Usage

### Processing Demos

The ETL (Extract, Transform, Load) pipeline processes demo files into cache files for fast playback:

```bash
# Basic usage:
python -m src.parsers.etl_pipeline --demo path/to/demo.dem

# Specify output location:
python -m src.parsers.etl_pipeline --demo demo.dem --output cache/custom_name.json

# Process and optimize:
python -m src.parsers.etl_pipeline --demo demo.dem --optimize
```

**What the ETL does:**
1. Parses demo file with demoparser2
2. Extracts input data for all ticks
3. Decodes button masks to key names
4. Identifies the main player (POV player)
5. Saves to JSON cache file

**Cache file structure:**
```json
{
  "meta": {
    "demo_file": "match.dem",
    "player_id": "STEAM_1:0:123456789",
    "player_name": "PlayerName",
    "tick_range": [0, 160000],
    "tick_rate": 64
  },
  "inputs": {
    "1000": {
      "keys": ["W", "A"],
      "mouse": ["MOUSE1"],
      "subtick": {"W": 0.0, "A": 0.2, "MOUSE1": 0.5}
    }
  }
}
```

### Finding Player Steam IDs

To visualize a specific player:

1. **Run ETL and check output:**
   ```bash
   python -m src.parsers.etl_pipeline --demo demo.dem
   # Output shows: "Detected player: STEAM_1:0:123456789 (PlayerName)"
   ```

2. **Use the Steam ID:**
   ```bash
   python src/main.py --mode prod --demo demo.dem --player STEAM_1:0:123456789
   ```

3. **Or add to config:**
   ```json
   {
     "target_player_id": "STEAM_1:0:123456789"
   }
   ```

### Multiple Demos

Process multiple demos at once:

```bash
# Linux/macOS:
for demo in demos/*.dem; do
  python -m src.parsers.etl_pipeline --demo "$demo"
done

# Windows (PowerShell):
Get-ChildItem demos\*.dem | ForEach-Object {
  python -m src.parsers.etl_pipeline --demo $_.FullName
}
```

### Recording Sessions

Record input data to file for later analysis:

```bash
# Enable recording in config:
{
  "record_inputs": true,
  "record_output": "recordings/session_1.json"
}
```

(Note: This feature may require additional implementation)

### Custom Key Bindings

The visualizer shows standard CS2 keys. To customize which keys are displayed, modify the `KeyboardLayout` in `src/ui/layouts.py`.

---

## FAQ

### General

**Q: Is this VAC safe?**

A: Yes, when used correctly:
-  Safe for watching demos with `-insecure` flag
- L Unsafe for online play with `-insecure` flag
- Always remove `-insecure` before playing online!

---

**Q: Does this work with GOTV demos?**

A: Yes! Works with:
- GOTV demos (from HLTV, FACEIT, etc.)
- POV demos (recorded by players)
- Official matchmaking demos
- Community server demos

---

**Q: Can I use this for live matches?**

A: No. This tool is designed for demo playback only. It cannot capture live inputs during gameplay.

---

**Q: Does it show enemy inputs?**

A: No. It only shows inputs for the player you're spectating (usually the POV player in the demo).

---

**Q: Can I change the overlay colors/style?**

A: Not in v1.0, but it's planned for future releases. You can modify the source code in `src/ui/` if you're comfortable with Python/PyQt6.

---

### Technical

**Q: What tick rate does CS2 use?**

A: CS2 uses 64 tick servers by default. Some third-party servers may use 128 tick.

---

**Q: Why does the visualizer poll CS2 instead of streaming?**

A: CS2's network console doesn't support streaming. We poll at 4Hz which is efficient and provides smooth visualization through tick prediction.

---

**Q: Can I run multiple instances?**

A: No, only one visualizer can connect to CS2's network console at a time (port 2121).

---

**Q: Does this work on Linux/macOS?**

A: Yes! Tested on Windows, Linux, and macOS (though macOS CS2 support varies).

---

### Troubleshooting

**Q: The overlay shows wrong inputs**

A: This usually means cache mismatch. Regenerate:
```bash
python -m src.parsers.etl_pipeline --demo demo.dem
```

---

**Q: Why does it say "No player selected"?**

A: Set the player explicitly:
```bash
python src/main.py --mode prod --demo demo.dem --player STEAM_1:0:123456789
```

---

**Q: Can I record the overlay for videos?**

A: Yes! Use OBS or other screen capture software. The overlay is a transparent window that will appear over CS2.

---

**Q: The overlay disappears when I click on it**

A: This is intentional - the overlay is click-through so it doesn't interfere with CS2. You can't interact with it while it's running.

---

## Support

### Getting Help

1. **Check this guide first** - Most issues are covered in Troubleshooting
2. **Check GitHub Issues** - Someone may have reported the same problem
3. **Enable debug mode** to get more information:
   ```bash
   python src/main.py --mode prod --demo demo.dem --debug
   ```
4. **Create a GitHub Issue** with:
   - Error messages
   - Your config.json
   - Steps to reproduce
   - Python version (`python --version`)
   - OS (Windows/Linux/macOS)

### Contributing

Contributions welcome! See `CONTRIBUTING.md` for guidelines.

### License

MIT License - Free to use and modify. See `LICENSE` file.

---

## Credits

- **demoparser2**: LaihoE - CS2 demo parsing library
- **PyQt6**: Riverbank Computing - GUI framework
- **CS2 Community**: For documentation and support

---

**Enjoy analyzing those pro demos!** <�
