"""
Test script for Receipt Management System API

This script demonstrates how to interact with the receipt processing API.
"""

import requests
import json
import sys
from pathlib import Path

def test_health_endpoint():
    """Test the health check endpoint."""
    try:
        response = requests.get("http://localhost:8000/health")
        print("Health Check:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("-" * 50)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the API. Make sure the server is running.")
        return False

def test_root_endpoint():
    """Test the root endpoint."""
    try:
        response = requests.get("http://localhost:8000/")
        print("Root Endpoint:")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("-" * 50)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the API. Make sure the server is running.")
        return False

def test_receipt_processing(image_path):
    """Test receipt processing with an image file."""
    if not Path(image_path).exists():
        print(f"Error: Image file {image_path} not found.")
        return False
    
    try:
        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            response = requests.post("http://localhost:8000/process-receipt", files=files)
        
        print("Receipt Processing:")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Success! Receipt processed.")
            print(f"Filename: {result.get('filename')}")
            print(f"File Size: {result.get('file_size')} bytes")
            print("\nProcessing Result:")
            print(json.dumps(result.get('processing_result'), indent=2))
        else:
            print(f"Error: {response.json()}")
        
        print("-" * 50)
        return response.status_code == 200
        
    except FileNotFoundError:
        print(f"Error: Image file {image_path} not found.")
        return False
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the API. Make sure the server is running.")
        return False

def main():
    """Main test function."""
    print("Testing Receipt Management System API")
    print("=" * 50)
    
    # Test health endpoint
    if not test_health_endpoint():
        print("Health check failed. Exiting.")
        sys.exit(1)
    
    # Test root endpoint
    if not test_root_endpoint():
        print("Root endpoint test failed. Exiting.")
        sys.exit(1)
    
    # Test receipt processing if image provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"Testing receipt processing with image: {image_path}")
        test_receipt_processing(image_path)
    else:
        print("To test receipt processing, run:")
        print("python test_api.py path/to/receipt/image.jpg")
    
    print("\nAPI testing completed!")

if __name__ == "__main__":
    main() 