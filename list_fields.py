from demoparser2 import DemoParser
import sys

if len(sys.argv) < 2:
    print("Usage: python list_fields.py <demo_path>")
    sys.exit(1)

demo_path = sys.argv[1]
parser = DemoParser(demo_path)

print(f"Inspecting fields in: {demo_path}")

try:
    # This might produce a lot of output, so we'll print filtered results
    # We are looking for anything related to 'button', 'input', 'mask'
    print("Fetching fields (this might take a moment)...")
    # Note: demoparser2 might not have a direct 'list_fields' for ticks in python bindings easily accessible 
    # without parsing, but let's try to parse a single tick with a wildcard or check documentation behavior.
    # Actually, typically we just guess or use a tool. 
    # But wait, demoparser2 python has `parse_ticks` which we used.
    
    # Let's try to find stream fields.
    # In the absence of a direct list_fields, we might need to rely on `parse_event` for "player_info" or similar
    # OR just try to grep common names.
    
    # However, let's try to use the `parse_events` to see if we can find anything.
    # But wait, we want tick data (props).
    
    # Let's try to use a known working field to verify the parser is actually working for props.
    # "CBasePlayerController.m_iszPlayerName" is a common one.
    
    # Let's try to brute force check some common button fields
    candidates = [
        "m_nButtonDownMaskPrev",
        "m_pInGameHashes.m_nButtonDownMaskPrev",
        "m_pMovementServices.m_nButtonDownMaskPrev",
        "CCSPlayerController.m_nButtonDownMaskPrev",
        "CCSPlayerPawn.m_pMovementServices.m_nButtonDownMaskPrev",
        "CCSPlayerPawn.m_nButtonDownMaskPrev",
        "m_nButtonDownMask",
        "m_pMovementServices.m_nButtonDownMask"
    ]
    
    print("Checking candidate fields...")
    for field in candidates:
        try:
            df = parser.parse_ticks([field])
            if field in df.columns:
                print(f"[FOUND] {field}")
                # Print a sample
                print(df[df[field] > 0].head())
            else:
                print(f"[MISSING] {field}")
        except Exception as e:
            print(f"[ERROR] {field}: {e}")

except Exception as e:
    print(f"Error: {e}")
