#!/usr/bin/env python
# This script will intentionally raise a division by zero error

import time
import sys
import os

def main():
    print(f"Starting the error script... (PID: {os.getpid()})")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    # Wait longer to ensure the monitor can attach
    print("Waiting 3 seconds for monitor to attach...")
    sys.stdout.flush()
    time.sleep(3)
    
    try:
        # Here's our intentional error
        print("About to cause an error...")
        sys.stdout.flush()
        result = 10 / 0  # Division by zero error
        print(f"Result: {result}")  # This will never be executed
    except Exception as e:
        # Print the error to stderr
        error_message = f"Error: {e}"
        print(error_message, file=sys.stderr)
        print(error_message)  # Also print to stdout for easier monitoring
        sys.stderr.flush()
        sys.stdout.flush()
        
        # Wait a bit so the error can be detected and fixed
        print("Waiting after error...", file=sys.stderr)
        print("Waiting after error for 5 seconds...")
        sys.stderr.flush()
        sys.stdout.flush()
        time.sleep(5)
        
        print("Error script completed, exiting with status 1")
        sys.stdout.flush()
        # Exit with non-zero status
        sys.exit(1)

if __name__ == "__main__":
    main() 