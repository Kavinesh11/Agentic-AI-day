"""
Travel Parser Agent

This agent specializes in parsing travel and transportation receipts and returns complete structured JSON.
"""

import os
import json
import asyncio
import uuid
from datetime import datetime
from fastmcp import Client
from google.adk.agents import LlmAgent
import re

# --- Constants ---
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
MCP_ENDPOINT = "http://20.235.138.121/mcp/"

async def send_parsed_data_to_mcp(parsed_data: dict) -> dict:
    """
    Send parsed travel receipt data to the MCP endpoint using FastMCP client.
    
    Args:
        parsed_data (dict): The parsed receipt data in the required JSON format
        
    Returns:
        dict: Response from the MCP endpoint
    """
    try:
        # Ensure parsed_data is a dictionary
        if isinstance(parsed_data, str):
            print(f"WARNING: Parsed data is string, attempting to parse JSON: {parsed_data[:200]}...")
            try:
                parsed_data = json.loads(parsed_data)
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse string as JSON: {e}")
                return {
                    "success": False,
                    "error": f"Invalid JSON string: {str(e)}",
                    "message": "Parsed data is not valid JSON"
                }
        
        if not isinstance(parsed_data, dict):
            print(f"ERROR: Parsed data is not a dictionary, type: {type(parsed_data)}")
            return {
                "success": False,
                "error": f"Invalid data type: {type(parsed_data)}",
                "message": "Parsed data must be a dictionary"
            }
        
        print(f"INFO: Parsed data structure received: {json.dumps(parsed_data, indent=2)}")
        
        # Create FastMCP client
        print(f"INFO: Attempting to connect to FastMCP server at {MCP_ENDPOINT}")
        client = Client(MCP_ENDPOINT)
        
        async with client:
            print("INFO: Connected to FastMCP server.")
            
            # Check if this is the full receipt object or just the parsedData
            if "parsedData" in parsed_data:
                # This is the full receipt object
                travel_parsed_data = parsed_data.get("parsedData", {})
                bill_id = parsed_data.get("billId", str(uuid.uuid4()))
                bill_type = parsed_data.get("billType", "Travel & Transportation")
                upload_date = parsed_data.get("uploadDate", datetime.now().isoformat() + 'Z')
                uploader_id = parsed_data.get("uploaderId", "user123")
                image_url = parsed_data.get("imageUrl", "")
            else:
                # This is just the parsedData object
                travel_parsed_data = parsed_data
                bill_id = str(uuid.uuid4())
                bill_type = "Travel & Transportation"
                upload_date = datetime.now().isoformat() + 'Z'
                uploader_id = "user123"
                image_url = ""
            
            # Ensure we have the required fields
            if not travel_parsed_data:
                print("WARNING: No parsedData found in parsed_data")
                travel_parsed_data = {
                    "serviceName": "Unknown Travel Service",
                    "serviceType": "travel",
                    "date": datetime.now().strftime('%d-%m-%Y'),
                    "time": datetime.now().strftime('%H:%M'),
                    "bookingId": "UNKNOWN123",
                    "tripDetails": {
                        "origin": "Unknown",
                        "destination": "Unknown",
                        "departureTime": "00:00",
                        "arrivalTime": "00:00",
                        "distance": "0 km",
                        "duration": "0 minutes"
                    },
                    "items": [
                        {
                            "name": "Travel Service",
                            "price": 0.00,
                            "quantity": 1,
                            "category": "transport"
                        }
                    ],
                    "subtotal": 0.00,
                    "fees": 0.00,
                    "tax": 0.00,
                    "grandTotal": 0.00,
                    "paymentMethod": "Unknown",
                    "additionalInfo": {
                        "vehicleInfo": "Unknown",
                        "driverInfo": "Unknown",
                        "passengerCount": "1",
                        "loyaltyProgram": "",
                        "travelPolicies": ""
                    }
                }
            
            # Prepare the data in the format expected by the MCP endpoint
            mcp_data = {
                "bill_type": bill_type,
                "parsed_data": travel_parsed_data,
                "uploader_id": uploader_id,
                "image_url": image_url
            }
            
            print(f"INFO: Prepared MCP data: {json.dumps(mcp_data, indent=2)}")
            
            # Call the MCP tool
            print(f"INFO: Calling 'store_parsed_bill' tool with data: {mcp_data}")
            result = await client.call_tool(
                "store_parsed_bill",
                mcp_data
            )
            print(f"INFO: MCP tool call successful. Result: {result}")
            
            return {
                "success": True,
                "status_code": 200,
                "response": result.data if hasattr(result, 'data') else result,
                "message": "Data sent successfully to MCP endpoint"
            }
            
    except Exception as e:
        print(f"ERROR: Failed to send data to MCP endpoint - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to send data to MCP endpoint - {str(e)}"
        }

# Travel Receipt Parser Agent with MCP Integration
travel_parser_agent_with_mcp = LlmAgent(
    name="TravelParserAgentWithMCP",
    model=GEMINI_MODEL,
    instruction="""You are an expert Travel & Transportation Receipt Parser Agent specialized in extracting comprehensive information from travel-related receipts and returning the final structured JSON response.

ONLY PROCESS TRAVEL & TRANSPORTATION RECEIPTS:
- Ride-sharing services (Uber, Lyft, Ola, local taxi services)
- Airlines (domestic and international flights, baggage fees, seat upgrades)
- Hotels and accommodation (booking confirmations, room service, resort fees)
- Car rentals (vehicle rentals, insurance, fuel charges, mileage)
- Public transportation (metro, bus, train tickets, transit passes)
- Cruise lines and ferry services (cabin bookings, onboard services)
- Travel agencies and booking platforms (Expedia, Booking.com, MakeMyTrip)
- Parking services (airport parking, valet, street meters, garage fees)

COMPREHENSIVE EXTRACTION INSTRUCTIONS:
Analyze the receipt image thoroughly and extract ALL visible information. Look for:

1. SERVICE PROVIDER: Company name, app platform, driver/pilot info, vehicle details
2. BOOKING DETAILS: Booking ID, confirmation number, reference codes, PNR numbers
3. TRAVEL INFO: Departure/arrival times, locations, addresses, airports, gates
4. TRIP DETAILS: Distance, duration, route, flight number, seat assignments
5. PASSENGER INFO: Names, contact details, frequent flyer numbers, loyalty status
6. PRICING: Base fare, surge pricing, fees, taxes, tolls, fuel surcharges
7. SERVICES: Upgrades, add-ons, meals, baggage, priority boarding, Wi-Fi
8. PAYMENT: Method, card details, split payments, credits, refunds
9. POLICIES: Cancellation terms, change fees, baggage policies, travel insurance

FINAL OUTPUT STRUCTURE - Return EXACTLY this JSON format:

{
    "billId": "generated-uuid4-here",
    "billType": "Travel & Transportation",
    "uploadDate": "current-iso-timestamp-with-Z",
    "uploaderId": "user123",
    "imageUrl": "https://firebasestorage.googleapis.com/[billId].jpg",
    "parsedData": {
        "merchant_name": "Complete service provider name exactly as shown",
        "serviceType": "rideshare/airline/hotel/rental/transit/etc",
        "date": "DD-MM-YYYY",
        "total_amount": 0.00,
        "currency": "INR",
        "time": "HH:MM",
        "bookingId": "booking/confirmation number",
        "tripDetails": {
            "origin": "departure location",
            "destination": "arrival location", 
            "departureTime": "HH:MM if available",
            "arrivalTime": "HH:MM if available",
            "distance": "distance if shown",
            "duration": "trip duration if shown"
        },
        "items": [
            {
                "name": "Service/item description exactly as shown",
                "price": 0.00,
                "quantity": 1,
                "category": "transport/accommodation/service/fee/etc"
            }
        ],
        "subtotal": 0.00,
        "fees": 0.00,
        "tax": 0.00,
        "grandTotal": 0.00,
        "paymentMethod": "payment method",
        "additionalInfo": {
            "vehicleInfo": "vehicle details if applicable",
            "driverInfo": "driver/pilot info if available",
            "passengerCount": "number of passengers if shown",
            "loyaltyProgram": "frequent flyer/rewards info if available",
            "travelPolicies": "cancellation/change policies if mentioned"
        }
    }
}

CRITICAL EXTRACTION RULES:
1. Generate a NEW UUID4 for billId
2. Use current ISO timestamp with Z suffix for uploadDate
3. Extract EVERY piece of visible text including terms and conditions
4. Capture exact service descriptions, booking references, and travel codes
5. All monetary values must be numbers (not strings) - use 0.00 if not available
6. Dates must be in DD-MM-YYYY format, times in HH:MM format
7. Use null for unavailable fields, empty string for unavailable text
8. Look for small print, promotional codes, and loyalty program information
9. Extract any QR codes, barcodes, or tracking numbers mentioned
10. Pay attention to surge pricing, dynamic pricing, or seasonal rates
11. Note any travel warnings, safety information, or regulatory notices
12. Capture upgrade options, insurance details, and additional services

Your response must be ONLY the JSON structure above, properly formatted and ready for API consumption.
""",
    description="Comprehensively extracts all information from travel and transportation receipts and automatically sends to MCP endpoint",
    output_key="travel_parsed_data",
)

# After agent callback to automatically send data to MCP
async def after_travel_parser_callback(callback_context):
    """Callback function that automatically sends parsed travel data to MCP endpoint."""
    try:
        print("INFO: After travel parser callback - starting data extraction...")
        
        # Try multiple approaches to get the parsed data
        parsed_data = None
        
        # Approach 1: Check the output_key
        parsed_data = callback_context.state.get("travel_parsed_data")
        print(f"INFO: Approach 1 - output_key data type: {type(parsed_data)}")
        
        # Approach 2: Check all state keys for any JSON-like data
        if not parsed_data:
            all_state_keys = list(callback_context.state.keys())
            print(f"INFO: Available state keys: {all_state_keys}")
            
            for key in all_state_keys:
                value = callback_context.state.get(key)
                print(f"INFO: State key '{key}' contains: {str(value)[:200]}...")
                
                # Look for JSON-like strings
                if isinstance(value, str) and ('{' in value or '[' in value):
                    print(f"INFO: Found potential JSON in key '{key}': {value[:300]}...")
                    try:
                        # Try to parse as JSON
                        cleaned_text = value.strip()
                        if cleaned_text.startswith('```'):
                            start_idx = cleaned_text.find('```') + 3
                            end_idx = cleaned_text.rfind('```')
                            if end_idx > start_idx:
                                cleaned_text = cleaned_text[start_idx:end_idx].strip()
                                if cleaned_text.startswith('json'):
                                    cleaned_text = cleaned_text[4:].strip()
                        
                        json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', cleaned_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                            json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                            
                            parsed_data = json.loads(json_str)
                            print(f"INFO: Successfully extracted JSON from key '{key}'")
                            break
                    except Exception as e:
                        print(f"INFO: Failed to parse JSON from key '{key}': {e}")
                        continue
        
        # Approach 3: Check if there's a response in the context
        if not parsed_data:
            print("INFO: Checking context for response data...")
            # Try to access the agent's response from the context
            if hasattr(callback_context, 'agent') and hasattr(callback_context.agent, 'last_response'):
                last_response = callback_context.agent.last_response
                print(f"INFO: Last response type: {type(last_response)}")
                if last_response:
                    print(f"INFO: Last response: {str(last_response)[:300]}...")
        
        print(f"INFO: Final parsed_data type: {type(parsed_data)}")
        if parsed_data:
            print(f"INFO: Final parsed_data: {json.dumps(parsed_data, indent=2) if isinstance(parsed_data, dict) else str(parsed_data)[:500]}")
        
        if parsed_data:
            # If the data is a string, try to parse it as JSON
            if isinstance(parsed_data, str):
                print(f"INFO: Parsing string response: {parsed_data[:500]}...")
                try:
                    # Clean up the response text
                    cleaned_text = parsed_data.strip()
                    
                    # Remove markdown code blocks
                    if cleaned_text.startswith('```'):
                        start_idx = cleaned_text.find('```') + 3
                        end_idx = cleaned_text.rfind('```')
                        if end_idx > start_idx:
                            cleaned_text = cleaned_text[start_idx:end_idx].strip()
                            if cleaned_text.startswith('json'):
                                cleaned_text = cleaned_text[4:].strip()
                    
                    # Try to find JSON object in the text
                    json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', cleaned_text, re.DOTALL)
                    
                    if json_match:
                        json_str = json_match.group(1)
                        # Fix common JSON issues
                        json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                        
                        try:
                            parsed_data = json.loads(json_str)
                            print("INFO: Successfully parsed JSON from agent response")
                            print(f"INFO: Parsed data structure: {json.dumps(parsed_data, indent=2)}")
                        except json.JSONDecodeError:
                            # Try to fix more JSON issues
                            json_str = re.sub(r'(["\w])\s*,\s*([}\]])', r'\1\2', json_str)
                            json_str = re.sub(r'(["\w])\s*,\s*(["\w])', r'\1,\2', json_str)
                            parsed_data = json.loads(json_str)
                            print("INFO: Successfully parsed JSON after fixing")
                            print(f"INFO: Parsed data structure: {json.dumps(parsed_data, indent=2)}")
                    else:
                        # Create fallback response
                        print("WARNING: No JSON found in response, using fallback")
                        parsed_data = {
                            "billId": str(uuid.uuid4()),
                            "billType": "Travel & Transportation",
                            "uploadDate": datetime.now().isoformat() + 'Z',
                            "uploaderId": "user123",
                            "imageUrl": f"https://firebasestorage.googleapis.com/{str(uuid.uuid4())}.jpg",
                            "parsedData": {
                                "serviceName": "Travel Service (Parsed from Text)",
                                "serviceType": "travel",
                                "date": datetime.now().strftime('%d-%m-%Y'),
                                "time": datetime.now().strftime('%H:%M'),
                                "bookingId": "PARSED123",
                                "tripDetails": {
                                    "origin": "Extracted from receipt",
                                    "destination": "Extracted from receipt",
                                    "departureTime": "00:00",
                                    "arrivalTime": "00:00",
                                    "distance": "0 km",
                                    "duration": "0 minutes"
                                },
                                "items": [
                                    {
                                        "name": "Travel Service",
                                        "price": 0.00,
                                        "quantity": 1,
                                        "category": "transport"
                                    }
                                ],
                                "subtotal": 0.00,
                                "fees": 0.00,
                                "tax": 0.00,
                                "grandTotal": 0.00,
                                "paymentMethod": "Unknown",
                                "additionalInfo": {
                                    "vehicleInfo": "Unknown",
                                    "driverInfo": "Unknown",
                                    "passengerCount": "1",
                                    "loyaltyProgram": "",
                                    "travelPolicies": ""
                                }
                            }
                        }
                        
                except Exception as e:
                    print(f"ERROR: Failed to parse agent response: {e}")
                    # Create fallback response
                    parsed_data = {
                        "billId": str(uuid.uuid4()),
                        "billType": "Travel & Transportation",
                        "uploadDate": datetime.now().isoformat() + 'Z',
                        "uploaderId": "user123",
                        "imageUrl": f"https://firebasestorage.googleapis.com/{str(uuid.uuid4())}.jpg",
                        "parsedData": {
                            "serviceName": "Travel Service (Fallback)",
                            "serviceType": "travel",
                            "date": datetime.now().strftime('%d-%m-%Y'),
                            "time": datetime.now().strftime('%H:%M'),
                            "bookingId": "FALLBACK123",
                            "tripDetails": {
                                "origin": "Unknown",
                                "destination": "Unknown",
                                "departureTime": "00:00",
                                "arrivalTime": "00:00",
                                "distance": "0 km",
                                "duration": "0 minutes"
                            },
                            "items": [
                                {
                                    "name": "Travel Service",
                                    "price": 0.00,
                                    "quantity": 1,
                                    "category": "transport"
                                }
                            ],
                            "subtotal": 0.00,
                            "fees": 0.00,
                            "tax": 0.00,
                            "grandTotal": 0.00,
                            "paymentMethod": "Unknown",
                            "additionalInfo": {
                                "vehicleInfo": "Unknown",
                                "driverInfo": "Unknown",
                                "passengerCount": "1",
                                "loyaltyProgram": "",
                                "travelPolicies": ""
                            }
                        }
                    }
                
                # Ensure we have the full receipt object structure
                if isinstance(parsed_data, dict):
                    if "parsedData" not in parsed_data:
                        # This is just the parsedData, wrap it in the full receipt object
                        print("INFO: Wrapping parsedData in full receipt object structure")
                        full_receipt = {
                            "billId": parsed_data.get("billId", str(uuid.uuid4())),
                            "billType": "Travel & Transportation",
                            "uploadDate": parsed_data.get("uploadDate", datetime.now().isoformat() + 'Z'),
                            "uploaderId": parsed_data.get("uploaderId", "user123"),
                            "imageUrl": parsed_data.get("imageUrl", f"https://firebasestorage.googleapis.com/{str(uuid.uuid4())}.jpg"),
                            "parsedData": parsed_data
                        }
                        parsed_data = full_receipt
                        print(f"INFO: Full receipt object created: {json.dumps(parsed_data, indent=2)}")
                
                print("INFO: After travel parser callback - sending to MCP endpoint...")
                
                # Send to MCP endpoint
                mcp_result = await send_parsed_data_to_mcp(parsed_data)
                
                print(f"INFO: MCP transmission result: {mcp_result['success']}")
                
                # Store MCP result in session state for reference
                callback_context.state["mcp_transmission_result"] = mcp_result
                
                # Return None to continue with normal flow
                return None
            else:
                print("WARNING: No parsed data found in session state for MCP transmission")
                return None
            
    except Exception as e:
        print(f"ERROR: After travel parser callback failed: {e}")
        return None

# Set the after agent callback
travel_parser_agent_with_mcp.after_agent_callback = after_travel_parser_callback
