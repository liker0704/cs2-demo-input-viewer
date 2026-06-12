from demoparser2 import DemoParser
import sys

demo_path = sys.argv[1] if len(sys.argv) > 1 else "demos/1-ff115b7a-c62d-4fae-89d4-0a404bb1540d-1-1.dem"
parser = DemoParser(demo_path)

print(f"Listing updated fields in: {demo_path}")

try:
    fields = parser.list_updated_fields()
    print(f"Total fields found: {len(fields)}")
    
    print("\n--- Button/Input Related Fields ---")
    button_fields = [f for f in fields if "button" in f.lower() or "input" in f.lower() or "mask" in f.lower()]
    for f in button_fields:
        print(f)
        
    print("\n--- Movement Services Fields ---")
    movement_fields = [f for f in fields if "movement" in f.lower()]
    for f in movement_fields[:20]:
        print(f)

except Exception as e:
    print(f"Error: {e}")
