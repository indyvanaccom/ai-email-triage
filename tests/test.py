from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Test: Print all environment variables loaded from .env
print("Environment variables loaded from .env:")
for key, value in os.environ.items():
    print(f"{key}={value}")
