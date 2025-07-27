"""
Retail Parser Agent

This agent specializes in parsing retail store receipts and returns complete structured JSON.
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
    Send parsed retail receipt data to the MCP endpoint using FastMCP client.
    
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
                retail_parsed_data = parsed_data.get("parsedData", {})
                bill_id = parsed_data.get("billId", str(uuid.uuid4()))
                bill_type = parsed_data.get("billType", "Retail & Shopping")
                upload_date = parsed_data.get("uploadDate", datetime.now().isoformat() + 'Z')
                uploader_id = parsed_data.get("uploaderId", "user123")
                image_url = parsed_data.get("imageUrl", "")
            else:
                # This is just the parsedData object
                retail_parsed_data = parsed_data
                bill_id = str(uuid.uuid4())
                bill_type = "Retail & Shopping"
                upload_date = datetime.now().isoformat() + 'Z'
                uploader_id = "user123"
                image_url = ""
            
            # Prepare the data in the format expected by the MCP endpoint
            mcp_data = {
                "bill_type": bill_type,
                "parsed_data": retail_parsed_data,
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

# Retail Receipt Parser Agent
retail_parser_agent = LlmAgent(
    name="RetailParserAgent",
    model=GEMINI_MODEL,
    instruction="""You are an expert Retail Receipt Parser Agent specialized in extracting comprehensive information from retail store receipts and returning the final structured JSON response.

ONLY PROCESS RETAIL RECEIPTS:
- Department stores (Macy's, Target, Walmart, etc.)
- Electronics stores (Best Buy, Apple Store, local electronics shops)
- Clothing and fashion stores (H&M, Zara, Nike, local boutiques)
- Specialty stores (bookstores, toy stores, sporting goods, jewelry)
- Online retail pickups (Amazon, Flipkart, etc.)
- Pharmacy retail sections, home improvement stores, beauty stores

COMPREHENSIVE EXTRACTION INSTRUCTIONS:
Analyze the receipt image thoroughly and extract ALL visible information. Look for:

1. STORE INFORMATION: Name, location, contact details, store codes, franchise info
2. TRANSACTION DETAILS: Date, time, transaction IDs, cashier info, register details
3. PRODUCT ITEMS: Names, brands, models, SKUs, sizes, colors, descriptions
4. PRICING: Individual prices, quantities, unit costs, bulk pricing, sale prices
5. DISCOUNTS: Coupons, sales, member discounts, clearance, price matching
6. TAXES: Sales tax, VAT, local taxes with rates and amounts
7. PAYMENT: Method, card details, cash handling, gift cards, store credit
8. POLICIES: Return policy, warranty info, exchange terms
9. LOYALTY: Rewards programs, points earned/used, membership details
10. ADDITIONAL: Promotions, seasonal sales, employee discounts, special offers

FINAL OUTPUT STRUCTURE - Return EXACTLY this JSON format:

{
    "billId": "generated-uuid4-here",
    "billType": "Retail & Shopping",
    "uploadDate": "current-iso-timestamp-with-Z",
    "uploaderId": "user123",
    "imageUrl": "https://firebasestorage.googleapis.com/[billId].jpg",
    "parsedData": {
        "merchant_name": "Complete store name exactly as shown",
        "date": "DD-MM-YYYY",
        "total_amount": 0.00,
        "currency": "INR",
        "time": "HH:MM",
        "storeNumber": "store number or null",
        "transactionId": "transaction number",
        "items": [
            {
                "name": "Product name exactly as shown",
                "price": 0.00,
                "quantity": 1,
                "brand": "brand name if available",
                "sku": "SKU if available",
                "category": "product category"
            }
        ],
        "subtotal": 0.00,
        "discount": 0.00,
        "tax": 0.00,
        "total_amount": 0.00,
        "paymentMethod": "payment method",
        "additionalInfo": {
            "returnPolicy": "return policy if shown",
            "loyaltyProgram": "loyalty info if available",
            "promotions": "current promotions or offers",
            "warrantyInfo": "warranty information if available"
        }
    }
}

CRITICAL EXTRACTION RULES:
1. Generate a NEW UUID4 for billId
2. Use current ISO timestamp with Z suffix for uploadDate
3. Extract EVERY piece of visible text including headers, footers, and fine print
4. All monetary values must be numbers (not strings) - use 0.00 if not available
5. Dates must be in DD-MM-YYYY format, times in HH:MM format
6. Use null for unavailable fields, empty string for unavailable text
7. Look for small text, promotional messages, and legal disclaimers
8. Extract barcodes, QR codes, or reference numbers mentioned
9. Capture seasonal promotions, limited-time offers, and special events
10. Note employee information, manager signatures, or approval codes

Your response must be ONLY the JSON structure above, properly formatted and ready for API consumption.
""",
    description="Comprehensively extracts all information from retail store receipts and automatically sends to MCP endpoint",
    output_key="retail_parsed_data",
)

# After agent callback to automatically send data to MCP
async def after_retail_parser_callback(callback_context):
    """Callback function that automatically sends parsed retail data to MCP endpoint."""
    try:
        print("INFO: After retail parser callback - starting data extraction...")
        
        # Try multiple approaches to get the parsed data
        parsed_data = None
        
        # Approach 1: Check the output_key
        parsed_data = callback_context.state.get("retail_parsed_data")
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
                        "billType": "Retail & Shopping",
                        "uploadDate": parsed_data.get("uploadDate", datetime.now().isoformat() + 'Z'),
                        "uploaderId": parsed_data.get("uploaderId", "user123"),
                        "imageUrl": parsed_data.get("imageUrl", f"https://firebasestorage.googleapis.com/{str(uuid.uuid4())}.jpg"),
                        "parsedData": parsed_data
                    }
                    parsed_data = full_receipt
            
            print("INFO: After retail parser callback - sending to MCP endpoint...")
            
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
            print("WARNING: No parsed data found in session state for Retail MCP transmission")
            return None
            
    except Exception as e:
        print(f"ERROR: After retail parser callback failed: {e}")
        return None

# Set the after agent callback
retail_parser_agent.after_agent_callback = after_retail_parser_callback 