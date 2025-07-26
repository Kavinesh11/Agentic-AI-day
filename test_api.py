"""
Test script for Receipt Management System API with ADK Integration

This script demonstrates how to interact with the enhanced receipt processing API
including WebSocket support, Runner caching, and session management.
"""

import requests
import json
import sys
import asyncio
import websockets
import base64
from pathlib import Path
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"


def test_health_endpoint():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("🏥 Health Check:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("-" * 50)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to the API. Make sure the server is running.")
        return False


def test_root_endpoint():
    """Test the root endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/")
        print("🏠 Root Endpoint:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print("-" * 50)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to the API. Make sure the server is running.")
        return False


def test_cache_endpoints():
    """Test cache management endpoints."""
    print("💾 Cache Management Tests:")

    # Test cache status
    try:
        response = requests.get(f"{BASE_URL}/cache/status")
        print(f"   Cache Status - Status: {response.status_code}")
        if response.status_code == 200:
            cache_info = response.json()
            print(f"   Cache Info: {json.dumps(cache_info, indent=2)}")
        print("-" * 30)
    except requests.exceptions.ConnectionError:
        print("   ❌ Cache status test failed")
        return False

    # Test cache clear
    try:
        response = requests.post(f"{BASE_URL}/cache/clear")
        print(f"   Cache Clear - Status: {response.status_code}")
        if response.status_code == 200:
            clear_info = response.json()
            print(f"   Clear Result: {json.dumps(clear_info, indent=2)}")
        print("-" * 30)
    except requests.exceptions.ConnectionError:
        print("   ❌ Cache clear test failed")
        return False

    return True


def test_ui_endpoint():
    """Test the WebSocket UI endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/ui")
        print("🖥️ WebSocket UI Endpoint:")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ WebSocket UI is accessible")
        else:
            print("   ⚠️ WebSocket UI not available")
        print("-" * 50)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to the API. Make sure the server is running.")
        return False


def test_receipt_processing(image_path):
    """Test receipt processing with an image file."""
    if not Path(image_path).exists():
        print(f"❌ Error: Image file {image_path} not found.")
        return False

    try:
        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            response = requests.post(
                f"{BASE_URL}/process-receipt", files=files)

        print("🧾 Receipt Processing:")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Success! Receipt processed.")
            print(f"   📁 Filename: {result.get('filename')}")
            print(f"   📏 File Size: {result.get('file_size')} bytes")
            print(
                f"   🆔 Bill ID: {result.get('processing_result', {}).get('billId', 'N/A')}")
            print(
                f"   💰 Total Amount: {result.get('processing_result', {}).get('totalAmount', 'N/A')}")
            print("\n   📋 Processing Result:")
            print(json.dumps(result.get('processing_result'), indent=4))
        else:
            print(f"   ❌ Error: {response.json()}")

        print("-" * 50)
        return response.status_code == 200

    except FileNotFoundError:
        print(f"❌ Error: Image file {image_path} not found.")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to the API. Make sure the server is running.")
        return False


async def test_websocket_connection(user_id: str = "test_user"):
    """Test WebSocket connection and basic messaging."""
    print(f"🔌 WebSocket Connection Test (User: {user_id}):")

    try:
        # Connect to WebSocket
        ws_url = f"{WS_BASE_URL}/ws/{user_id}?is_audio=false"
        async with websockets.connect(ws_url) as websocket:
            print("   ✅ WebSocket connected successfully")

            # Send a test message
            test_message = {
                "type": "text",
                "mime_type": "text/plain",
                "data": "Hello, this is a test message from the test script!"
            }

            await websocket.send(json.dumps(test_message))
            print("   📤 Test message sent")

            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print("   📥 Response received:")
                response_data = json.loads(response)
                print(
                    f"   Response Type: {response_data.get('type', 'unknown')}")
                if response_data.get('type') == 'text':
                    print(
                        f"   Response Data: {response_data.get('data', '')[:100]}...")
                print("   ✅ WebSocket communication successful")
                return True
            except asyncio.TimeoutError:
                print("   ⚠️ No response received within timeout")
                return False

    except Exception as e:
        print(f"   ❌ WebSocket test failed: {e}")
        return False


async def test_websocket_receipt_processing(image_path: str, user_id: str = "test_user"):
    """Test receipt processing via WebSocket."""
    if not Path(image_path).exists():
        print(f"❌ Error: Image file {image_path} not found.")
        return False

    print(f"🧾 WebSocket Receipt Processing Test (User: {user_id}):")

    try:
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

        # Connect to WebSocket
        ws_url = f"{WS_BASE_URL}/ws/{user_id}?is_audio=false"
        async with websockets.connect(ws_url) as websocket:
            print("   ✅ WebSocket connected for receipt processing")

            # Send receipt image
            receipt_message = {
                "type": "receipt_image",
                "mime_type": "image/jpeg",
                "data": base64_image,
                "filename": Path(image_path).name
            }

            await websocket.send(json.dumps(receipt_message))
            print(f"   📤 Receipt image sent: {Path(image_path).name}")

            # Wait for processing response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                print("   📥 Processing response received:")
                response_data = json.loads(response)
                print(
                    f"   Response Type: {response_data.get('type', 'unknown')}")
                if response_data.get('type') == 'text':
                    print(
                        f"   Response Data: {response_data.get('data', '')[:200]}...")
                print("   ✅ WebSocket receipt processing successful")
                return True
            except asyncio.TimeoutError:
                print("   ⚠️ No processing response received within timeout")
                return False

    except Exception as e:
        print(f"   ❌ WebSocket receipt processing failed: {e}")
        return False


async def run_websocket_tests(image_path: Optional[str] = None):
    """Run all WebSocket tests."""
    print("🔌 WebSocket Tests:")
    print("=" * 50)

    # Test basic WebSocket connection
    ws_success = await test_websocket_connection()

    # Test WebSocket receipt processing if image provided
    if image_path and Path(image_path).exists():
        ws_receipt_success = await test_websocket_receipt_processing(image_path)
    else:
        ws_receipt_success = True  # Skip if no image
        print("   ℹ️ Skipping WebSocket receipt test (no image provided)")

    return ws_success and ws_receipt_success


def main():
    """Main test function with comprehensive ADK feature testing."""
    print("🧾 Testing Receipt Management System API with ADK Integration")
    print("=" * 70)

    # Test basic endpoints
    if not test_health_endpoint():
        print("❌ Health check failed. Exiting.")
        sys.exit(1)

    if not test_root_endpoint():
        print("❌ Root endpoint test failed. Exiting.")
        sys.exit(1)

    # Test cache management
    test_cache_endpoints()

    # Test UI endpoint
    test_ui_endpoint()

    # Test receipt processing if image provided
    image_path = None
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"📸 Testing receipt processing with image: {image_path}")
        test_receipt_processing(image_path)
    else:
        print("ℹ️ To test receipt processing, run:")
        print("   python test_api.py path/to/receipt/image.jpg")

    # Run WebSocket tests
    print("\n🔌 Running WebSocket tests...")
    try:
        ws_success = asyncio.run(run_websocket_tests(image_path))
        if ws_success:
            print("✅ WebSocket tests completed successfully")
        else:
            print("⚠️ Some WebSocket tests failed")
    except Exception as e:
        print(f"❌ WebSocket tests failed: {e}")

    print("\n🎯 API testing completed!")
    print("=" * 70)
    print("📚 Available endpoints:")
    print("   • GET  / - Root endpoint")
    print("   • GET  /health - Health check")
    print("   • GET  /cache/status - Cache status")
    print("   • POST /cache/clear - Clear cache")
    print("   • POST /process-receipt - Process receipt image")
    print("   • GET  /ui - WebSocket UI")
    print("   • WS   /ws/{user_id} - WebSocket endpoint")
    print("\n🔗 Access the WebSocket UI at: http://localhost:8000/ui")


if __name__ == "__main__":
    main()
