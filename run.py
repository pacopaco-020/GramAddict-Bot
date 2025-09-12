import platform
import os
import sys
import argparse

# Architecture self-correction for macOS
def test_import():
    """Test if we can import Instamatic without architecture issues"""
    try:
        import Instamatic
        return True
    except ImportError as e:
        if "incompatible architecture" in str(e) or "have 'arm64', need 'x86_64'" in str(e):
            return False
        else:
            # Re-raise if it's not an architecture issue
            raise

if sys.platform == "darwin":
    # Only force x86_64 if explicitly requested via environment variable
    if os.environ.get("FORCE_X86_64", "false").lower() == "true" and platform.machine() != "x86_64":
        print("FORCE_X86_64 set. Relaunching with x86_64...")
        os.execvp("arch", ["arch", "-x86_64", sys.executable] + sys.argv)
    
    print(f"Running on {platform.machine()} architecture")

import Instamatic

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("command", help="Command to run")
parser.add_argument("--config", help="Path to config file")
parser.add_argument("--device", help="Device ID")
args = parser.parse_args()

# Pass arguments to Instamatic
Instamatic.run()