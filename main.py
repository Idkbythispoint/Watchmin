import apihandlers.OAIKeys as OAIKeys
import sys
import psutil
import watchers.base_watcher as base_watcher
from openai import OpenAI
import internal.confighandler as confighandler
import time


# Initialize these lazily to avoid blocking on API keys at import time
OAIClient = None
ConfigHandler = None

def get_oai_client():
    """Get OpenAI client, initializing if needed"""
    global OAIClient
    if OAIClient is None:
        OAIClient = OpenAI(api_key=OAIKeys.get_api_key())
    return OAIClient

def get_config_handler():
    """Get config handler, initializing if needed"""
    global ConfigHandler
    if ConfigHandler is None:
        ConfigHandler = confighandler.ConfigHandler()
    return ConfigHandler

# Store active watchers
active_watchers = {}

def main():
    # Check for command line arguments
    args = sys.argv[1:]  # Skip the first argument (script name)
    
    # Handle watch_process command
    if "--watch_process" in args:
        index = args.index("--watch_process")
        if index + 1 < len(args):
            target = args[index + 1]
            print(f"Requested to watch: {target}")
            
            # Check if it's a PID or command
            if target.isdigit():
                # It's a PID, attach to existing process
                watch_existing_process(int(target))
            else:
                # It's a command, start and watch the process
                watch_new_process(target)
        else:
            print("Error: --watch_process requires a path or process ID")
            
    # Handle attach command
    elif "--attach" in args:
        index = args.index("--attach")
        if index + 1 < len(args):
            pid = args[index + 1]
            if pid.isdigit():
                watch_existing_process(int(pid))
            else:
                print("Error: --attach requires a valid process ID")
        else:
            print("Error: --attach requires a process ID")
    
    # Handle list command to show active watchers
    elif "--list" in args:
        list_active_watchers()
    
    # Handle stop command to stop a specific watcher
    elif "--stop" in args:
        index = args.index("--stop")
        if index + 1 < len(args):
            watcher_id = args[index + 1]
            stop_watcher(watcher_id)
        else:
            print("Error: --stop requires a watcher ID")
    
    # No arguments, show help
    else:
        show_help()
    
    # If this is the main thread (not a subprocess)
    if not "--background" in args:
        try:
            # Keep main process alive while watchers are running
            while active_watchers:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping all watchers...")
            stop_all_watchers()


def watch_new_process(command):
    """
    Start a new process and watch it
    
    Args:
        command: The command to execute and watch
    
    Returns:
        str: ID of the created watcher
    """
    try:
        # Get dependencies only if needed for repair functionality
        config_handler = get_config_handler()
        
        # Create a BaseWatcher instance (OpenAI client will be lazy-loaded if needed)
        watcher = base_watcher.BaseWatcher(
            process_target=command, 
            config_handler=config_handler,
            oai_client=None  # Will be lazy-loaded when needed for repair
        )
        
        # Start the process
        pid = watcher.start()
        
        if pid:
            watcher_id = f"process_{pid}"
            active_watchers[watcher_id] = watcher
            print(f"Created watcher '{watcher_id}' for command: {command}")
            return watcher_id
        else:
            print(f"Failed to start process: {command}")
            return None
    except Exception as e:
        print(f"Error starting process watcher: {e}")
        return None


def watch_existing_process(pid):
    """
    Attach to an existing process and watch it
    
    Args:
        pid: Process ID to attach to
    
    Returns:
        str: ID of the created watcher
    """
    try:
        # Verify the process exists
        try:
            process = psutil.Process(pid)
            process_name = process.name()
        except psutil.NoSuchProcess:
            print(f"Process with PID {pid} not found")
            return None
        
        # Get dependencies only if needed for repair functionality
        config_handler = get_config_handler()
        
        # Create a BaseWatcher instance and attach to the process
        watcher = base_watcher.BaseWatcher(
            pid=pid, 
            config_handler=config_handler,
            oai_client=None  # Will be lazy-loaded when needed for repair
        )
        
        if watcher.is_attached:
            watcher_id = f"attached_{pid}"
            active_watchers[watcher_id] = watcher
            print(f"Created watcher '{watcher_id}' for process: {process_name} (PID: {pid})")
            return watcher_id
        else:
            print(f"Failed to attach to process: {pid}")
            return None
    except Exception as e:
        print(f"Error attaching to process: {e}")
        return None


def list_active_watchers():
    """Display all active watchers"""
    if not active_watchers:
        print("No active watchers")
        return
    
    print("\nActive Watchers:")
    print("-" * 60)
    print(f"{'ID':<15} {'Process':<20} {'PID':<10} {'Type':<15}")
    print("-" * 60)
    
    for watcher_id, watcher in active_watchers.items():
        if watcher.is_attached:
            process_info = f"PID: {watcher.pid}"
            watcher_type = "Attached"
            pid = watcher.pid
        else:
            process_info = watcher.process_target
            watcher_type = "Started"
            pid = watcher.process.pid if watcher.process else "N/A"
        
        print(f"{watcher_id:<15} {process_info:<20} {str(pid):<10} {watcher_type:<15}")


def stop_watcher(watcher_id):
    """Stop a specific watcher"""
    if watcher_id in active_watchers:
        watcher = active_watchers[watcher_id]
        watcher.stop()
        del active_watchers[watcher_id]
        print(f"Stopped watcher: {watcher_id}")
    else:
        print(f"Watcher '{watcher_id}' not found")


def stop_all_watchers():
    """Stop all active watchers"""
    for watcher_id in list(active_watchers.keys()):
        stop_watcher(watcher_id)


def show_help():
    """Display help information"""
    print("\nWatchmin - Process Monitoring and Error Recovery Tool")
    print("=" * 60)
    print("Usage:")
    print("  python main.py [command] [options]")
    print("\nCommands:")
    print("  --watch_process <command or pid>  Start a new process and watch it, or attach to existing PID")
    print("  --attach <pid>                    Attach to an existing process by PID")
    print("  --list                            List all active watchers")
    print("  --stop <watcher_id>               Stop a specific watcher")
    print("\nExamples:")
    print("  python main.py --watch_process \"python my_script.py\"")
    print("  python main.py --attach 12345")
    print("  python main.py --list")
    print("  python main.py --stop process_12345")


# Legacy function maintained for backward compatibility
def find_process(pid=None, process_name=None):
    """
    Find a system process based on PID or name.
    This is maintained for backward compatibility.
    
    Args:
        pid (int, optional): Process ID to find
        process_name (str, optional): Process name to find
        
    Returns:
        psutil.Process: Process object if found, None otherwise
    """
    try:
        if pid and str(pid).isdigit():
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
        print(f"Error finding process: {e}")
        return None

if __name__ == "__main__":
    main()
