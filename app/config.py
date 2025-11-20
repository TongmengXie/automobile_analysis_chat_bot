import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

# Load environment first so status logs reflect the actual values.
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)
    print(f"Loaded configuration from {Path(env_path).name}")
else:
    print("No .env file found - using process environment values")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NGROK_API_KEY = os.getenv("NGRROK_API_KEY")  # keep legacy spelling for compatibility

print("\nAPI Key Status:")
print("OPENAI_API_KEY loaded" if OPENAI_API_KEY else "OPENAI_API_KEY missing")
if NGROK_API_KEY:
    print("NGRROK_API_KEY loaded")
print("\nAll imports successful!")
