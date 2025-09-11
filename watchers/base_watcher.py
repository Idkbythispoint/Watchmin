import os
import sys
import psutil
import subprocess
import threading
import time
from collections import deque
import json
from watchers.fixers.base_fixer import BaseFixer
from watchers.subwatchers.relavance_finder import find_relevant_code

# Global dictionary to store output lines for each process
process_output_buffers = {}
# Default max lines to store in buffer
DEFAULT_BUFFER_SIZE = 100
# Default maximum number of turns for LLM interactions
DEFAULT_MAX_TURNS = 20

class BaseWatcher:
    def __init__(self, process_target=None, buffer_size=None, pid=None, max_turns=None, config_handler=None, oai_client=None):
        """
        Initialize a watcher for a specific process.
        
        Args:
            process_target: The process command to start (if not attaching to existing)
            buffer_size: Maximum number of output lines to keep in buffer
            pid: Process ID to attach to (if already running)
            max_turns: Maximum number of interaction turns with LLM before giving up
            config_handler: Configuration handler instance
            oai_client: OpenAI client instance
        """
        self.process_target = process_target
        self.pid = pid
        self.config_handler = config_handler
        self.oai_client = oai_client
        
        # Use config value for buffer size if not specified
        if buffer_size is None:
            try:
                if self.config_handler:
                    buffer_size = self.config_handler.get_value("lines_of_logs_to_give_llm", DEFAULT_BUFFER_SIZE)
                else:
                    buffer_size = DEFAULT_BUFFER_SIZE
            except (AttributeError, KeyError):
                buffer_size = DEFAULT_BUFFER_SIZE
        
        # Use config value for max turns if not specified
        if max_turns is None:
            try:
                if self.config_handler:
                    max_turns = self.config_handler.get_value("max_turns", DEFAULT_MAX_TURNS)
                else:
                    max_turns = DEFAULT_MAX_TURNS
            except (AttributeError, KeyError):
                max_turns = DEFAULT_MAX_TURNS
                
        self.buffer_size = buffer_size
        self.max_turns = max_turns
        self.output_buffer = deque(maxlen=buffer_size)
        self.process = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.monitor_thread = None
        self.is_attached = False
        self.should_stop = False
        
        # If PID is provided, attach to the process immediately
        if pid:
            self.attach_to_process(pid)
    
    def start_repair(self, error, logs):
        """
        Handle errors detected in the watched process by attempting repairs
        
        Args:
            error: The error message detected
            logs: Recent logs from the process
        """
        print(f"Starting repair for error: {error}")
        print(f"Logs: {logs}")
        
        # Get the process ID for the fixer
        process_id = self.pid if self.is_attached else (self.process.pid if self.process else None)
        
        # If we don't have a valid process ID, we can't proceed
        if not process_id:
            print("Error: Cannot start repair without a valid process ID")
            return
        
        # Check if we have the required dependencies for repair
        if not self.config_handler:
            print("Warning: Cannot start repair without config handler")
            return
            
        # Lazy-load OpenAI client if not provided
        if not self.oai_client:
            try:
                # Import here to avoid circular dependency
                import main
                self.oai_client = main.get_oai_client()
            except Exception as e:
                print(f"Warning: Cannot load OpenAI client for repair: {e}")
                return
        
        # Find relevant code for the error
        try:
            relevance_data = json.loads(find_relevant_code(logs, self.oai_client, self.config_handler))
            print(f"Found relevant code: {relevance_data}")
            
            # Create a fixer instance
            fixer = BaseFixer(self.process_target, process_id, self.config_handler, self.oai_client)
            
            # If we have relevant code, read it
            relevant_code = ""
            if relevance_data.get("has_relevant_file", False):
                file_path = relevance_data.get("file_path")
                start_line = relevance_data.get("start_line")
                end_line = relevance_data.get("end_line")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if start_line >= 0 and end_line < len(lines):
                            relevant_code = ''.join(lines[start_line:end_line+1])
                except Exception as e:
                    print(f"Error reading relevant code: {e}")
            
            # Initialize turn counter
            turn_count = 0
            
            # Run the fixer with a turn limit
            # The loops runs until the LLM calls mark_as_fixed (which sets fixer.isfixed to True)
            # or until we reach max_turns
            while not fixer.isfixed and turn_count < self.max_turns:
                print(f"Starting repair turn {turn_count + 1}/{self.max_turns}")
                fixer.fix(error, logs, relevant_code)
                turn_count += 1
                
                # If we've reached max turns without fixing, log this
                if turn_count >= self.max_turns and not fixer.isfixed:
                    print(f"Reached maximum number of turns ({self.max_turns}) without fixing the issue.")
                    break
            
            # Report outcome
            if fixer.isfixed:
                print(f"Error fixed after {turn_count} turns")
            else:
                print(f"Failed to fix error after {turn_count} turns")
                
        except Exception as e:
            print(f"Error during repair process: {e}")
            import traceback
            traceback.print_exc()
    
    def get_logs(self, stream_type=None, lines=None):
        """
        Get the logs from the process buffer.
        
        Args:
            stream_type: Optional; 'stdout' or 'stderr' to specify which stream
            lines: Number of log lines to return
            
        Returns:
            String containing the last X lines of logs
        """
        # Get the number of lines from config or use default
        if lines is None:
            try:
                if self.config_handler:
                    lines = self.config_handler.get_value("lines_of_logs_to_give_llm", self.buffer_size)
                else:
                    lines = self.buffer_size
            except (AttributeError, KeyError):
                lines = self.buffer_size
        
        # Return the last X lines from the buffer
        if self.output_buffer:
            buffer = list(self.output_buffer)
            return "\n".join(buffer[-lines:])
        
        process_id = self.pid if self.is_attached else (self.process.pid if self.process else None)
        return f"No logs available for process: {self.process_target or process_id}"
    
    def monitor_stream(self, stream, stream_type):
        """
        Monitor a stream for output and errors.
        
        Args:
            stream: The stream to monitor (stdout or stderr)
            stream_type: String identifier for the stream ('stdout' or 'stderr')
        """
        for line in iter(stream.readline, ''):
            line = line.strip()
            # Add line to the process buffer
            self.output_buffer.append(f"[{stream_type}] {line}")
            
            # Simple error detection - you could make this more sophisticated
            if "error" in line.lower() or "exception" in line.lower() or "traceback" in line.lower():
                process_id = self.pid if self.is_attached else (self.process.pid if self.process else None)
                print(f"Error detected in {self.process_target or process_id} {stream_type}: {line}")
                # Get the logs
                logs = self.get_logs()
                self.start_repair(line, logs)
    
    def attach_to_process(self, pid):
        """
        Attach to an existing process by PID
        
        Args:
            pid: Process ID to attach to
            
        Returns:
            bool: True if successfully attached, False otherwise
        """
        try:
            # Check if process exists
            process = psutil.Process(pid)
            self.pid = pid
            self.is_attached = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(
                target=self.monitor_attached_process,
                args=(process,)
            )
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            print(f"Attached to process: {pid} ({process.name()})")
            return True
            
        except psutil.NoSuchProcess:
            print(f"Error: Process with PID {pid} does not exist")
            return False
        except Exception as e:
            print(f"Error attaching to process: {e}")
            return False
    
    def monitor_attached_process(self, process):
        """Monitor a process that was attached to rather than started by us"""
        self.should_stop = False
        
        # Add initial process info to buffer
        try:
            cmd = process.cmdline()
            self.output_buffer.append(f"[attached] Monitoring process: {process.pid} ({process.name()})")
            self.output_buffer.append(f"[attached] Command: {' '.join(cmd)}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.output_buffer.append(f"[attached] Process {process.pid} no longer exists or access denied")
            self.is_attached = False
            return
            
        # Check if we can find log files for this process
        log_files = self.find_process_log_files(process)
        log_file_watchers = []
        
        # Set up log file watching if any were found
        for log_file in log_files:
            thread = threading.Thread(
                target=self.monitor_log_file,
                args=(log_file,)
            )
            thread.daemon = True
            thread.start()
            log_file_watchers.append(thread)
        
        # Monitor process status and resource usage
        while not self.should_stop:
            try:
                if not process.is_running():
                    # Check exit status for errors
                    try:
                        exit_code = process.wait()  # Get the exit code
                        self.output_buffer.append(f"[attached] Process {process.pid} has terminated with exit code {exit_code}")
                        
                        # If process exited with non-zero status, treat as potential error
                        if exit_code != 0:
                            error_message = f"Process terminated with exit code {exit_code}"
                            self.output_buffer.append(f"[attached] Error detected: {error_message}")
                            print(f"Error detected in attached process {process.pid}: {error_message}")
                            logs = self.get_logs()
                            self.start_repair(error_message, logs)
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        self.output_buffer.append(f"[attached] Process {process.pid} has terminated")
                    break
                    
                # Check recent output buffer entries for errors
                if len(self.output_buffer) > 0:
                    # Check last few entries for errors
                    recent_entries = list(self.output_buffer)[-5:]  # Check last 5 entries
                    for entry in recent_entries:
                        if ("error" in entry.lower() or "exception" in entry.lower() or 
                            "traceback" in entry.lower()) and "[attached]" not in entry.lower():
                            # Make sure we haven't already processed this error
                            if not hasattr(self, '_last_error_entry') or self._last_error_entry != entry:
                                self._last_error_entry = entry
                                print(f"Error detected in attached process {process.pid}: {entry}")
                                logs = self.get_logs()
                                self.start_repair(entry, logs)
                    
                # Collect process metrics
                try:
                    cpu_percent = process.cpu_percent(interval=0.1)
                    memory_info = process.memory_info()
                    
                    # Only add to buffer if values are significant
                    if cpu_percent > 80:  # High CPU usage
                        self.output_buffer.append(f"[attached] High CPU: {cpu_percent}% for {process.pid}")
                    
                    # Check for potential memory leaks (only log significant increases)
                    if hasattr(self, 'last_memory_usage'):
                        memory_increase = memory_info.rss - self.last_memory_usage
                        # Log if memory increased by more than 10MB
                        if memory_increase > 10 * 1024 * 1024:  
                            self.output_buffer.append(f"[attached] Memory increased by {memory_increase/1024/1024:.2f} MB")
                    
                    self.last_memory_usage = memory_info.rss
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # Check for process exceptions or crashes
                try:
                    status = process.status()
                    if status == psutil.STATUS_ZOMBIE:
                        self.output_buffer.append(f"[attached] Process {process.pid} is in zombie state")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
                time.sleep(1)
                
            except psutil.NoSuchProcess:
                self.output_buffer.append(f"[attached] Process {process.pid} has terminated")
                break
            except Exception as e:
                self.output_buffer.append(f"[attached] Error monitoring process: {e}")
                time.sleep(5)  # Back off on errors
        
        # Wait for log file watchers to finish
        for thread in log_file_watchers:
            thread.join(timeout=1)
            
        self.is_attached = False
    
    def find_process_log_files(self, process):
        """Find log files that might be associated with the process"""
        log_files = []
        
        try:
            # Check open files
            for open_file in process.open_files():
                if '.log' in open_file.path.lower() or 'log' in open_file.path.lower():
                    log_files.append(open_file.path)
            
            # Check process working directory for log files
            try:
                proc_cwd = process.cwd()
                for root, _, files in os.walk(proc_cwd):
                    for file in files:
                        if '.log' in file.lower():
                            log_files.append(os.path.join(root, file))
            except (psutil.AccessDenied, PermissionError):
                pass
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
        return log_files
    
    def monitor_log_file(self, log_file):
        """Monitor a log file for changes and errors"""
        try:
            # Get current file size
            file_size = os.path.getsize(log_file)
            
            self.output_buffer.append(f"[log] Monitoring log file: {log_file}")
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Move to the end of file
                f.seek(file_size)
                
                while not self.should_stop:
                    line = f.readline()
                    if line:
                        line = line.strip()
                        self.output_buffer.append(f"[log] {line}")
                        
                        # Check for errors
                        if "error" in line.lower() or "exception" in line.lower():
                            print(f"Error detected in log file {log_file}: {line}")
                            logs = self.get_logs()
                            self.start_repair(line, logs)
                    else:
                        # No new data, sleep briefly
                        time.sleep(0.1)
        except Exception as e:
            self.output_buffer.append(f"[log] Error monitoring log file {log_file}: {e}")
    
    def start(self):
        """Start watching the process"""
        if self.is_attached:
            print(f"Already attached to process with PID {self.pid}")
            return self.pid
            
        if not self.process_target:
            print("Error: No process target specified")
            return None
            
        try:
            # Start the process and capture its output
            self.process = subprocess.Popen(
                self.process_target,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            print(f"Watching process: {self.process_target} (PID: {self.process.pid})")
            
            # Set up threads to monitor stdout and stderr
            self.stdout_thread = threading.Thread(
                target=self.monitor_stream,
                args=(self.process.stdout, "stdout")
            )
            self.stdout_thread.daemon = True
            self.stdout_thread.start()
            
            self.stderr_thread = threading.Thread(
                target=self.monitor_stream,
                args=(self.process.stderr, "stderr")
            )
            self.stderr_thread.daemon = True
            self.stderr_thread.start()
            
            return self.process.pid
            
        except Exception as e:
            print(f"Error watching process: {e}")
            return None
    
    def wait(self):
        """Wait for the watched process and monitoring threads to complete"""
        if self.process:
            # Wait for the process to complete
            self.process.wait()
            # Wait for monitoring threads to finish
            if self.stdout_thread:
                self.stdout_thread.join()
            if self.stderr_thread:
                self.stderr_thread.join()
        elif self.is_attached and self.monitor_thread:
            # Wait for attached process monitoring to complete
            self.monitor_thread.join()
    
    def stop(self):
        """Stop the watched process or monitoring"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                # Give it some time to terminate gracefully
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                self.process.kill()
        
        if self.is_attached:
            # Stop monitoring but don't terminate the process
            self.should_stop = True
            self.is_attached = False
            print(f"Stopped monitoring process with PID {self.pid}")

# Legacy function to maintain backward compatibility
def establish_watcher(process_target, buffer_size=None):
    """Legacy function that creates and starts a BaseWatcher instance"""
    # Import here to avoid circular dependency
    import main
    config_handler = main.get_config_handler()
    watcher = BaseWatcher(process_target, buffer_size, config_handler=config_handler)
    watcher.start()
    return watcher

# Legacy function to maintain backward compatibility
def get_logs(process_name, lines=None):
    """Legacy function - this will only work with the last watcher created"""
    print("Warning: Using legacy get_logs function. Please use BaseWatcher instances directly.")
    # This is just a placeholder and won't work well with multiple watchers
    return f"Legacy get_logs function called for {process_name}. Please use BaseWatcher instances directly."