#!/usr/bin/env python
"""
This script performs a full test of the Watchmin application by:
1. Running a process with an intentional error
2. Using Watchmin to monitor and attempt to fix the process
"""

import os
import sys
import subprocess
import time
import argparse
import threading

def print_process_output(process, prefix):
    """Helper function to print process output in a separate thread"""
    def read_and_print(stream, prefix):
        for line in iter(stream.readline, ''):
            if line:
                print(f"{prefix}: {line.rstrip()}")
    
    stdout_thread = threading.Thread(
        target=read_and_print, 
        args=(process.stdout, f"{prefix} [stdout]")
    )
    stderr_thread = threading.Thread(
        target=read_and_print, 
        args=(process.stderr, f"{prefix} [stderr]")
    )
    
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    return stdout_thread, stderr_thread

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run a full test of Watchmin')
    parser.add_argument('--run-unittest', action='store_true', 
                        help='Run the unittest instead of direct demonstration')
    parser.add_argument('--debug', action='store_true',
                        help='Print more debug information')
    args = parser.parse_args()
    
    # Get the path to the Python executable
    python_exe = sys.executable
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.run_unittest:
        # Run the unittest version
        print("=== Running unittest version of the full test ===")
        unittest_cmd = [
            python_exe, 
            os.path.join(script_dir, "tests", "full_process_hook_test.py")
        ]
        
        process = subprocess.Popen(
            unittest_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Print output in real time
        stdout_thread, stderr_thread = print_process_output(process, "UNITTEST")
        
        # Wait for process to complete with timeout
        try:
            process.wait(timeout=45)  # 45 second timeout
            return process.returncode
        except subprocess.TimeoutExpired:
            print("ERROR: Test timed out after 45 seconds")
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
            return 1
    else:
        # Run the demonstration version
        print("=== Running direct demonstration of Watchmin ===")
        
        # Step 1: Start the error script as a separate process
        error_script_path = os.path.join(script_dir, "error_script.py")
        print(f"\n[1] Starting error script: {error_script_path}")
        
        # Use unbuffered output
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        error_process = subprocess.Popen(
            [python_exe, error_script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )
        
        # Start threads to print process output
        if args.debug:
            error_stdout_thread, error_stderr_thread = print_process_output(
                error_process, "ERROR_SCRIPT"
            )
        
        # Give it more time to start (3 seconds as in the error script)
        print("Waiting for error script to start...")
        time.sleep(2)
        
        # Step 2: Get the PID of the error process
        pid = error_process.pid
        print(f"Error script process started with PID: {pid}")
        
        # Check if the process is still running
        if error_process.poll() is not None:
            print(f"Error: Process exited too quickly with code {error_process.returncode}")
            return 1
            
        # Step 3: Use Watchmin to monitor the process
        print(f"\n[2] Using Watchmin to monitor process with PID: {pid}")
        
        watchmin_cmd = [
            python_exe, 
            os.path.join(script_dir, "main.py"),
            "--attach",
            str(pid)
        ]
        
        watchmin_process = subprocess.Popen(
            watchmin_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )
        
        # Start threads to print Watchmin output
        print("\n=== Watchmin Output ===")
        watchmin_stdout_thread, watchmin_stderr_thread = print_process_output(
            watchmin_process, "WATCHMIN"
        )
        
        # Wait longer for Watchmin to detect and fix the error (up to 15 seconds)
        timeout = 20
        print(f"Waiting up to {timeout} seconds for error detection and fix...")
        start_time = time.time()
        
        try:
            # Wait for error process to complete (it should exit after the error)
            error_process.wait(timeout=timeout)
            print(f"Error process exited with code: {error_process.returncode}")
            
            # Give Watchmin a moment to process the error
            time.sleep(2)
        except subprocess.TimeoutExpired:
            print("Warning: Error process did not exit within the timeout period")
        
        # Step 4: Clean up processes
        print("\n[3] Cleaning up processes")
        
        cleanup_timeout = 5
        print(f"Terminating processes with {cleanup_timeout}s timeout...")
        
        # Clean up error process
        if error_process.poll() is None:
            try:
                error_process.terminate()
                error_process.wait(timeout=cleanup_timeout)
            except subprocess.TimeoutExpired:
                print("Warning: Failed to terminate error process gracefully")
                try:
                    error_process.kill()
                    print("Force killed error process")
                except:
                    print("Failed to kill error process")
            
        # Clean up Watchmin process    
        if watchmin_process.poll() is None:
            try:
                watchmin_process.terminate()
                watchmin_process.wait(timeout=cleanup_timeout)
            except subprocess.TimeoutExpired:
                print("Warning: Failed to terminate Watchmin process gracefully")
                try:
                    watchmin_process.kill()
                    print("Force killed Watchmin process")
                except:
                    print("Failed to kill Watchmin process")
            
        print("\n=== Test Complete ===")
        
        return 0

if __name__ == "__main__":
    sys.exit(main()) 