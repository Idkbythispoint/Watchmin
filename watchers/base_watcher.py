import os
import sys
import psutil
import subprocess
import threading

def start_repair(error):
    
    pass

def establish_watcher(process_target):
    """
    Watches a process's output and calls start_repair when an error is detected.
    
    Args:
        process_target: The process to watch or start
    """
    
    # Function to monitor a stream for errors
    def monitor_stream(stream, process_name):
        for line in iter(stream.readline, ''):
            line = line.strip()
            # Simple error detection - you could make this more sophisticated
            if "error" in line.lower() or "exception" in line.lower():
                print(f"Error detected in {process_name}: {line}")
                start_repair(line)
    
    try:
        # Start the process and capture its output
        process = subprocess.Popen(
            process_target,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"Watching process: {process_target} (PID: {process.pid})")
        
        # Set up threads to monitor stdout and stderr
        stderr_thread = threading.Thread(
            target=monitor_stream,
            args=(process.stderr, f"stderr of {process_target}")
        )
        stderr_thread.daemon = True
        stderr_thread.start()
        
        # Wait for the process to complete
        process.wait()
        stderr_thread.join(timeout=1)
        
    except Exception as e:
        print(f"Error watching process: {e}")