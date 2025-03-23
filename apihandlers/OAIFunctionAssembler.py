from openai import OpenAI

def get_oai_tools():
    """
    Returns a list of tool definitions for use with OpenAI API.
    
    Currently includes:
    - run_shell_command: A function to run Ubuntu shell commands
    
    Returns:
        list: A list of tool definitions compatible with OpenAI's function calling
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_shell_command",
                "description": "A function to run a Ubuntu shell command in the current working directory",
                "parameters": {
                    "type": "object",
                    "required": [
                        "command"
                    ],
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to be executed"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "The maximum number of seconds to wait for the command to complete",
                            "default": 60
                        }
                    },
                    "additionalProperties": False
                },
                "strict": True
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_python_code",
                "description": "A function to run a Python code snippet",
                "parameters": {
                    "type": "object",
                    "required": [
                        "code"
                    ],
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Python code to be executed"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "The maximum number of seconds to wait for the code to complete",
                            "default": 60
                        }
                    },
                    "additionalProperties": False
                },
                "strict": True
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mark_as_fixed",
                "description": "Mark the error/issue as fixed or ignorable",
                "parameters": {
                    "type": "object",
                    "required": [
                        "fixed"
                    ],
                    "properties": {
                        "fixed": {
                            "type": "boolean",
                            "description": "Whether the error/issue has been fixed or is ignorable. True is fixed, False is ignorable.",
                            "default": True
                        }
                    },
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    ]
    
    return tools

# client = OpenAI()

# response = client.chat.completions.create(
#   model="gpt-4o",
#   messages=[],
#   response_format={
#     "type": "text"
#   },
#   tools=get_oai_tools(),
#   temperature=1,
#   max_completion_tokens=2048,
#   top_p=1,
#   frequency_penalty=0,
#   presence_penalty=0
# )