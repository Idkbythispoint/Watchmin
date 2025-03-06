import apihandlers.OAIKeys as OAIKeys
import sys
import psutil
import watchers.base_watcher as base_watcher

def main():
    openaikey = OAIKeys.get_api_key()
    
    # Check for command line arguments
    args = sys.argv[1:]  # Skip the first argument (script name)
    
    # Check if --watch_process argument exists
    if "--watch_process" in args:
        # Find the index of --watch_process
        index = args.index("--watch_process")
        
        # Check if there's a value after --watch_process
        if index + 1 < len(args):
            target = args[index + 1]
            print(f"Watching process: {target}")
            find_process(target)
        else:
            print("Error: --watch_process requires a path or process ID")
    

def find_process(pid=None, process_name=None):
    """
    Establish a watcher for a system process based on PID or name.
    
    Args:
        pid (int, optional): Process ID to watch
        process_name (str, optional): Process name to watch
        
    Returns:
        psutil.Process: Process object if found, None otherwise
    """
    try:
        if pid and pid.isdigit():
            # If a numeric PID was provided
            process = psutil.Process(int(pid))
            return process
        elif process_name or pid:
            # Search by name (or non-numeric identifier)
            name_to_search = process_name or pid
            for proc in psutil.process_iter(['pid', 'name']):
                if name_to_search.lower() in proc.info['name'].lower():
                    return proc
            print(f"No process matching '{name_to_search}' found")
            return None
        else:
            print("Either PID or process name must be provided")
            return None
    except psutil.NoSuchProcess:
        print(f"Process with PID {pid} not found")
        return None
    except Exception as e:
        print(f"Error establishing process watcher: {e}")
        return None

if __name__ == "__main__":
    main()
