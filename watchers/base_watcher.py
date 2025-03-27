import os
import sys
import psutil
import subprocess
import threading
from collections import deque
import main

# Global dictionary to store output lines for each process
process_output_buffers = {}
# Default max lines to store in buffer
DEFAULT_BUFFER_SIZE = 100

def start_repair(error, logs):
    print(error)
    print(logs)
    
    pass

def get_logs(process_name, lines=None):
    # Get the number of lines from config or use default
    if lines is None:
        try:
            lines = main.ConfigHandler.get_config("lines_of_logs_to_give_llm")
        except (AttributeError, KeyError):
            lines = DEFAULT_BUFFER_SIZE
    
    # Extract the base process name if it contains "stdout of" or "stderr of"
    process_key = process_name
    if "stdout of " in process_name:
        process_key = process_name.replace("stdout of ", "")
    elif "stderr of " in process_name:
        process_key = process_name.replace("stderr of ", "")
        
    # Get the last X lines of output from the process buffer
    if process_key in process_output_buffers:
        buffer = list(process_output_buffers[process_key])
        # Take only the requested number of lines (or all if lines > buffer size)
        return "\n".join(buffer[-lines:])
    return f"No logs available for process: {process_name}"

def establish_watcher(process_target, buffer_size=None):
    """
    Watches a process's output and calls start_repair when an error is detected.
    
    Args:
        process_target: The process to watch or start
        buffer_size: Maximum number of output lines to keep in buffer
    """
    
    # Use config value for buffer size if not specified
    if buffer_size is None:
        try:
            buffer_size = main.ConfigHandler.get_config("lines_of_logs_to_give_llm")
        except (AttributeError, KeyError):
            buffer_size = DEFAULT_BUFFER_SIZE
    
    # Initialize buffer for this process
    process_output_buffers[process_target] = deque(maxlen=buffer_size)
    
    # Function to monitor a stream for errors
    def monitor_stream(stream, process_name):
        for line in iter(stream.readline, ''):
            line = line.strip()
            # Add line to the process buffer
            process_output_buffers[process_target].append(line)
            
            # Simple error detection - you could make this more sophisticated
            if "error" in line.lower() or "exception" in line.lower():
                print(f"Error detected in {process_name}: {line}")
                # Get the logs
                logs = get_logs(process_name)
                start_repair(line, logs)
    
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
        stdout_thread = threading.Thread(
            target=monitor_stream,
            args=(process.stdout, f"stdout of {process_target}")
        )
        stdout_thread.daemon = True
        stdout_thread.start()
        
        stderr_thread = threading.Thread(
            target=monitor_stream,
            args=(process.stderr, f"stderr of {process_target}")
        )
        stderr_thread.daemon = True
        stderr_thread.start()
        
        # Wait for the process to complete
        process.wait()
        # Wait for monitoring threads to finish without a short timeout
        stdout_thread.join()
        stderr_thread.join()
        
    except Exception as e:
        print(f"Error watching process: {e}")