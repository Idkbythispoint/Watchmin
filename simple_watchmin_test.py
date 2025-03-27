#!/usr/bin/env python
"""
Simple demonstration of Watchmin's functionality:
1. Starts an error-prone process
2. Uses Watchmin to monitor the process
3. Checks if errors are detected and handled
"""

import os
import sys
import subprocess
import time
import threading
import signal
import re

def print_process_output(process, prefix):
    """Print process output in real-time with prefixes"""
    def read_stream(stream, prefix_str):
        for line in iter(stream.readline, ''):
            if line:
                print(f"{prefix_str}: {line.rstrip()}")

    stdout_thread = threading.Thread(
        target=read_stream,
        args=(process.stdout, f"{prefix} [stdout]")
    )
    stderr_thread = threading.Thread(
        target=read_stream,
        args=(process.stderr, f"{prefix} [stderr]")
    )
    
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    return stdout_thread, stderr_thread

def capture_process_output(process, results):
    """Capture process output to a list for later analysis"""
    def capture_stream(stream, output_list, source):
        for line in iter(stream.readline, ''):
            if line:
                output_list.append((source, line.rstrip()))

    stdout_thread = threading.Thread(
        target=capture_stream,
        args=(process.stdout, results, "stdout")
    )
    stderr_thread = threading.Thread(
        target=capture_stream,
        args=(process.stderr, results, "stderr")
    )
    
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    return stdout_thread, stderr_thread

def main():
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable
    
    # Path to the error script 
    error_script_path = os.path.join(script_dir, "error_script.py")
    
    # Make sure error script exists
    if not os.path.exists(error_script_path):
        print(f"Error: Script not found at {error_script_path}")
        return 1
    
    # Set unbuffered output
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    # Lists to store output for analysis
    error_output = []
    watchmin_output = []
    
    print("\n===== WATCHMIN DEMONSTRATION =====")
    print("1. Starting error script...")
    
    # Start the error script
    error_process = subprocess.Popen(
        [python_exe, error_script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env
    )
    
    # Print and capture error script output
    error_threads = print_process_output(error_process, "ERROR_SCRIPT")
    capture_threads = capture_process_output(error_process, error_output)
    
    # Wait for it to start
    print("   Waiting for error script to initialize...")
    time.sleep(2)
    
    # Get the PID
    error_pid = error_process.pid
    print(f"   Error script running with PID: {error_pid}")
    
    # Check if process is still running
    if error_process.poll() is not None:
        print(f"Error: Process exited prematurely with code {error_process.returncode}")
        return 1
    
    # Step 2: Start Watchmin to monitor the process
    print("\n2. Starting Watchmin to monitor the process...")
    
    watchmin_cmd = [
        python_exe,
        os.path.join(script_dir, "main.py"),
        "--attach",
        str(error_pid)
    ]
    
    watchmin_process = subprocess.Popen(
        watchmin_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env
    )
    
    # Print and capture Watchmin output
    watchmin_threads = print_process_output(watchmin_process, "WATCHMIN")
    watchmin_capture = capture_process_output(watchmin_process, watchmin_output)
    
    # Step 3: Wait for the error detection and handling
    print("\n3. Waiting for error detection and handling...")
    
    # Wait up to 30 seconds for the processes to finish
    timeout = 30
    print(f"   (Timeout: {timeout} seconds)")
    
    start_time = time.time()
    error_detected = False
    repair_attempted = False
    
    try:
        while time.time() - start_time < timeout:
            # Check if error process has exited
            if error_process.poll() is not None:
                print(f"\n4. Error process exited with code: {error_process.returncode}")
                break
                
            # Check output for error detection
            for source, line in watchmin_output:
                if "Error detected" in line and not error_detected:
                    error_detected = True
                    print("\n   >>> Error detected by Watchmin!")
                if "Starting repair" in line and not repair_attempted:
                    repair_attempted = True
                    print("   >>> Repair process initiated!")
                if "Error fixed" in line:
                    print("   >>> Error has been fixed!")
            
            # If Watchmin detects and fixes the error, we'll see in the output
            time.sleep(1)
        
        # Give a moment for any final output
        time.sleep(2)
        
        # Step 5: Clean up processes
        print("\n5. Cleaning up processes...")
        
        # Terminate error process if still running
        if error_process.poll() is None:
            print("   Terminating error process...")
            error_process.terminate()
            try:
                error_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("   Force killing error process...")
                error_process.kill()
        
        # Terminate Watchmin process
        if watchmin_process.poll() is None:
            print("   Terminating Watchmin process...")
            watchmin_process.terminate()
            try:
                watchmin_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("   Force killing Watchmin process...")
                watchmin_process.kill()
        
        # Analyze and report results
        print("\n===== TEST RESULTS =====")
        
        # Check if error occurred
        error_occurred = any("Error: division by zero" in line for _, line in error_output)
        
        # Check Watchmin output
        error_detected = any("Error detected" in line for _, line in watchmin_output)
        repair_attempted = any("Starting repair" in line for _, line in watchmin_output)
        error_fixed = any("Error fixed" in line for _, line in watchmin_output)
        
        # Print summary
        print(f"Error occurred in script:  {'✅ Yes' if error_occurred else '❌ No'}")
        print(f"Error detected by Watchmin: {'✅ Yes' if error_detected else '❌ No'}")
        print(f"Repair process attempted:  {'✅ Yes' if repair_attempted else '❌ No'}")
        print(f"Error reported as fixed:   {'✅ Yes' if error_fixed else '❌ No'}")
        
        # If error was not detected, explain possible reasons
        if not error_detected and error_occurred:
            print("\nPossible reasons for Watchmin not detecting the error:")
            print("1. The error string might not match the pattern Watchmin is looking for")
            print("2. The error might be in stderr but Watchmin is only monitoring stdout")
            print("3. There might be a timing issue with the process termination")
            print("\nTo improve error detection, you could modify watchers/base_watcher.py")
            print("to enhance the error detection patterns or add custom error handlers.")
        
        print("\n===== DEMONSTRATION COMPLETE =====")
        return 0
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user. Cleaning up...")
        
        # Terminate processes
        for p in [error_process, watchmin_process]:
            if p and p.poll() is None:
                try:
                    p.terminate()
                    p.wait(timeout=2)
                except:
                    try:
                        p.kill()
                    except:
                        pass
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 