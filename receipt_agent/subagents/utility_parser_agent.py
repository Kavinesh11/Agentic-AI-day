"""
Utility Parser Agent

This agent specializes in parsing utility bills and returns complete structured JSON.
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
    Send parsed utility bill data to the MCP endpoint using FastMCP client.
    
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
                utility_parsed_data = parsed_data.get("parsedData", {})
                bill_id = parsed_data.get("billId", str(uuid.uuid4()))
                bill_type = parsed_data.get("billType", "Utility Bills")
                upload_date = parsed_data.get("uploadDate", datetime.now().isoformat() + 'Z')
                uploader_id = parsed_data.get("uploaderId", "user123")
                image_url = parsed_data.get("imageUrl", "")
            else:
                # This is just the parsedData object
                utility_parsed_data = parsed_data
                bill_id = str(uuid.uuid4())
                bill_type = "Utility Bills"
                upload_date = datetime.now().isoformat() + 'Z'
                uploader_id = "user123"
                image_url = ""
            
            # Prepare the data in the format expected by the MCP endpoint
            mcp_data = {
                "bill_type": bill_type,
                "parsed_data": utility_parsed_data,
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
                "response": result,
                "message": "Data sent successfully to MCP endpoint"
            }
            
    except Exception as e:
        print(f"ERROR: Failed to send data to MCP endpoint - {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to send data to MCP endpoint - {str(e)}"
        }

# Utility Bill Parser Agent
utility_parser_agent = LlmAgent(
    name="UtilityParserAgent",
    model=GEMINI_MODEL,
    instruction="""You are an expert Utility Bill Parser Agent specialized in extracting comprehensive information from utility bills and returning the final structured JSON response.

ONLY PROCESS UTILITY BILLS:
- Electricity bills (power companies, renewable energy providers, municipal utilities)
- Water and sewer bills (municipal water departments, private water companies)
- Natural gas bills (gas companies, propane services, heating utilities)
- Internet and cable bills (ISPs, cable providers, fiber optic services)
- Phone bills (landline, mobile carriers, VoIP services)
- Waste management (garbage collection, recycling services, hazardous waste)
- Municipal services (property taxes, city services, special assessments)

COMPREHENSIVE EXTRACTION INSTRUCTIONS:
Analyze the receipt image thoroughly and extract ALL visible information. Look for:

1. UTILITY PROVIDER: Company name, logo, service territory, contact information
2. ACCOUNT INFO: Customer ID, account number, service address, billing address
3. BILLING PERIOD: Service dates, billing cycle, meter reading dates, due dates
4. USAGE DATA: Consumption amounts, units (kWh, gallons, therms, GB), meter readings
5. RATE STRUCTURE: Rate schedules, tier pricing, time-of-use rates, demand charges
6. CHARGES: Base charges, usage charges, delivery fees, connection fees, taxes
7. ADJUSTMENTS: Credits, rebates, late fees, deposits, previous balance
8. PAYMENT: Amount due, payment methods, autopay settings, payment history
9. REGULATORY: Taxes, surcharges, environmental fees, government charges

FINAL OUTPUT STRUCTURE - Return EXACTLY this JSON format:

{
    "billId": "generated-uuid4-here",
    "billType": "Utility Bills",
    "uploadDate": "current-iso-timestamp-with-Z",
    "uploaderId": "user123",
    "imageUrl": "https://firebasestorage.googleapis.com/[billId].jpg",
    "parsedData": {
        "merchant_name": "Complete utility company name exactly as shown",
        "utilityType": "electricity/water/gas/internet/phone/waste/municipal",
        "billDate": "DD-MM-YYYY",
        "dueDate": "DD-MM-YYYY",
        "totalAmount": 0.00,
        "currency": "INR",
        "customerId": "customer/account ID number",
        "serviceAddress": "service location address",
        "billingPeriod": {
            "startDate": "DD-MM-YYYY",
            "endDate": "DD-MM-YYYY",
            "days": 0
        },
        "usage": {
            "currentReading": "current meter reading",
            "previousReading": "previous meter reading", 
            "consumption": 0.00,
            "unit": "kWh/gallons/therms/GB/minutes/etc"
        },
        "charges": [
            {
                "description": "Charge description exactly as shown",
                "amount": 0.00,
                "category": "base/usage/delivery/fee/tax/adjustment"
            }
        ],
        "previousBalance": 0.00,
        "currentCharges": 0.00,
        "adjustments": 0.00,
        "totalAmountDue": 0.00,
        "paymentMethod": "payment method if specified",
        "additionalInfo": {
            "rateSchedule": "rate plan or schedule if shown",
            "peakHours": "time-of-use details if applicable",
            "environmentalPrograms": "green energy or conservation programs",
            "customerPrograms": "assistance programs or special rates",
            "regulatoryInfo": "PUC info or regulatory notices"
        },
        "additionalNotes": "any other relevant notes or fine print or user context"
    }
}

CRITICAL EXTRACTION RULES:
1. Generate a NEW UUID4 for billId
2. Use current ISO timestamp with Z suffix for uploadDate
3. Extract EVERY piece of visible text including regulatory disclaimers
4. Capture exact utility account numbers, meter readings, and rate schedules
5. All monetary values must be numbers (not strings) - use 0.00 if not available
6. Dates must be in DD-MM-YYYY format
7. Use null for unavailable fields, empty string for unavailable text
8. Look for small print, regulatory notices, and environmental programs
9. Extract any QR codes, barcodes, or payment reference numbers
10. Pay attention to tier pricing, peak/off-peak rates, and seasonal adjustments
11. Note any energy efficiency tips, conservation programs, or rebate information
12. Capture customer service information and emergency contact numbers

Your response must be ONLY the JSON structure above, properly formatted and ready for API consumption.
""",
    description="Comprehensively extracts all information from utility bills and automatically sends to MCP endpoint",
    output_key="utility_parsed_data",
)

# After agent callback to automatically send data to MCP
async def after_utility_parser_callback(callback_context):
    """Callback function that automatically sends parsed utility data to MCP endpoint."""
    try:
        print("INFO: After utility parser callback - starting data extraction...")
        
        # Try multiple approaches to get the parsed data
        parsed_data = None
        
        # Approach 1: Check the output_key
        parsed_data = callback_context.state.get("utility_parsed_data")
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
        
        if parsed_data:
            # Handle string responses
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
                        except json.JSONDecodeError:
                            # Try to fix more JSON issues
                            json_str = re.sub(r'(["\w])\s*,\s*([}\]])', r'\1\2', json_str)
                            json_str = re.sub(r'(["\w])\s*,\s*(["\w])', r'\1,\2', json_str)
                            parsed_data = json.loads(json_str)
                            print("INFO: Successfully parsed JSON after fixing")
                        
                except Exception as e:
                    print(f"ERROR: Failed to parse agent response: {e}")
                    parsed_data = None
            
            # Ensure we have the full receipt object structure
            if isinstance(parsed_data, dict):
                if "parsedData" not in parsed_data:
                    # This is just the parsedData, wrap it in the full receipt object
                    print("INFO: Wrapping parsedData in full receipt object structure")
                    full_receipt = {
                        "billId": parsed_data.get("billId", str(uuid.uuid4())),
                        "billType": "Utility Bills",
                        "uploadDate": parsed_data.get("uploadDate", datetime.now().isoformat() + 'Z'),
                        "uploaderId": parsed_data.get("uploaderId", "user123"),
                        "imageUrl": parsed_data.get("imageUrl", f"https://firebasestorage.googleapis.com/{str(uuid.uuid4())}.jpg"),
                        "parsedData": parsed_data
                    }
                    parsed_data = full_receipt
            
            print("INFO: After utility parser callback - sending to MCP endpoint...")
            
            # Send to MCP endpoint only if we have valid data
            if parsed_data and isinstance(parsed_data, dict):
                mcp_result = await send_parsed_data_to_mcp(parsed_data)
                
                print(f"INFO: MCP transmission result: {mcp_result['success']}")
                
                # Store MCP result in session state for reference
                callback_context.state["mcp_transmission_result"] = mcp_result
            else:
                print("WARNING: Invalid parsed data for MCP transmission")
            
            # Return None to continue with normal flow
            return None
        else:
            print("WARNING: No parsed data found in session state for Utility MCP transmission")
            return None
            
    except Exception as e:
        print(f"ERROR: After utility parser callback failed: {e}")
        return None

# Set the after agent callback
utility_parser_agent.after_agent_callback = after_utility_parser_callback
