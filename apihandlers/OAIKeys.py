import os
import sys
import time
import json
import openai
import requests
import logging
import threading

def get_api_key():
    # Try standard environment variable first
    api_key = os.getenv("OPENAI_API_KEY")
    
    # If not found, try the injected secret name from Copilot environment
    if not api_key:
        api_key = os.getenv("_OPENAIKEY")
    
    if not api_key:
        if not os.path.exists("openai.key"):
            print("No API key found")
            valid_key = False
            while not valid_key:
                api_key = input("Enter your OpenAI API key: ")
                valid_key = check_oai_key(api_key)
        else:
            with open("openai.key", "r") as f:
                api_key = f.read().strip()
    return api_key
        


def check_oai_key(api_key):
    try:
        openai.api_key = api_key
        openai.models.list()
        with open("openai.key", "w") as f:
            f.write(api_key)
        print("API key is valid and saved.")
    except Exception as e:
        print("Invalid API key. Please try again. Error: ", e)
        return False
    return True