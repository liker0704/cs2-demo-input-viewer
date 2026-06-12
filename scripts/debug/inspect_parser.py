from demoparser2 import DemoParser
import sys

demo_path = sys.argv[1] if len(sys.argv) > 1 else "demos/1-ff115b7a-c62d-4fae-89d4-0a404bb1540d-1-1.dem"
parser = DemoParser(demo_path)

print("Dir(parser):")
print(dir(parser))
