#!/usr/bin/env python3
"""
Test script to diagnose environment secret access in Copilot environment.
"""

import os
import sys

def test_secret_access():
    """Test various ways to access the OPENAI_API_KEY environment secret."""
    
    print("Environment Secret Access Diagnostic")
    print("=" * 50)
    
    # Check standard environment variable access
    print("\n1. Standard Environment Variable Access:")
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"   os.getenv('OPENAI_API_KEY'): {repr(api_key)}")
    
    # Check if secret name is injected
    print("\n2. Copilot Secret Injection Status:")
    injected_secrets = os.getenv('COPILOT_AGENT_INJECTED_SECRET_NAMES', '')
    print(f"   COPILOT_AGENT_INJECTED_SECRET_NAMES: {repr(injected_secrets)}")
    
    # Check all environment variables for any that might contain the key
    print("\n3. Environment Variables Containing 'OPENAI' or 'KEY':")
    relevant_vars = []
    for key, value in os.environ.items():
        if 'OPENAI' in key.upper() or ('KEY' in key.upper() and len(value) > 20):
            relevant_vars.append((key, value))
    
    if relevant_vars:
        for key, value in relevant_vars:
            if len(value) > 50:
                display_value = f"{value[:20]}...{value[-10:]}"
            else:
                display_value = value
            print(f"   {key}: {display_value}")
    else:
        print("   No relevant environment variables found")
    
    # Test our current API key function
    print("\n4. Testing Current API Key Function:")
    try:
        from apihandlers.OAIKeys import get_api_key
        
        # Temporarily redirect stdin to avoid hanging on input()
        old_stdin = sys.stdin
        from io import StringIO
        sys.stdin = StringIO('')
        
        try:
            result = get_api_key()
            print(f"   get_api_key() returned: {type(result)} of length {len(result) if result else 'None'}")
            if result and len(result) > 10:
                print(f"   Key starts with: {result[:10]}...")
            else:
                print(f"   Full result: {repr(result)}")
        except EOFError:
            print("   get_api_key() prompted for input (no API key found)")
        except Exception as e:
            print(f"   get_api_key() error: {type(e).__name__}: {e}")
        finally:
            sys.stdin = old_stdin
            
    except ImportError as e:
        print(f"   Import error: {e}")
    
    # Check if the secret might be available in a different format
    print("\n5. Alternative Secret Access Patterns:")
    
    # Try different case variations
    for var_name in ['OPENAI_API_KEY', 'openai_api_key', 'OpenAI_API_Key']:
        value = os.getenv(var_name)
        if value:
            print(f"   Found {var_name}: {value[:20]}..." if len(value) > 20 else f"   Found {var_name}: {value}")
    
    # Check for GitHub Actions patterns
    for pattern in ['INPUT_OPENAI_API_KEY', 'GITHUB_SECRET_OPENAI_API_KEY', 'SECRET_OPENAI_API_KEY']:
        value = os.getenv(pattern)
        if value:
            print(f"   Found {pattern}: {value[:20]}..." if len(value) > 20 else f"   Found {pattern}: {value}")
    
    print("\n6. Environment Secret Injection Analysis:")
    if 'OPENAI_API_KEY' in injected_secrets:
        print("   ✅ Secret name is listed in COPILOT_AGENT_INJECTED_SECRET_NAMES")
        if api_key:
            print("   ✅ Secret value is accessible via os.getenv()")
            print("   🎉 Environment secret is working correctly!")
        else:
            print("   ❌ Secret value is NOT accessible via os.getenv()")
            print("   🔍 This suggests the secret injection mechanism needs investigation")
    else:
        print("   ❌ Secret name is NOT listed in COPILOT_AGENT_INJECTED_SECRET_NAMES")
        print("   ⚠️  Environment secret may not be configured properly")
    
    print("\n" + "=" * 50)
    print("Diagnostic Complete")

if __name__ == "__main__":
    test_secret_access()