"""
MCP Integration Template

This template provides reusable functions and patterns for integrating MCP 
with any parser agent. Use this as a reference for adding MCP to parser agents.
"""

import os
import json
import asyncio
import uuid
from datetime import datetime
from fastmcp import Client
import re

# --- Constants ---
MCP_ENDPOINT = "http://20.235.138.121/mcp/"

async def send_parsed_data_to_mcp(parsed_data: dict, bill_type: str = "General") -> dict:
    """
    Generic function to send parsed receipt data to the MCP endpoint.
    
    Args:
        parsed_data (dict): The parsed receipt data in the required JSON format
        bill_type (str): The type of bill (e.g., "Food & Dining", "Retail & Shopping", etc.)
        
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
                parsed_data_content = parsed_data.get("parsedData", {})
                bill_id = parsed_data.get("billId", str(uuid.uuid4()))
                bill_type_final = parsed_data.get("billType", bill_type)
                upload_date = parsed_data.get("uploadDate", datetime.now().isoformat() + 'Z')
                uploader_id = parsed_data.get("uploaderId", "user123")
                image_url = parsed_data.get("imageUrl", "")
            else:
                # This is just the parsedData object
                parsed_data_content = parsed_data
                bill_id = str(uuid.uuid4())
                bill_type_final = bill_type
                upload_date = datetime.now().isoformat() + 'Z'
                uploader_id = "user123"
                image_url = ""
            
            # Prepare the data in the format expected by the MCP endpoint
            mcp_data = {
                "bill_type": bill_type_final,
                "parsed_data": parsed_data_content,
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

def create_after_agent_callback(bill_type: str, output_key: str):
    """
    Factory function to create an after_agent_callback for any parser agent.
    
    Args:
        bill_type (str): The bill type for this agent (e.g., "Food & Dining")
        output_key (str): The output key for this agent (e.g., "food_parsed_data")
        
    Returns:
        function: The callback function ready to be assigned to an agent
    """
    async def after_parser_callback(callback_context):
        """Callback function that automatically sends parsed data to MCP endpoint."""
        try:
            print(f"INFO: After {bill_type} parser callback - starting data extraction...")
            
            # Try multiple approaches to get the parsed data
            parsed_data = None
            
            # Approach 1: Check the output_key
            parsed_data = callback_context.state.get(output_key)
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
                            "billType": bill_type,
                            "uploadDate": parsed_data.get("uploadDate", datetime.now().isoformat() + 'Z'),
                            "uploaderId": parsed_data.get("uploaderId", "user123"),
                            "imageUrl": parsed_data.get("imageUrl", f"https://firebasestorage.googleapis.com/{str(uuid.uuid4())}.jpg"),
                            "parsedData": parsed_data
                        }
                        parsed_data = full_receipt
                
                print(f"INFO: After {bill_type} parser callback - sending to MCP endpoint...")
                
                # Send to MCP endpoint
                mcp_result = await send_parsed_data_to_mcp(parsed_data, bill_type)
                
                print(f"INFO: MCP transmission result: {mcp_result['success']}")
                
                # Store MCP result in session state for reference
                callback_context.state["mcp_transmission_result"] = mcp_result
                
                # Return None to continue with normal flow
                return None
            else:
                print(f"WARNING: No parsed data found in session state for {bill_type} MCP transmission")
                return None
                
        except Exception as e:
            print(f"ERROR: After {bill_type} parser callback failed: {e}")
            return None
    
    return after_parser_callback

# Helper function to add MCP integration to any parser agent
def add_mcp_integration_to_agent(agent, bill_type: str, output_key: str):
    """
    Add MCP integration to an existing parser agent.
    
    Args:
        agent: The LlmAgent instance
        bill_type (str): The bill type for this agent
        output_key (str): The output key for this agent
    """
    # Create and assign the callback
    callback_function = create_after_agent_callback(bill_type, output_key)
    agent.after_agent_callback = callback_function
    
    print(f"INFO: MCP integration added to {agent.name} for {bill_type}")
    return agent
