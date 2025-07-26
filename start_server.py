"""
Startup script for Receipt Management System

This script checks the environment and starts the FastAPI server.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check if the environment is properly configured."""
    print("Checking environment configuration...")
    
    # Load environment variables
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please copy env_example.txt to .env and configure your API keys.")
        return False
    
    load_dotenv()
    
    # Check for required environment variables
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key or google_api_key == "your_google_api_key_here":
        print("❌ GOOGLE_API_KEY not configured!")
        print("Please set your Google API key in the .env file.")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "google.adk",
        "PIL",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "PIL":
                import PIL
            elif package == "google.adk":
                import google.adk
            elif package == "python-dotenv":
                import dotenv
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def start_server():
    """Start the FastAPI server."""
    print("Starting Receipt Management System...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server.")
    print("-" * 50)
    
    # Import and run the main application
    try:
        from main import app
        import uvicorn
        
        port = int(os.getenv("PORT", 8000))
        debug = os.getenv("DEBUG", "False").lower() == "true"
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=debug,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main startup function."""
    print("Receipt Management System - Startup")
    print("=" * 50)
    
    # Check environment configuration
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main() 