import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)
    print("Loaded configuration from .env file")
else:
    print("No .env file found - using environment variables or hardcoded keys")

# Verify API keys
print("\nAPI Key Status:")
if os.getenv('OPENAI_API_KEY') and os.getenv('OPENAI_API_KEY'):
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    print("OPENAI_API_KEY  loaded")

if os.getenv('NGRROK_API_KEY') and os.getenv('NGRROK_API_KEY'):
    NGRROK_API_KEY = os.getenv('NGRROK_API_KEY')
    print("NGRROK_API_KEY  loaded")
    
print("\nAll imports successful!")
