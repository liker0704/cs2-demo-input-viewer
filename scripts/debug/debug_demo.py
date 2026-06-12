from demoparser2 import DemoParser
import sys

if len(sys.argv) < 2:
    print("Usage: python debug_demo.py <demo_path>")
    sys.exit(1)

demo_path = sys.argv[1]
parser = DemoParser(demo_path)

print(f"Inspecting: {demo_path}")

# List all event names
print("\n--- Available Events ---")
try:
    events = parser.list_game_events()
    for event in events[:20]: # Print first 20
        print(event)
    if len(events) > 20:
        print(f"... and {len(events) - 20} more")
except Exception as e:
    print(f"Error listing events: {e}")

# Try to parse a common event like 'player_death' to verify parser works
print("\n--- Testing player_death extraction ---")
try:
    deaths = parser.parse_event("player_death")
    print(f"Found {len(deaths)} player_death events")
    if not deaths.empty:
        print(deaths.head())
except Exception as e:
    print(f"Error parsing player_death: {e}")

# Check if 'player_input' exists or similar
print("\n--- Checking for input-related events ---")
input_events = [e for e in events if "input" in e.lower() or "cmd" in e.lower()]
print("Events with 'input' or 'cmd':", input_events)
