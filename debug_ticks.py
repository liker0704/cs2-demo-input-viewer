from demoparser2 import DemoParser
import sys

if len(sys.argv) < 2:
    print("Usage: python debug_ticks.py <demo_path>")
    sys.exit(1)

demo_path = sys.argv[1]
parser = DemoParser(demo_path)

print(f"Inspecting: {demo_path}")

fields = [
    "CCSPlayerPawn.CCSPlayer_MovementServices.m_nButtonDownMaskPrev",
    "m_steamID"
]

print(f"\n--- Testing parse_ticks with fields: {fields} ---")
try:
    # Try to parse first 1000 ticks
    df = parser.parse_ticks(fields)
    print(f"Returned DataFrame shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    if not df.empty:
        print(df.head())
        
        # Check for steamid column (it might be 'steamid' or 'm_steamID')
        steam_col = 'm_steamID' if 'm_steamID' in df.columns else 'steamid'
        if steam_col in df.columns:
            print("\nUnique Steam IDs found:")
            print(df[steam_col].unique())
        else:
            print("\nNo steam ID column found")

        # Check for button mask
        btn_col = "CCSPlayerPawn.CCSPlayer_MovementServices.m_nButtonDownMaskPrev"
        if btn_col in df.columns:
            active_inputs = df[df[btn_col] > 0]
            print(f"\nTicks with active inputs: {len(active_inputs)}")
            if not active_inputs.empty:
                print(active_inputs.head())
        else:
            print(f"\n'{btn_col}' not in columns")
    else:
        print("DataFrame is empty")

except Exception as e:
    print(f"Error parsing ticks: {e}")
