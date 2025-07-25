import base64
import logging
import json
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

from google.adk.agents.llm_agent import Agent
from google.adk.agents import LiveRequestQueue
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools import ToolContext
from google.genai import types as genai_types
from google.genai import Client
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH


logger = logging.getLogger(__name__)


class ReceiptInput(BaseModel):
    """Input schema for receipt processing."""
    image_data: bytes
    mime_type: str = "image/jpeg"
    input_mode: str  # "camera", "screenshot", "email"
    user_context: Optional[Dict[str, Any]] = None
    category_hint: Optional[str] = None


class ReceiptCategory(BaseModel):
    """Output schema for receipt categorization."""
    category: str
    amount: Optional[float]
    merchant: Optional[str]
    date: Optional[str]
    confidence: float
    detected_features: List[str]
    routing_agent: str
    processed_at: str


class InputHandlerAgent:
    def __init__(self):
        self.client = Client(vertexai=False)

        # Create the ADK agent with proper tool integration
        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="input_handler_agent",
            description="Processes receipt inputs from multiple sources and routes to specialized parsers",
            instruction="""  
            You are a receipt input handler responsible for:  
            1. Accepting receipt images from camera, screenshot, or email sources  
            2. Analyzing receipt content to categorize into specific types  
            3. Extracting key information (amount, merchant, date)  
            4. Routing categorized receipts to appropriate parser agents  
              
            Categories and routing:  
            - retail: E-commerce receipts (Amazon, Flipkart, Myntra) → retail_parser_agent  
            - food_dining: Restaurant/food delivery receipts → food_parser_agent    
            - miscellaneous: All other receipt types → misc_parser_agent  
              
            When processing receipts:  
            - Use vision capabilities to analyze receipt content  
            - Look for key indicators like merchant names, item types, layout patterns  
            - Consider any user-provided context or category hints  
            - Extract structured data accurately  
            - Route to the correct parser agent based on categorization  
            """,
            tools=[
                self.classify_receipt,
                self.save_receipt_with_classification,
                self.process_receipt_stream,
                self.route_to_parser
            ],
            generate_content_config=genai_types.GenerateContentConfig(
                safety_settings=[
                    genai_types.SafetySetting(
                        category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
            ),
        )

        self.retail_parser = RemoteA2aAgent(
            name="retail_parser_agent",
            description="Specialized parser for retail receipts",
            agent_card=f"http://localhost:8001/a2a/retail_parser{AGENT_CARD_WELL_KNOWN_PATH}"
        )

        self.food_parser = RemoteA2aAgent(
            name="food_parser_agent",
            description="Specialized parser for food & dining receipts",
            agent_card=f"http://localhost:8002/a2a/food_parser{AGENT_CARD_WELL_KNOWN_PATH}"
        )

        self.misc_parser = RemoteA2aAgent(
            name="misc_parser_agent",
            description="Specialized parser for miscellaneous receipts",
            agent_card=f"http://localhost:8003/a2a/misc_parser{AGENT_CARD_WELL_KNOWN_PATH}"
        )

        # Update the main agent to include sub_agents for A2A routing
        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="input_handler_agent",
            description="Processes receipt inputs from multiple sources and routes to specialized parsers",
            instruction="""  
            You are a receipt input handler responsible for:  
            1. Accepting receipt images from camera, screenshot, or email sources  
            2. Analyzing receipt content to categorize into specific types  
            3. Extracting key information (amount, merchant, date)  
            4. Routing categorized receipts to appropriate parser agents via A2A communication  
              
            Categories and routing:  
            - retail: E-commerce receipts (Amazon, Flipkart, Myntra) → delegate to retail_parser_agent  
            - food_dining: Restaurant/food delivery receipts → delegate to food_parser_agent    
            - miscellaneous: All other receipt types → delegate to misc_parser_agent  
              
            When processing receipts:  
            - Use vision capabilities to analyze receipt content  
            - Look for key indicators like merchant names, item types, layout patterns  
            - Consider any user-provided context or category hints  
            - Extract structured data accurately  
            - Route to the correct parser agent based on categorization using sub-agent delegation  
            """,
            tools=[
                self.classify_receipt,
                self.save_receipt_with_classification,
                self.process_receipt_stream
            ],
            sub_agents=[
                self.retail_parser,
                self.food_parser,
                self.misc_parser
            ],
            generate_content_config=genai_types.GenerateContentConfig(
                safety_settings=[
                    genai_types.SafetySetting(
                        category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
            ),
        )

    async def route_to_parser(self, classification: Dict[str, Any], receipt_data: Dict[str, Any]) -> str:
        """Route categorized receipt to appropriate parser agent using A2A communication."""

        category = classification.get("category", "miscellaneous")
        routing_agent = classification.get(
            "routing_agent", "misc_parser_agent")

        # Select the appropriate parser based on category
        if category == "retail":
            parser_agent = self.retail_parser
        elif category == "food_dining":
            parser_agent = self.food_parser
        else:
            parser_agent = self.misc_parser

        try:
            # Create a JSON message with all the data
            message = json.dumps({
                "message": f"Parse this {category} receipt",
                "receipt_data": receipt_data,
                "classification": classification
            })
            
            # Use A2A communication to send receipt data to parser
            parsing_result = await parser_agent.run_async(
                parent_context=None,  # Provide the required parent_context parameter
                message=message
            )

            return f"Successfully routed {category} receipt to {routing_agent}. Parsing result: {parsing_result}"

        except Exception as e:
            logger.error(f"Failed to route to {routing_agent}: {e}")
            return f"Failed to route {category} receipt to {routing_agent}: {str(e)}"

    async def classify_receipt(self, image_data: bytes, mime_type: str = "image/jpeg", user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Classify a receipt image and extract key information."""

        # Create image part from receipt data
        image_part = genai_types.Part.from_bytes(
            data=image_data, mime_type=mime_type
        )

        # Enhanced prompt for better categorization
        prompt_text = """  
        Analyze this receipt image and provide the following information in JSON format:  
        {  
            "category": "one of: retail, food_dining, miscellaneous",  
            "amount": "total amount as number or null if not visible",  
            "merchant": "merchant/store name or null if not visible",   
            "date": "date in YYYY-MM-DD format or null if not visible",  
            "confidence": "confidence level from 0.0 to 1.0",  
            "detected_features": ["list of key features that led to categorization"],  
            "routing_agent": "suggested parser agent based on category"  
        }  
          
        Category guidelines:  
        - retail: E-commerce sites (Amazon, Flipkart, Myntra), shopping malls, electronics stores  
        - food_dining: Restaurants, cafes, food delivery (Zomato, Swiggy), groceries  
        - miscellaneous: Everything else (utilities, transport, healthcare, etc.)  
          
        Be accurate and only extract information that is clearly visible.  
        """

        contents = genai_types.Content(
            role="user",
            parts=[image_part, genai_types.Part.from_text(text=prompt_text)],
        )

        response = await self.client.models.generate_content_async(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction="You are a receipt analysis assistant. Extract information accurately from receipt images and return valid JSON."
            ),
        )

        try:
            result_text = response.candidates[0].content.parts[0].text.strip()
            # Clean up the response to extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            result = json.loads(result_text)
            result["processed_at"] = datetime.now().isoformat()

            # Add routing logic
            category_to_agent = {
                "retail": "retail_parser_agent",
                "food_dining": "food_parser_agent",
                "miscellaneous": "misc_parser_agent"
            }
            result["routing_agent"] = category_to_agent.get(
                result.get("category"), "misc_parser_agent")

            return result
        except (json.JSONDecodeError, IndexError) as e:
            return {
                "category": "miscellaneous",
                "amount": None,
                "merchant": None,
                "date": None,
                "confidence": 0.0,
                "detected_features": [],
                "routing_agent": "misc_parser_agent",
                "error": f"Failed to parse response: {str(e)}",
                "processed_at": datetime.now().isoformat()
            }

    async def save_receipt_with_classification(
        self,
        tool_context: ToolContext,
        image_data: bytes,
        mime_type: str,
        classification: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """Save receipt image as artifact with classification metadata."""

        try:
            # Create artifact part for the receipt image
            receipt_artifact = genai_types.Part(
                inline_data=genai_types.Blob(
                    mime_type=mime_type,
                    data=image_data
                )
            )

            # Save the receipt image
            await tool_context.save_artifact(f'receipt_{filename}', receipt_artifact)

            # Prepare metadata with classification results
            metadata = {
                "filename": filename,
                "mime_type": mime_type,
                "classification": classification,
                "saved_at": datetime.now().isoformat(),
                "size_bytes": len(image_data)
            }

            # Save classification metadata as JSON
            metadata_json = json.dumps(metadata, indent=2)
            metadata_artifact = genai_types.Part(
                inline_data=genai_types.Blob(
                    mime_type='application/json',
                    data=metadata_json.encode('utf-8')
                )
            )

            await tool_context.save_artifact(f'receipt_metadata_{filename}', metadata_artifact)

            return {
                "status": "saved",
                "filename": filename,
                "classification": classification,
                "metadata": metadata
            }

        except Exception as e:
            return {
                "status": "error",
                "filename": filename,
                "error": str(e)
            }

    async def process_receipt_stream(
        self,
        input_stream: LiveRequestQueue
    ) -> AsyncGenerator[str, None]:
        """Process receipt images from live camera stream."""

        while True:
            last_valid_receipt = None

            # Get the latest receipt image from the queue, discarding older ones
            while input_stream._queue.qsize() != 0:
                live_req = await input_stream.get()

                if (live_req.blob is not None and
                        live_req.blob.mime_type in ["image/jpeg", "image/png"]):
                    last_valid_receipt = live_req

            # Process the receipt if we have one
            if last_valid_receipt is not None:
                try:
                    # Classify the receipt
                    classification = await self.classify_receipt(
                        last_valid_receipt.blob.data,
                        last_valid_receipt.blob.mime_type
                    )

                    # Format the result for streaming
                    result = {
                        "type": "receipt_processed",
                        "timestamp": datetime.now().isoformat(),
                        "classification": classification,
                        "mime_type": last_valid_receipt.blob.mime_type
                    }

                    yield json.dumps(result)

                except Exception as e:
                    error_result = {
                        "type": "processing_error",
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    }
                    yield json.dumps(error_result)

            # Small delay to prevent excessive CPU usage
            await asyncio.sleep(0.5)

    async def route_to_parser(self, classification: Dict[str, Any], receipt_data: Dict[str, Any]) -> str:
        """Route categorized receipt to appropriate parser agent using A2A communication."""

        routing_agent = classification.get(
            "routing_agent", "misc_parser_agent")
        category = classification.get("category", "miscellaneous")

        # This would integrate with A2A communication to route to parser agents
        # For now, return routing information
        return f"Routed {category} receipt to {routing_agent} with confidence {classification.get('confidence', 0.0)}"

    async def get_receipt_categories(self) -> Dict[str, str]:
        """Get available receipt categories with descriptions."""
        return {
            "retail": "E-commerce and shopping receipts (Amazon, Flipkart, Myntra)",
            "food_dining": "Restaurant, cafe, and food delivery receipts",
            "miscellaneous": "All other receipt types (utilities, transport, healthcare, etc.)"
        }


# Create the input handler agent instance
input_handler_agent = InputHandlerAgent()

# Export the ADK agent for use in the system
root_agent = input_handler_agent.agent
