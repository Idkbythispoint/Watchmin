from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
  model="gpt-4o-mini",
  messages=[
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "Given an error message and logs, identify the location of any relevant custom code.\n\nFocus on pinpointing relevant parts of custom code, excluding the interpreter's code, and specify the relevant file and its lines.\n\n# Steps\n\n1. **Analyze the Error Message**: Break down the error message to understand what went wrong.\n2. **Review the Logs**: Look through the logs to gather additional context that can help locate the problem.\n3. **Identify Custom Code**: Distinguish between custom code and interpreter code to focus on user-introduced sections.\n4. **Locate the File and Lines**: Determine the file path and specific line numbers where the issue is likely to originate.\n5. **Determine Relevance**: Assess whether a relevant file and lines can be identified post-analysis.\n\n# Notes\n\n- Ensure that the focus remains on custom code, excluding interpreter-level code."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "logs here"
        }
      ]
    }
  ],
  response_format={
    "type": "json_schema",
    "json_schema": {
      "name": "file_relevance",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "The full Linux file path to where the relevant file is."
          },
          "start_line": {
            "type": "number",
            "description": "The starting line of relevance in the file."
          },
          "end_line": {
            "type": "number",
            "description": "The ending line of relevance in the file."
          },
          "has_relevant_file": {
            "type": "boolean",
            "description": "Indicates whether a relevant file is known."
          }
        },
        "required": [
          "file_path",
          "start_line",
          "end_line",
          "has_relevant_file"
        ],
        "additionalProperties": False
      }
    }
  },
  temperature=1,
  max_completion_tokens=2048,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)