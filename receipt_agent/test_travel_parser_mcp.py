#!/usr/bin/env python3
"""
Test script for Travel Parser Agent with MCP Integration

This script demonstrates how to use the enhanced travel parser agent
that automatically sends parsed data to the MCP endpoint.
"""

import asyncio
import json
from subagents.travel_parser_agent import (
    process_travel_receipt_and_send_to_mcp,
    process_travel_receipt_sync
)

async def test_async_travel_parser():
    """Test the async version of the travel parser with MCP integration."""
    print("🧪 Testing Async Travel Parser with MCP Integration")
    print("=" * 60)
    
    # Example travel receipt data (base64 encoded image or description)
    sample_image_data = """
    Travel Receipt Sample:
    Service: Uber
    Date: 15-01-2024
    Time: 14:30
    Booking ID: UBER123456
    Origin: San Francisco Airport
    Destination: Downtown San Francisco
    Distance: 12.5 km
    Duration: 25 minutes
    Base Fare: $25.00
    Service Fee: $2.50
    Tax: $2.25
    Total: $29.75
    Payment Method: Credit Card
    Driver: John Smith
    Vehicle: Toyota Camry (ABC-123)
    """
    
    try:
        # Process the receipt and send to MCP
        result = await process_travel_receipt_and_send_to_mcp(
            image_data=sample_image_data,
            user_id="test_user_001"
        )
        
        print("✅ Processing completed!")
        print(f"📊 Success: {result['success']}")
        print(f"🔍 Parsing Success: {result['parsing_success']}")
        print(f"📡 MCP Transmission: {result['mcp_transmission']['success']}")
        
        if result['parsed_data']:
            print("\n📋 Parsed Data Summary:")
            summary = result['processing_summary']
            print(f"   Bill ID: {summary['bill_id']}")
            print(f"   Service: {summary['service_name']}")
            print(f"   Total Amount: ${summary['total_amount']}")
            print(f"   MCP Endpoint: {summary['mcp_endpoint']}")
            print(f"   Timestamp: {summary['timestamp']}")
        
        if result['mcp_transmission']['success']:
            print(f"\n✅ MCP Response: {result['mcp_transmission']['message']}")
        else:
            print(f"\n❌ MCP Error: {result['mcp_transmission']['message']}")
        
        # Print full parsed data
        print("\n📄 Full Parsed Data:")
        print(json.dumps(result['parsed_data'], indent=2))
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

def test_sync_travel_parser():
    """Test the synchronous version of the travel parser with MCP integration."""
    print("\n🧪 Testing Sync Travel Parser with MCP Integration")
    print("=" * 60)
    
    # Example travel receipt data
    sample_image_data = """
    Travel Receipt Sample:
    Service: Delta Airlines
    Date: 20-01-2024
    Time: 09:15
    Booking ID: DL789012
    Flight: DL1234
    Origin: New York JFK
    Destination: Los Angeles LAX
    Departure: 09:15
    Arrival: 12:30
    Seat: 12A
    Passenger: Jane Doe
    Base Fare: $350.00
    Baggage Fee: $30.00
    Tax: $35.00
    Total: $415.00
    Payment Method: Credit Card
    """
    
    try:
        # Process the receipt and send to MCP
        result = process_travel_receipt_sync(
            image_data=sample_image_data,
            user_id="test_user_002"
        )
        
        print("✅ Processing completed!")
        print(f"📊 Success: {result['success']}")
        print(f"🔍 Parsing Success: {result['parsing_success']}")
        print(f"📡 MCP Transmission: {result['mcp_transmission']['success']}")
        
        if result['parsed_data']:
            print("\n📋 Parsed Data Summary:")
            summary = result['processing_summary']
            print(f"   Bill ID: {summary['bill_id']}")
            print(f"   Service: {summary['service_name']}")
            print(f"   Total Amount: ${summary['total_amount']}")
            print(f"   MCP Endpoint: {summary['mcp_endpoint']}")
            print(f"   Timestamp: {summary['timestamp']}")
        
        if result['mcp_transmission']['success']:
            print(f"\n✅ MCP Response: {result['mcp_transmission']['message']}")
        else:
            print(f"\n❌ MCP Error: {result['mcp_transmission']['message']}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

async def main():
    """Run all tests."""
    print("🚀 Starting Travel Parser Agent MCP Integration Tests")
    print("=" * 60)
    
    # Test async version
    await test_async_travel_parser()
    
    # Test sync version
    test_sync_travel_parser()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 