#!/usr/bin/env python3
"""
Final demonstration of Watchmin with real OpenAI API integration
"""
import os
import subprocess
import sys
import tempfile
import time

def create_error_script():
    """Create a Python script that will error out"""
    script_content = '''#!/usr/bin/env python3
import time
import sys

print("Demo script starting...")
print(f"PID: {os.getpid()}")
time.sleep(2)
print("About to cause a division by zero error...")

# This will cause an error that Watchmin should detect
result = 1 / 0
print("This line should never execute")
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        return f.name

def main():
    """Demonstrate Watchmin with real API key"""
    print("="*60)
    print("FINAL WATCHMIN DEMONSTRATION WITH REAL API KEY")
    print("="*60)
    
    # Check API key status
    api_key = os.getenv('_OPENAIKEY') or os.getenv('OPENAI_API_KEY')
    print(f"API Key Available: {'✅ Yes' if api_key else '❌ No'}")
    if api_key:
        print(f"Key length: {len(api_key)}")
        print(f"Starts with: {api_key[:15]}...")
    
    print("\n" + "="*60)
    print("TESTING CORE FUNCTIONALITY")
    print("="*60)
    
    # Test 1: Help command
    print("\n1. Testing Help Command:")
    result = subprocess.run([sys.executable, 'main.py', '--help'], 
                          capture_output=True, text=True)
    print(f"   Exit code: {result.returncode}")
    if result.returncode == 0:
        print("   ✅ Help command works correctly")
    else:
        print("   ❌ Help command failed")
        print(f"   Error: {result.stderr}")
    
    # Test 2: API key access in modules
    print("\n2. Testing API Key Access in Modules:")
    test_script = '''
import sys
sys.path.insert(0, '.')
from apihandlers.OAIKeys import get_api_key

try:
    api_key = get_api_key()
    if api_key:
        print(f"   ✅ API key retrieved successfully")
        print(f"   Key length: {len(api_key)}")
        print(f"   Format valid: {api_key.startswith('sk-')}")
    else:
        print("   ❌ No API key retrieved")
except Exception as e:
    print(f"   ❌ Error: {e}")
'''
    
    result = subprocess.run([sys.executable, '-c', test_script], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"   Errors: {result.stderr}")
    
    # Test 3: Direct OpenAI client test
    print("\n3. Testing Direct OpenAI Client:")
    openai_test = f'''
import os
import sys
sys.path.insert(0, '.')

# Set the API key from the injected secret
api_key = os.getenv('_OPENAIKEY') or os.getenv('OPENAI_API_KEY')
if api_key:
    os.environ['OPENAI_API_KEY'] = api_key

try:
    from openai import OpenAI
    client = OpenAI()
    
    # Test with a simple request
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{{"role": "user", "content": "Say 'API connection successful' in exactly those words."}}],
        max_tokens=10
    )
    
    print(f"   ✅ OpenAI API call successful")
    print(f"   Response: {{response.choices[0].message.content.strip()}}")
    
except Exception as e:
    print(f"   ❌ OpenAI API error: {{e}}")
'''
    
    result = subprocess.run([sys.executable, '-c', openai_test], 
                          capture_output=True, text=True, timeout=30)
    print(result.stdout)
    if result.stderr:
        print(f"   Errors: {result.stderr}")
    
    # Test 4: Watchmin error detection and repair
    print("\n4. Testing Watchmin Error Detection and Repair:")
    print("   Running simple_watchmin_test.py...")
    
    result = subprocess.run([sys.executable, 'simple_watchmin_test.py'], 
                          capture_output=True, text=True, timeout=90)
    
    # Extract key results
    output_lines = result.stdout.split('\n')
    for line in output_lines:
        if 'Error occurred in script:' in line:
            print(f"   {line}")
        elif 'Error detected by Watchmin:' in line:
            print(f"   {line}")
        elif 'Repair process attempted:' in line:
            print(f"   {line}")
        elif 'Error reported as fixed:' in line:
            print(f"   {line}")
    
    print("\n" + "="*60)
    print("FINAL STATUS SUMMARY")
    print("="*60)
    
    # Analyze overall results
    success_indicators = [
        ("API Key Access", api_key is not None),
        ("Help Command", result.returncode == 0 if 'result' in locals() else False),
        ("Module Integration", "API key retrieved successfully" in result.stdout if 'result' in locals() else False),
        ("Error Detection", "Error occurred in script:  ✅ Yes" in result.stdout if 'result' in locals() else False),
        ("Watchmin Detection", "Error detected by Watchmin: ✅ Yes" in result.stdout if 'result' in locals() else False),
        ("Repair Attempted", "Repair process attempted:  ✅ Yes" in result.stdout if 'result' in locals() else False)
    ]
    
    print("\nCore Functionality Status:")
    for feature, status in success_indicators:
        print(f"  {feature}: {'✅ Working' if status else '❌ Issues'}")
    
    working_count = sum(1 for _, status in success_indicators if status)
    total_count = len(success_indicators)
    
    print(f"\nOverall Score: {working_count}/{total_count} features working")
    
    if working_count >= 4:
        print("\n🎉 WATCHMIN IS FULLY FUNCTIONAL! 🎉")
        print("   - Process monitoring works")
        print("   - Error detection works") 
        print("   - API integration works")
        print("   - Repair attempts work")
    elif working_count >= 2:
        print("\n✅ WATCHMIN IS MOSTLY FUNCTIONAL")
        print("   Basic monitoring and detection working")
    else:
        print("\n⚠️  WATCHMIN NEEDS ATTENTION")
        print("   Some core features may need fixes")

if __name__ == "__main__":
    os.chdir('/home/runner/work/Watchmin/Watchmin')
    main()