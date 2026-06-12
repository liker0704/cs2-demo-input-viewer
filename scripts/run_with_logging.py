"""
Run production mode with file logging.
"""
import sys
import logging
from datetime import datetime

# Setup file logging
log_filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

print(f"Logging to: {log_filename}")
print("="*80)

# Monkey patch print to also log
original_print = print
def logged_print(*args, **kwargs):
    message = ' '.join(str(arg) for arg in args)
    logging.info(message)
    original_print(*args, **kwargs)

import builtins
builtins.print = logged_print

# Now run the main app
from src.main import main
main()
