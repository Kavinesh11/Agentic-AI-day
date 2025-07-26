"""
Startup script for Receipt Management System with ADK Integration

This script checks the environment and starts the FastAPI server with enhanced
ADK features including Runner caching, WebSocket support, and session management.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv


def check_environment():
    """Check if the environment is properly configured."""
    print("🔍 Checking environment configuration...")

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

    # Check for optional environment variables
    port = os.getenv("PORT", "8000")
    debug = os.getenv("DEBUG", "False")

    print(f"✅ Environment configuration looks good!")
    print(f"   📡 Port: {port}")
    print(f"   🐛 Debug mode: {debug}")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("📦 Checking dependencies...")

    required_packages = [
        "fastapi",
        "uvicorn",
        "google.adk",
        "PIL",
        "python-dotenv",
        "websockets",
        "aiofiles"
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
            elif package == "websockets":
                import websockets
            elif package == "aiofiles":
                import aiofiles
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

    print("✅ All dependencies are installed!")
    return True


def check_adk_features():
    """Check ADK-specific features and capabilities."""
    print("🔧 Checking ADK features...")

    try:
        from google.adk import Runner, LiveRequestQueue
        from google.adk.types import types
        print("   ✅ ADK Runner and LiveRequestQueue available")
        print("   ✅ ADK types module available")

        # Check for WebSocket support
        try:
            import websockets
            print("   ✅ WebSocket support available")
        except ImportError:
            print("   ⚠️ WebSocket support not available")

        # Check for static file serving
        try:
            from fastapi.staticfiles import StaticFiles
            print("   ✅ Static file serving available")
        except ImportError:
            print("   ⚠️ Static file serving not available")

        return True

    except ImportError as e:
        print(f"   ❌ ADK features not available: {e}")
        return False


def check_static_directory():
    """Check if static directory exists for WebSocket UI."""
    print("📁 Checking static directory...")

    static_dir = Path("static")
    if not static_dir.exists():
        print("   ⚠️ Static directory not found, creating...")
        static_dir.mkdir(exist_ok=True)
        print("   ✅ Static directory created")
    else:
        print("   ✅ Static directory exists")

    # Check for index.html
    index_file = static_dir / "index.html"
    if not index_file.exists():
        print("   ⚠️ index.html not found in static directory")
        print("   ℹ️ WebSocket UI will not be available")
    else:
        print("   ✅ WebSocket UI available")

    return True


def start_server():
    """Start the FastAPI server with enhanced ADK features."""
    print("🚀 Starting Receipt Management System with ADK Integration...")

    # Get configuration
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    host = os.getenv("HOST", "0.0.0.0")

    print(f"   🌐 Server: http://{host}:{port}")
    print(f"   📚 API Docs: http://{host}:{port}/docs")
    print(f"   🖥️ WebSocket UI: http://{host}:{port}/ui")
    print(f"   🔍 Health Check: http://{host}:{port}/health")
    print(f"   📊 Cache Status: http://{host}:{port}/cache/status")
    print(f"   🐛 Debug Mode: {debug}")
    print("-" * 60)

    # Import and run the main application
    try:
        from main import app
        import uvicorn

        # Enhanced server configuration
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=debug,
            access_log=True,
            log_level="info" if not debug else "debug",
            workers=1  # Single worker for WebSocket support
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user.")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


def main():
    """Main startup function with enhanced checks."""
    print("🧾 Receipt Management System - ADK Enhanced Startup")
    print("=" * 60)

    # Check environment configuration
    if not check_environment():
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check ADK features
    if not check_adk_features():
        print("⚠️ Some ADK features may not be available")

    # Check static directory
    check_static_directory()

    print("\n🎯 All checks completed! Starting server...")
    print("=" * 60)

    # Start the server
    start_server()


if __name__ == "__main__":
    main()
