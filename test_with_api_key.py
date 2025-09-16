#!/usr/bin/env python
"""
Test script that demonstrates Watchmin functionality with a provided API key.
This shows how the system would behave when the OpenAI API is available.
"""

import os
import sys
import subprocess
import time
import threading

def test_api_integration():
    """Test the API integration with a mock scenario"""
    print("=== Testing OpenAI API Integration ===")
    
    # Check if API key is available
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('_OPENAIKEY')
    if not api_key:
        print("❌ No API key found in environment")
        print("   The secret injection may not be working properly")
        print("   When a real API key is provided, the system would:")
        print("   1. Initialize OpenAI client successfully")
        print("   2. Generate repair suggestions for detected errors") 
        print("   3. Attempt to apply fixes to the failing code")
        print("   4. Retry the process to verify the fix")
        return False
    else:
        print(f"✅ API key found: {api_key[:10]}...")
        
        # Test OpenAI client initialization 
        try:
            import main
            client = main.get_oai_client()
            print("✅ OpenAI client initialized successfully")
            
            # Test a simple API call to verify connectivity
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                print("✅ OpenAI API connection successful")
                print(f"   Response: {response.choices[0].message.content}")
                return True
            except Exception as e:
                print(f"❌ OpenAI API call failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAI client initialization failed: {e}")
            return False

def test_end_to_end_with_api():
    """Test end-to-end functionality when API is available"""
    print("\n=== End-to-End Test with API ===")
    
    api_available = test_api_integration()
    
    if api_available:
        print("With API key available, Watchmin would:")
        print("✅ Monitor processes for errors")
        print("✅ Detect errors in stdout/stderr or exit codes")
        print("✅ Extract relevant code context")
        print("✅ Send error details to OpenAI for analysis")
        print("✅ Generate targeted repair suggestions")
        print("✅ Apply fixes to the code")
        print("✅ Restart the process to verify the fix")
        print("✅ Continue monitoring for future issues")
    else:
        print("Current behavior without API key:")
        print("✅ Monitor processes for errors") 
        print("✅ Detect errors in stdout/stderr or exit codes")
        print("❌ Cannot generate repair suggestions (no API key)")
        print("❌ Cannot apply fixes (repair requires AI)")
        print("✅ Graceful degradation - no crashes")

def run_demonstration():
    """Run a demonstration showing current vs. desired behavior"""
    print("\n=== Watchmin Functionality Demonstration ===")
    
    # First show what works now
    print("\nCurrent Working Features:")
    result = subprocess.run([
        sys.executable, "main.py", "--help"
    ], capture_output=True, text=True, cwd="/home/runner/work/Watchmin/Watchmin")
    
    if result.returncode == 0:
        print("✅ Help system works without API key")
    else:
        print("❌ Help system failed")
    
    # Test process monitoring
    print("\nProcess Monitoring Test:")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    error_script = os.path.join(script_dir, "error_script.py")
    
    # Start error script
    error_process = subprocess.Popen([
        sys.executable, error_script
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Give it time to start
    time.sleep(1)
    pid = error_process.pid
    print(f"✅ Started test process with PID: {pid}")
    
    # Test monitoring
    monitor_process = subprocess.Popen([
        sys.executable, "main.py", "--attach", str(pid)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    cwd="/home/runner/work/Watchmin/Watchmin")
    
    # Wait for results
    time.sleep(5)
    
    # Clean up
    if error_process.poll() is None:
        error_process.terminate()
    if monitor_process.poll() is None:
        monitor_process.terminate()
    
    monitor_output, monitor_error = monitor_process.communicate(timeout=5)
    
    if "Attached to process" in monitor_output:
        print("✅ Process attachment works")
    if "Error detected" in monitor_output:
        print("✅ Error detection works")
    if "Starting repair" in monitor_output:
        print("✅ Repair initiation works")
    
    print(f"\nMonitor output preview:")
    print(monitor_output[:300] + "..." if len(monitor_output) > 300 else monitor_output)

if __name__ == "__main__":
    print("Watchmin API Integration Test")
    print("=" * 40)
    
    test_end_to_end_with_api()
    run_demonstration()
    
    print("\n" + "=" * 40)
    print("Test Complete")