import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("Environment Variables (from shell and .env):")
print("-" * 50)

# Get all environment variables
env_vars = {
    'POSTGRES_DB': os.getenv('POSTGRES_DB'),
    'POSTGRES_USER': os.getenv('POSTGRES_USER'),
    'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
    'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
    'POSTGRES_PORT': os.getenv('POSTGRES_PORT'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
}

# Print each variable
for key, value in env_vars.items():
    if value:
        if 'KEY' in key or 'PASSWORD' in key:
            # Mask sensitive values
            masked_value = '*' * (len(value) - 4) + value[-4:]
            print(f"{key}: {masked_value}")
        else:
            print(f"{key}: {value}")
    else:
        print(f"{key}: Not set")

print("-" * 50) 