import os
import subprocess
import sys
import threading
import time

class ToolsHandler:
    @staticmethod
    def run_shell_command(command, timeout):
        """
        Run a shell command with a timeout.
        
        Args:
            command (str): The shell command to execute
            timeout (int): Maximum seconds to wait for completion
            
        Returns:
            dict: Result of the command execution
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            return {
                "success": process.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": ""
            }
    
    @staticmethod
    def run_python_code(code, timeout):
        """
        Execute Python code with a timeout.
        
        Args:
            code (str): Python code to execute
            timeout (int): Maximum seconds to wait for completion
            
        Returns:
            dict: Result of the code execution
        """
        # Create a temporary file to store the code
        temp_file = "temp_code_execution.py"
        try:
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Create a dictionary to store results from the thread
            result = {"stdout": "", "stderr": "", "success": False, "error": None}
            
            # Define a function to run in a separate thread
            def run_code():
                try:
                    process = subprocess.Popen(
                        [sys.executable, temp_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate()
                    result["stdout"] = stdout
                    result["stderr"] = stderr
                    result["success"] = process.returncode == 0
                    result["returncode"] = process.returncode
                except Exception as e:
                    result["success"] = False
                    result["error"] = str(e)
            
            # Create and start thread
            thread = threading.Thread(target=run_code)
            thread.daemon = True
            thread.start()
            
            # Wait for the thread with timeout
            thread.join(timeout)
            
            # If thread is still alive after timeout, the execution took too long
            if thread.is_alive():
                return {
                    "success": False,
                    "error": f"Code execution timed out after {timeout} seconds",
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", "")
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": ""
            }
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    @staticmethod
    def mark_as_fixed(fixed):
        """
        Mark an issue as fixed or ignorable.
        
        Args:
            fixed (bool): True if fixed, False if ignorable
            
        Returns:
            dict: Status of the operation
        """
        return {
            "success": True,
            "fixed": fixed,
            "message": "Issue marked as fixed" if fixed else "Issue marked as ignorable"
        }
    
    @staticmethod
    def read_file(file_path, line_start, line_end):
        """
        Read content from a file with specified line range.
        
        Args:
            file_path (str): Path to the file to read
            line_start (int): Starting line number (0-indexed)
            line_end (int): Ending line number (0-indexed), -1 for end of file
            
        Returns:
            dict: File content and status
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
                
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Handle special case where line_end is -1
            if line_end == -1:
                line_end = len(lines) - 1
                
            # Validate line ranges
            if line_start < 0:
                line_start = 0
            if line_end >= len(lines):
                line_end = len(lines) - 1
                
            # Extract requested lines
            selected_lines = lines[line_start:line_end+1]
            content = ''.join(selected_lines)
            
            return {
                "success": True,
                "content": content,
                "total_lines": len(lines),
                "lines_read": len(selected_lines)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def edit_file(file_path, line_start, line_end, new_content):
        """
        Edit a file by replacing specified lines with new content.
        
        Args:
            file_path (str): Path to the file to edit
            line_start (int): Starting line number (0-indexed)
            line_end (int): Ending line number (0-indexed), -1 for end of file
            new_content (str): Content to replace the specified lines
            
        Returns:
            dict: Status of the edit operation
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
                
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Handle special case where line_end is -1
            if line_end == -1:
                line_end = len(lines) - 1
                
            # Validate line ranges
            if line_start < 0:
                line_start = 0
            if line_end >= len(lines):
                line_end = len(lines) - 1
                
            # Split new_content into lines, ensuring each line ends with newline
            new_lines = new_content.split('\n')
            if new_content.endswith('\n'):
                new_lines = new_lines[:-1]
            
            new_lines_with_newlines = [line + '\n' for line in new_lines[:-1]]
            if new_lines:
                if lines and not lines[-1].endswith('\n'):
                    new_lines_with_newlines.append(new_lines[-1])
                else:
                    new_lines_with_newlines.append(new_lines[-1] + '\n')
            
            # Replace lines in the file
            before = lines[:line_start]
            after = lines[line_end+1:]
            updated_lines = before + new_lines_with_newlines + after
            
            # Write back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            return {
                "success": True,
                "message": f"Successfully edited {file_path}",
                "lines_replaced": line_end - line_start + 1,
                "new_lines_count": len(new_lines_with_newlines)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
