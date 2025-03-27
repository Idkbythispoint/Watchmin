time to lock tf in

1. add a webui/gui/not cli of some sort
2. allow the user to write tests to auto-run
3. automatic backups

original schizo-post:

Attaches to a service/process
Monitors output from said service/process
If an error comes up, send error +last ~100 lines of logs + relavant code portion (decided by gpt-4o-mini after seeing error messages) to o3-mini/whatever model
Give LLM shell command access + read/write tools + Google (probably duckduckgo as that doesn't need API keys but sjfhwndbsj)
Tell LLM to suggest commands to fix it, and depending on configuration 1. Sandbox then test 2. Send to human for review or 3. Execute commands
Severity system decided by LLM? Maybe give it more authority if it sees a possible data leak?
Could also expand to watch network traffic and user activity to look for intrusions
"Ask the Admin" feature where you can ask the LLM why it did what or about the current state of the server
PUT EVERYTHING AS UNTRUSTED TEXT!!!!! prompt injection is VERY BAD and if the LLM sees any user input that is an attack vector