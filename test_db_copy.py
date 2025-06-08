#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing environment variables...")
print(f"POSTGRES_SERVER: {os.getenv('POSTGRES_SERVER')}")
print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
print(f"POSTGRES_PASSWORD: {'***' if os.getenv('POSTGRES_PASSWORD') else 'Not set'}")
print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT')}")

# Test import
try:
    import psycopg2
    print("✅ psycopg2 imported successfully")
except ImportError as e:
    print(f"❌ Error importing psycopg2: {e}")

print("Test completed.")
