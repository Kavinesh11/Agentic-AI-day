#!/usr/bin/env python3
"""
Environment Setup Script for Receipt Management System

This script helps you set up your environment configuration file.
"""

import os
import shutil
from pathlib import Path


def setup_environment():
    """Set up the environment configuration file."""
    print("🧾 Receipt Management System - Environment Setup")
    print("=" * 50)

    # Check if .env already exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists!")
        print("Current configuration:")
        with open(env_file, 'r') as f:
            print(f.read())
        return

    # Copy from example
    example_file = Path("env_example.txt")
    if not example_file.exists():
        print("❌ env_example.txt not found!")
        return

    try:
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from template")
        print("\n📝 Next steps:")
        print("1. Edit the .env file and add your Google API key")
        print("2. Get your API key from: https://aistudio.google.com/")
        print("3. Replace 'your_google_api_key_here' with your actual key")
        print("4. Run: python start_server.py")

    except Exception as e:
        print(f"❌ Error creating .env file: {e}")


def check_environment():
    """Check if environment is properly configured."""
    print("\n🔍 Checking environment configuration...")

    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        setup_environment()
        return False

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check for required environment variables
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key or google_api_key == "your_google_api_key_here":
        print("❌ GOOGLE_API_KEY not configured!")
        print("Please edit the .env file and add your Google API key.")
        return False

    print("✅ Environment configuration looks good!")
    return True


if __name__ == "__main__":
    setup_environment()
    check_environment()
