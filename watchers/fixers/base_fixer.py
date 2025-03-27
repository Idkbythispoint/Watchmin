import main
import json
import apihandlers.OAIFunctionAssembler as OAIFunctionAssembler
from watchers.fixers.tools_handler import ToolsHandler

class BaseFixer:
    def __init__(self, process_target, pid):
        self.process_target = process_target
        self.pid = pid
        self.isfixed = False

    def fix(self, error, logs, relevant_code):
        """
        Attempt to fix an error by interacting with the LLM for one turn.
        
        This method handles one interaction/turn with the LLM. It sends the error, logs,
        and relevant code to the LLM, gets a response, processes any tool calls,
        and updates the conversation context.
        
        Args:
            error: The error message
            logs: The logs from the process
            relevant_code: The relevant code that might be causing the error
            
        Returns:
            bool: True if the issue was fixed in this turn, False otherwise
        """
        # If this is the first call to fix, initialize messages
        if not hasattr(self, 'messages'):
            self.messages = [
                {"role": "developer", "content": main.ConfigHandler.get_value("fixer_prompt")},
                {"role": "user", "content": f"Error: {error}\nLogs: {logs}\nRelevant Code: {relevant_code}"}
            ]
        
        # Make an API call for this turn
        response = main.OAIClient.chat.completions.create(
            model=main.ConfigHandler.get_value("model_for_fixer"),
            messages=self.messages,
            tools=OAIFunctionAssembler.get_fixer_tools(),
        )
        
        # Process the response
        message = response.choices[0].message
        print(f"Response from model: {message.content}")
        
        # Check if the model wants to use a tool
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                # Get tool details
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the appropriate tool
                tool_result = self._execute_tool(function_name, function_args)
                
                # Add the tool call and result to messages
                self.messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })
                
                # If the model marked the issue as fixed, set flag
                if function_name == "mark_as_fixed" and function_args.get("fixed", False):
                    self.isfixed = True
        else:
            # If no tool calls, add the response to messages for context
            self.messages.append({
                "role": "assistant",
                "content": message.content
            })
            
            # Ask if the error is fixed
            self.messages.append({
                "role": "user",
                "content": "Is the error fixed or should we continue trying to fix it? Use the mark_as_fixed tool to indicate if the error is fixed."
            })
        
        # Return current fixed status
        return self.isfixed
    
    def _execute_tool(self, function_name, args):
        """
        Execute the specified tool function with the given arguments.
        
        Args:
            function_name (str): Name of the tool function to execute
            args (dict): Arguments for the tool function
            
        Returns:
            dict: Result of the tool execution
        """
        tool_handler = ToolsHandler()
        
        if function_name == "run_shell_command":
            return tool_handler.run_shell_command(args.get("command"), args.get("timeout"))
            
        elif function_name == "run_python_code":
            return tool_handler.run_python_code(args.get("code"), args.get("timeout"))
            
        elif function_name == "mark_as_fixed":
            result = tool_handler.mark_as_fixed(args.get("fixed"))
            self.isfixed = args.get("fixed", False)
            return result
            
        elif function_name == "read_file":
            return tool_handler.read_file(
                args.get("file_path"), 
                args.get("line_start"), 
                args.get("line_end")
            )
            
        elif function_name == "edit_file":
            return tool_handler.edit_file(
                args.get("file_path"),
                args.get("line_start"),
                args.get("line_end"),
                args.get("new_content")
            )
            
        else:
            return {
                "success": False,
                "error": f"Unknown function name: {function_name}"
            }