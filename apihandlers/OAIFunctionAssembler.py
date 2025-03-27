from openai import OpenAI

def get_fixer_tools():
    """
    Returns a list of tool definitions for use with OpenAI API.
    
    Currently includes:
    - run_shell_command: A function to run Ubuntu shell commands
    - run_python_code: A function to run Python code
    - mark_as_fixed: A function to mark the error/issue as fixed or ignorable
    - read_file: A function to read a file in the current working directory

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
                        "command",
                        "timeout"
                    ],
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to be executed"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "The maximum number of seconds to wait for the command to complete",
                            #"default": 60
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
                        "code",
                        "timeout"
                    ],
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Python code to be executed"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "The maximum number of seconds to wait for the code to complete",
                            #"default": 60
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
                            #  "default": True
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
                "name": "read_file",
                "description": "A function to read a file in the current working directory",
                "parameters": {
                    "type": "object",
                    "required": [
                        "file_path",
                        "line_start",
                        "line_end"
                    ],
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The full path to the file to be read"
                        },
                        "line_start": {
                            "type": "integer",
                            "description": "The line number to start reading from, 0 is the first line"
                        },
                        "line_end": {
                            "type": "integer",
                            "description": "The line number to end reading at, 0 is the first line, -1 makes it read to the end of the file"
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
                "name": "edit_file",
                "description": "A function to edit a file",
                "parameters": {
                    "type": "object",
                    "required": [
                        "file_path",
                        "line_start",
                        "line_end",
                        "new_content"
                    ],
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file to be edited"
                        },
                        "line_start": {
                            "type": "integer",
                            "description": "The line number to start editing from, 0 is the first line"
                        },
                        "line_end": {
                            "type": "integer",
                            "description": "The line number to end editing at, 0 is the first line, -1 makes it edit to the end of the file"
                        },
                        "new_content": {
                            "type": "string",
                            "description": "The new content to be written to the file"
                        }
                    },
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    ]
    
    return tools


def get_relevance_format():
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "file_path_information",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file."
                    },
                    "start_line": {
                        "type": "number",
                        "description": "The starting line number of the relevant section; -1 indicates the start of the file."
                    },
                    "end_line": {
                        "type": "number",
                        "description": "The ending line number of the relevant section; -1 indicates the end of the file."
                    },
                    "more_relevant_code": {
                        "type": "boolean",
                        "description": "Whether there is more relevant code elsewhere."
                    }
                },
                "required": [
                    "file_path",
                    "start_line",
                    "end_line",
                    "more_relevant_code"
                ],
                "additionalProperties": False
            }
        }
    }

    return response_format



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