#!/usr/bin/env python3
"""
Test the updated secret name for OpenAI API key access
"""
import os
import subprocess
import sys
import tempfile

def test_secret_access():
    """Test accessing the updated secret"""
    print("=== Testing Updated Secret Access ===")
    
    # Check the new secret name
    secret_names = os.getenv("COPILOT_AGENT_INJECTED_SECRET_NAMES")
    print(f"Injected secret names: {secret_names}")
    
    # Try to access the API key with the new name
    api_key = os.getenv("_OPENAIKEY")
    print(f"_OPENAIKEY found: {api_key is not None}")
    
    if api_key:
        print(f"Key length: {len(api_key)}")
        print(f"Starts with sk-: {api_key.startswith('sk-')}")
        print(f"First 15 chars: {api_key[:15]}...")
        return api_key
    
    return None

def test_watchmin_with_real_api_key():
    """Test Watchmin with the real API key"""
    print("\n=== Testing Watchmin with Real API Key ===")
    
    api_key = os.getenv("_OPENAIKEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    # Create a simple error script
    error_script_content = '''
import time
print("Starting test script...")
time.sleep(2)
print("About to cause an error...")
raise Exception("Test error for Watchmin")
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(error_script_content)
        error_script = f.name
    
    try:
        # Test 1: Basic help command with API key available
        print("\n1. Testing help command:")
        env = os.environ.copy()
        env['OPENAI_API_KEY'] = api_key  # Map to expected name
        
        result = subprocess.run(
            [sys.executable, 'main.py', '--help'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Exit code: {result.returncode}")
        if result.returncode == 0:
            print("✅ Help command works")
        else:
            print("❌ Help command failed")
            print(f"stderr: {result.stderr}")
        
        # Test 2: Test API key access in our modules
        print("\n2. Testing API key access in modules:")
        test_script = '''
import sys
sys.path.insert(0, '.')
from apihandlers.OAIKeys import get_api_key

try:
    api_key = get_api_key()
    print(f"API key retrieved: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"Key length: {len(api_key)}")
        print(f"Starts with sk-: {api_key.startswith('sk-')}")
except Exception as e:
    print(f"Error: {e}")
'''
        
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Exit code: {result.returncode}")
        print("Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        # Test 3: Test simple watchmin test with real API key
        print("\n3. Testing simple_watchmin_test.py:")
        result = subprocess.run(
            [sys.executable, 'simple_watchmin_test.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=90
        )
        
        print(f"Exit code: {result.returncode}")
        print("\nOutput highlights:")
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if any(keyword in line.lower() for keyword in ['error', 'repair', 'detected', 'openai', 'authentication']):
                print(f"  {line}")
        
        if result.stderr:
            print("\nError highlights:")
            error_lines = result.stderr.split('\n')
            for line in error_lines:
                if any(keyword in line.lower() for keyword in ['error', 'authentication', 'openai']):
                    print(f"  {line}")
        
        # Analyze results
        print("\n=== Results Analysis ===")
        full_output = result.stdout + result.stderr
        
        if "Error occurred in script:" in full_output and "Yes" in full_output:
            print("✅ Error detection working")
        
        if "Error detected by Watchmin:" in full_output and "Yes" in full_output:
            print("✅ Watchmin error detection working")
        
        if "Repair process attempted:" in full_output and "Yes" in full_output:
            print("✅ Repair process initiated")
        
        if "AuthenticationError" in full_output:
            print("❌ API authentication failed")
        elif "openai" in full_output.lower() and "error" not in full_output.lower():
            print("✅ OpenAI API access successful")
        
    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out")
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        try:
            os.unlink(error_script)
        except:
            pass

def test_direct_openai_client():
    """Test direct OpenAI client initialization"""
    print("\n=== Testing Direct OpenAI Client ===")
    
    api_key = os.getenv("_OPENAIKEY")
    if not api_key:
        print("❌ No API key found")
        return
    
    test_script = f'''
import os
os.environ['OPENAI_API_KEY'] = '{api_key}'

try:
    from openai import OpenAI
    client = OpenAI()
    
    # Try to list models to test API access
    models = client.models.list()
    print(f"✅ OpenAI client initialized successfully")
    print(f"Available models: {{len(models.data)}} models found")
    
except Exception as e:
    print(f"❌ OpenAI client error: {{e}}")
'''
    
    try:
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Exit code: {result.returncode}")
        print("Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Test failed: {e}")

def main():
    """Run all tests"""
    print("Testing Updated OpenAI API Secret\n")
    
    os.chdir('/home/runner/work/Watchmin/Watchmin')
    
    # Test secret access
    api_key = test_secret_access()
    
    if api_key:
        # Test Watchmin functionality
        test_watchmin_with_real_api_key()
        
        # Test direct OpenAI client
        test_direct_openai_client()
    else:
        print("❌ Cannot proceed without API key")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if api_key:
        print("✅ API key secret is now accessible")
        print("✅ Testing completed with real OpenAI API key")
        print("🔧 Check results above for functionality status")
    else:
        print("❌ API key still not accessible")

if __name__ == "__main__":
    main()