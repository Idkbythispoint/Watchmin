import unittest
import sys
import os
import platform
import subprocess
import time
import threading
import tempfile
import signal
import json
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a mock ConfigHandler class
class MockConfigHandler:
    def __init__(self, *args, **kwargs):
        pass
        
    def get_value(self, key, default=None):
        # For testing, we'll just return a fixed value
        if key == "lines_of_logs_to_give_llm":
            return 100
        elif key == "model_for_fixer":
            return "gpt-4o-mini"
        elif key == "max_turns":
            return 5  # Use a small value for testing
        elif key == "fixer_prompt":
            return "You are a helpful assistant that fixes code errors."
        return default

# Patch the ConfigHandler before importing any modules that use it
import internal.confighandler as confighandler
original_ConfigHandler = confighandler.ConfigHandler
confighandler.ConfigHandler = MockConfigHandler

# Now import other modules
import main
from main import find_process
import watchers.base_watcher as base_watcher
import psutil
from watchers.fixers.base_fixer import BaseFixer
from watchers.fixers.tools_handler import ToolsHandler

def is_wsl():
    """Check if running under Windows Subsystem for Linux"""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except:
        return False

# Configure the mock ConfigHandler for the modules that need it

class TestProcessFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up for the tests"""
        if sys.platform == 'win32' and not is_wsl():
            print("WARNING: This application is meant to be run on Linux or WSL.")
            print("For best results, please run these tests using Windows Subsystem for Linux (WSL).")
    
    def test_find_process_by_name(self):
        """Test finding a process by name"""
        # Find a common process that should be running
        if sys.platform == 'win32' and not is_wsl():
            process_name = 'explorer'
        else:
            # Linux or WSL
            process_name = 'systemd'
            
        process = find_process(process_name=process_name)
        self.assertIsNotNone(process, f"Should find the {process_name} process")
        self.assertIsInstance(process, psutil.Process)
        
    def test_find_process_nonexistent(self):
        """Test finding a nonexistent process"""
        process = find_process(process_name="nonexistentprocessnamethatdoesnotexist12345")
        self.assertIsNone(process, "Should return None for nonexistent process")
    
    def test_find_process_by_pid(self):
        """Test finding a process by PID"""
        # Get current process PID
        current_pid = str(os.getpid())
        process = find_process(pid=current_pid)
        self.assertIsNotNone(process, "Should find the current process by PID")
        self.assertIsInstance(process, psutil.Process)
        self.assertEqual(process.pid, int(current_pid))

class TestBaseWatcher(unittest.TestCase):
    """Basic tests for the BaseWatcher class"""
    
    def setUp(self):
        """Set up test environment"""
        # Store the python executable path
        self.python_exe = sys.executable
    
    def test_watcher_init(self):
        """Test initializing a BaseWatcher"""
        # Test with buffer_size explicitly provided
        watcher = base_watcher.BaseWatcher(process_target="echo test", buffer_size=50)
        self.assertEqual(watcher.process_target, "echo test")
        self.assertEqual(watcher.buffer_size, 50)
        self.assertIsNone(watcher.pid)
        self.assertFalse(watcher.is_attached)
        
    def test_start_process(self):
        """Test starting a process with BaseWatcher"""
        # Use a simple echo command
        cmd = f"{self.python_exe} -c \"print('Test output'); import time; time.sleep(0.5)\""
        watcher = base_watcher.BaseWatcher(process_target=cmd, buffer_size=50)
        
        # Start the process
        pid = watcher.start()
        
        # Check that we got a PID
        self.assertIsNotNone(pid)
        self.assertTrue(pid > 0)
        
        # Wait for process to complete
        watcher.wait()
        
        # Check logs
        logs = watcher.get_logs()
        self.assertTrue("Test output" in logs)

    def test_error_detection(self):
        """Test error detection in process output"""
        # Create a BaseWatcher with a patched start_repair method
        mock_start_repair = MagicMock()
        with patch.object(base_watcher.BaseWatcher, 'start_repair', mock_start_repair):
            # Start a process that will output an error
            cmd = f"{self.python_exe} -c \"import sys; print('Normal output'); sys.stderr.write('Error: test error\\n'); sys.stdout.flush(); sys.stderr.flush()\""
            watcher = base_watcher.BaseWatcher(process_target=cmd, buffer_size=50)
            
            # Start the process
            watcher.start()
            
            # Wait for process to complete
            watcher.wait()
            
            # Check that start_repair was called
            mock_start_repair.assert_called()
            
            # Extract the args from the call
            call_args = mock_start_repair.call_args[0]
            
            # Verify error message is in the first argument
            self.assertTrue("Error: test error" in call_args[0])

class TestMainFunctions(unittest.TestCase):
    """Tests for functions in main.py"""
    
    def setUp(self):
        """Set up test environment"""
        # Import the module to ensure it's loaded
        import main
        
        # Store the original active_watchers
        self.original_active_watchers = dict(main.active_watchers)
        # Clear active_watchers for tests
        main.active_watchers.clear()
        
        # Script file for testing
        self.script_file = tempfile.NamedTemporaryFile(delete=False, suffix='.py')
        script_content = """
import time
print("Test script running")
time.sleep(0.5)
print("Test script completed")
"""
        self.script_file.write(script_content.encode('utf-8'))
        self.script_path = self.script_file.name
        self.script_file.close()
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original active_watchers
        import main
        main.active_watchers.clear()
        main.active_watchers.update(self.original_active_watchers)
        
        # Delete temporary files
        try:
            os.unlink(self.script_path)
        except:
            pass
    
    def test_watch_new_process(self):
        """Test creating a watcher for a new process"""
        # Create a command that will run for a little while
        cmd = f"{sys.executable} {self.script_path}"
        
        # Import here to make sure we use the patched version
        from main import watch_new_process
        
        # Watch the process
        watcher_id = watch_new_process(cmd)
        
        # Check that a watcher was created
        self.assertIsNotNone(watcher_id)
        
        # Get the watcher
        import main
        self.assertTrue(watcher_id in main.active_watchers)
        watcher = main.active_watchers[watcher_id]
        
        # Check watcher properties
        self.assertEqual(watcher.process_target, cmd)
        self.assertFalse(watcher.is_attached)
        
        # Clean up
        from main import stop_watcher
        stop_watcher(watcher_id)
    
    def test_stop_watcher(self):
        """Test stopping a watcher"""
        # Create a command that will run for a little while
        cmd = f"{sys.executable} -c \"import time; time.sleep(2)\""
        
        # Import here to make sure we use the patched version
        from main import watch_new_process, stop_watcher
        
        # Watch the process
        watcher_id = watch_new_process(cmd)
        
        # Check that a watcher was created
        import main
        self.assertTrue(watcher_id in main.active_watchers)
        
        # Stop the watcher
        stop_watcher(watcher_id)
        
        # Check that the watcher was removed
        self.assertFalse(watcher_id in main.active_watchers)

class TestToolsHandler(unittest.TestCase):
    """Tests for the ToolsHandler class"""
    
    def setUp(self):
        """Set up test environment"""
        self.tools_handler = ToolsHandler()
        
        # Create a temporary test file
        self.test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        self.test_file_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
        self.test_file.write(self.test_file_content.encode('utf-8'))
        self.test_file_path = self.test_file.name
        self.test_file.close()
    
    def tearDown(self):
        """Clean up after tests"""
        # Delete temporary files
        try:
            os.unlink(self.test_file_path)
        except:
            pass
    
    def test_run_shell_command_success(self):
        """Test running a successful shell command"""
        if sys.platform == 'win32':
            result = self.tools_handler.run_shell_command("echo Hello World", 5)
        else:
            result = self.tools_handler.run_shell_command("echo 'Hello World'", 5)
        
        self.assertTrue(result["success"])
        self.assertIn("Hello World", result["stdout"])
        self.assertEqual(result["returncode"], 0)
    
    def test_run_shell_command_failure(self):
        """Test running a failing shell command"""
        result = self.tools_handler.run_shell_command("thiscommandprobablydoesnotexist xyz", 5)
        self.assertFalse(result["success"])
        self.assertNotEqual(result["returncode"], 0)
    
    def test_run_shell_command_timeout(self):
        """Test shell command timeout"""
        if sys.platform == 'win32':
            cmd = "ping -n 10 127.0.0.1"
        else:
            cmd = "sleep 10"
            
        result = self.tools_handler.run_shell_command(cmd, 1)
        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"])
    
    def test_run_python_code_success(self):
        """Test running successful Python code"""
        code = "print('Hello from Python')"
        result = self.tools_handler.run_python_code(code, 5)
        
        self.assertTrue(result["success"])
        self.assertIn("Hello from Python", result["stdout"])
        self.assertEqual(result["returncode"], 0)
    
    def test_run_python_code_error(self):
        """Test running Python code with errors"""
        code = "print(undefined_variable)"
        result = self.tools_handler.run_python_code(code, 5)
        
        self.assertFalse(result["success"])
        self.assertNotEqual(result["returncode"], 0)
        self.assertIn("NameError", result["stderr"])
    
    def test_run_python_code_timeout(self):
        """Test Python code execution timeout"""
        code = "import time; time.sleep(10)"
        result = self.tools_handler.run_python_code(code, 1)
        
        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"])
    
    def test_mark_as_fixed_true(self):
        """Test marking as fixed"""
        result = self.tools_handler.mark_as_fixed(True)
        
        self.assertTrue(result["success"])
        self.assertTrue(result["fixed"])
        self.assertIn("fixed", result["message"])
    
    def test_mark_as_fixed_false(self):
        """Test marking as ignorable"""
        result = self.tools_handler.mark_as_fixed(False)
        
        self.assertTrue(result["success"])
        self.assertFalse(result["fixed"])
        self.assertIn("ignorable", result["message"])
    
    def test_read_file_success(self):
        """Test reading a file successfully"""
        result = self.tools_handler.read_file(self.test_file_path, 1, 3)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "Line 2\nLine 3\nLine 4\n")
        self.assertEqual(result["total_lines"], 5)
        self.assertEqual(result["lines_read"], 3)
    
    def test_read_file_end_of_file(self):
        """Test reading a file to the end"""
        result = self.tools_handler.read_file(self.test_file_path, 2, -1)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "Line 3\nLine 4\nLine 5\n")
        self.assertEqual(result["total_lines"], 5)
        self.assertEqual(result["lines_read"], 3)
    
    def test_read_file_not_found(self):
        """Test reading a nonexistent file"""
        result = self.tools_handler.read_file("nonexistent_file.txt", 0, 5)
        
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])
    
    def test_edit_file_success(self):
        """Test editing a file successfully"""
        result = self.tools_handler.edit_file(self.test_file_path, 1, 3, "New Line 2\nNew Line 3\nNew Line 4")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["lines_replaced"], 3)
        
        # Verify file contents
        with open(self.test_file_path, 'r') as f:
            content = f.read()
        
        expected_content = "Line 1\nNew Line 2\nNew Line 3\nNew Line 4\nLine 5\n"
        self.assertEqual(content, expected_content)
    
    def test_edit_file_not_found(self):
        """Test editing a nonexistent file"""
        result = self.tools_handler.edit_file("nonexistent_file.txt", 0, 5, "New content")
        
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])

class TestBaseFixer(unittest.TestCase):
    """Tests for the BaseFixer class"""
    
    def setUp(self):
        """Set up test environment"""
        # We're not mocking the OAIClient anymore to allow real API calls
        # But save original value of the model name for teardown
        self.original_model = confighandler.ConfigHandler().get_value("model_for_fixer")
        
        # Create mock config handler and oai client for testing
        self.mock_config = MockConfigHandler()
        self.mock_oai_client = MagicMock()
        
        # Create a sample BaseFixer for testing
        self.fixer = BaseFixer(process_target="test_target", pid=12345, 
                              config_handler=self.mock_config, 
                              oai_client=self.mock_oai_client)
        
        # Create a temporary test file
        self.test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.py')
        self.test_file_content = "def main():\n    result = 'Hello ' + 42\n    print(result)\n\nif __name__ == '__main__':\n    main()\n"
        self.test_file.write(self.test_file_content.encode('utf-8'))
        self.test_file_path = self.test_file.name
        self.test_file.close()
        
    def tearDown(self):
        """Clean up after tests"""
        # Delete temporary files
        try:
            os.unlink(self.test_file_path)
        except:
            pass
    
    def test_fixer_init(self):
        """Test initializing a BaseFixer"""
        fixer = BaseFixer(process_target="test_target", pid=12345)
        self.assertEqual(fixer.process_target, "test_target")
        self.assertEqual(fixer.pid, 12345)
        self.assertFalse(fixer.isfixed)
    
    def test_execute_tool_run_shell_command(self):
        """Test _execute_tool with run_shell_command"""
        # Create a mock for run_shell_command
        with patch.object(ToolsHandler, 'run_shell_command') as mock_run_shell_command:
            # Configure the mock
            mock_run_shell_command.return_value = {"success": True, "stdout": "test output"}
            
            # Call the function
            result = self.fixer._execute_tool("run_shell_command", {"command": "echo test", "timeout": 5})
            
            # Verify the correct method was called with correct arguments
            mock_run_shell_command.assert_called_with("echo test", 5)
            self.assertEqual(result, {"success": True, "stdout": "test output"})
    
    def test_execute_tool_run_python_code(self):
        """Test _execute_tool with run_python_code"""
        # Create a mock for run_python_code
        with patch.object(ToolsHandler, 'run_python_code') as mock_run_python_code:
            # Configure the mock
            mock_run_python_code.return_value = {"success": True, "stdout": "Hello from Python"}
            
            # Call the function
            result = self.fixer._execute_tool("run_python_code", {"code": "print('Hello from Python')", "timeout": 5})
            
            # Verify the correct method was called
            mock_run_python_code.assert_called_with("print('Hello from Python')", 5)
            self.assertEqual(result, {"success": True, "stdout": "Hello from Python"})
    
    def test_execute_tool_mark_as_fixed(self):
        """Test _execute_tool with mark_as_fixed"""
        # Create a mock for mark_as_fixed
        with patch.object(ToolsHandler, 'mark_as_fixed') as mock_mark_as_fixed:
            # Configure the mock
            mock_mark_as_fixed.return_value = {"success": True, "fixed": True, "message": "Issue marked as fixed"}
            
            # Call the function
            result = self.fixer._execute_tool("mark_as_fixed", {"fixed": True})
            
            # Verify the correct method was called
            mock_mark_as_fixed.assert_called_with(True)
            self.assertEqual(result, {"success": True, "fixed": True, "message": "Issue marked as fixed"})
            self.assertTrue(self.fixer.isfixed)
    
    def test_execute_tool_read_file(self):
        """Test _execute_tool with read_file"""
        # Create a mock for read_file
        with patch.object(ToolsHandler, 'read_file') as mock_read_file:
            # Configure the mock
            mock_read_file.return_value = {"success": True, "content": "test content"}
            
            # Call the function
            result = self.fixer._execute_tool("read_file", {"file_path": "test.txt", "line_start": 0, "line_end": 10})
            
            # Verify the correct method was called
            mock_read_file.assert_called_with("test.txt", 0, 10)
            self.assertEqual(result, {"success": True, "content": "test content"})
    
    def test_execute_tool_edit_file(self):
        """Test _execute_tool with edit_file"""
        # Create a mock for edit_file
        with patch.object(ToolsHandler, 'edit_file') as mock_edit_file:
            # Configure the mock
            mock_edit_file.return_value = {"success": True, "message": "File edited successfully"}
            
            # Call the function
            result = self.fixer._execute_tool("edit_file", {
                "file_path": "test.txt", 
                "line_start": 0, 
                "line_end": 10, 
                "new_content": "new content"
            })
            
            # Verify the correct method was called
            mock_edit_file.assert_called_with("test.txt", 0, 10, "new content")
            self.assertEqual(result, {"success": True, "message": "File edited successfully"})
    
    def test_execute_tool_unknown_function(self):
        """Test _execute_tool with an unknown function"""
        result = self.fixer._execute_tool("unknown_function", {})
        
        self.assertFalse(result["success"])
        self.assertIn("Unknown function", result["error"])
    
    def test_fix_with_tool_calls(self):
        """Test the fix method with tool calls"""
        # Create a sample error and code
        error = "TypeError: can only concatenate str (not 'int') to str"
        logs = "Error: can only concatenate str (not 'int') to str"
        relevant_code = "def main():\n    result = 'Hello ' + 42\n    print(result)"
        
        # Create a mock response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "I will fix this error by converting the integer to a string."
        
        # Create a tool call for edit_file
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "edit_file"
        mock_tool_call.function.arguments = json.dumps({
            "file_path": self.test_file_path,
            "line_start": 1,
            "line_end": 1,
            "new_content": "    result = 'Hello ' + str(42)"
        })
        
        # Add a second tool call for mark_as_fixed
        mock_tool_call2 = MagicMock()
        mock_tool_call2.id = "call_456"
        mock_tool_call2.function.name = "mark_as_fixed"
        mock_tool_call2.function.arguments = json.dumps({"fixed": True})
        
        # Set up the message to return the tool calls
        mock_message.tool_calls = [mock_tool_call, mock_tool_call2]
        mock_response.choices = [MagicMock(message=mock_message)]
        
        # Set up the mock client to return our mock response
        self.fixer.oai_client.chat.completions.create.return_value = mock_response
        
        # No need to patch anything, just call the fix method directly
        # Also patch _execute_tool to use the real implementation but avoid real file operations
        with patch.object(self.fixer, '_execute_tool', side_effect=self.fixer._execute_tool) as mock_execute_tool:
            # Run the fix method in a single turn
            result = self.fixer.fix(error=error, logs=logs, relevant_code=relevant_code)
            
            # Check that execute_tool was called twice
            self.assertEqual(mock_execute_tool.call_count, 2)
            
            # Check that the first call was for edit_file
            args1, kwargs1 = mock_execute_tool.call_args_list[0]
            self.assertEqual(args1[0], "edit_file")
            
            # Check that the second call was for mark_as_fixed
            args2, kwargs2 = mock_execute_tool.call_args_list[1]
            self.assertEqual(args2[0], "mark_as_fixed")
            
            # Check that isfixed is now True and the method returned True
            self.assertTrue(self.fixer.isfixed)
            self.assertTrue(result)
    
    def test_fix_no_tool_calls(self):
        """Test the fix method with no tool calls"""
        # Create a sample error and code
        error = "TypeError: can only concatenate str (not 'int') to str"
        logs = "Error: can only concatenate str (not 'int') to str"
        relevant_code = "def main():\n    result = 'Hello ' + 42\n    print(result)"
        
        # Create a mock response with no tool calls
        mock_response1 = MagicMock()
        mock_message1 = MagicMock()
        mock_message1.content = "You need to convert the integer to a string."
        mock_message1.tool_calls = None
        mock_response1.choices = [MagicMock(message=mock_message1)]
        
        # Create a second mock response with a mark_as_fixed tool call
        mock_response2 = MagicMock()
        mock_message2 = MagicMock()
        mock_message2.content = "The issue is fixed."
        
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_789"
        mock_tool_call.function.name = "mark_as_fixed"
        mock_tool_call.function.arguments = json.dumps({"fixed": True})
        
        mock_message2.tool_calls = [mock_tool_call]
        mock_response2.choices = [MagicMock(message=mock_message2)]
        
        # Set up the mock client to return our mock responses in sequence
        self.fixer.oai_client.chat.completions.create.side_effect = [mock_response1, mock_response2]
        
        # No need to patch anything, just call the fix method directly
        # Run the fix method - first turn (no tool calls)
        result1 = self.fixer.fix(error=error, logs=logs, relevant_code=relevant_code)
        
        # Check that isfixed is still False after first turn
        self.assertFalse(self.fixer.isfixed)
        self.assertFalse(result1)
        
        # Run the fix method - second turn (mark_as_fixed)
        result2 = self.fixer.fix(error=error, logs=logs, relevant_code=relevant_code)
        
        # Check that isfixed is True after second turn
        self.assertTrue(self.fixer.isfixed)
        self.assertTrue(result2)
    
    # End of TestBaseFixer class

if __name__ == '__main__':
    unittest.main()
