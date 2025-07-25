import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from google.adk.agents.llm_agent import Agent
from google.genai import types as genai_types
from google.genai import Client

logger = logging.getLogger(__name__)


class FoodParserAgent:
    def __init__(self):
        self.client = Client(vertexai=False)

        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="food_parser_agent",
            description="Specialized parser for food and dining receipts",
            instruction="""  
            You are a food & dining receipt parser specialized in extracting structured data from:  
            - Restaurant receipts  
            - Food delivery receipts (Zomato, Swiggy, Uber Eats)  
            - Cafe and fast food receipts  
            - Grocery store receipts  
              
            Extract the following information:  
            - Restaurant/establishment name  
            - Order ID and table number  
            - Food items with prices  
            - Service charges and tips  
            - GST and tax breakdown  
            - Payment method  
            - Delivery information (if applicable)  
              
            Return structured JSON data following the food & dining receipt schema.  
            """,
            tools=[
                self.parse_food_receipt,
                self.calculate_tip_percentage,
                self.extract_delivery_info
            ],
            generate_content_config=genai_types.GenerateContentConfig(
                temperature=0.1,
                safety_settings=[
                    genai_types.SafetySetting(
                        category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
            ),
        )

    async def parse_food_receipt(self, image_data: bytes, mime_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse food & dining receipt and extract structured data."""

        image_part = genai_types.Part.from_bytes(
            data=image_data, mime_type=mime_type
        )

        prompt_text = """  
        Parse this food & dining receipt and extract the following information in JSON format:  
        {  
            "restaurantName": "restaurant or establishment name",  
            "restaurantAddress": "restaurant address if visible",  
            "date": "dining date in YYYY-MM-DD format",  
            "time": "dining time if visible",  
            "tableNumber": "table number if applicable",  
            "numberOfGuests": "number of guests if mentioned",  
            "orderId": "order ID or bill number",  
            "items": [  
                {  
                    "name": "food item name",  
                    "quantity": "quantity ordered",  
                    "unitPrice": "price per unit",  
                    "totalPrice": "total price for this item",  
                    "category": "food category (appetizer, main, dessert, beverage)"  
                }  
            ],  
            "subtotal": "subtotal amount",  
            "serviceCharge": "service charge amount",  
            "gst": "GST/tax amount",  
            "deliveryCharge": "delivery charge if applicable",  
            "packagingCharge": "packaging charge if applicable",  
            "discount": "discount amount if applicable",  
            "grandTotal": "final total amount",  
            "tipAmount": "tip amount if mentioned",  
            "paymentMethod": "payment method used",  
            "deliveryAddress": "delivery address if applicable",  
            "deliveryTime": "estimated delivery time if mentioned"  
        }  
          
        Focus on accuracy and only extract clearly visible information.  
        """

        contents = genai_types.Content(
            role="user",
            parts=[image_part, genai_types.Part.from_text(text=prompt_text)],
        )

        response = await self.client.models.generate_content_async(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction="You are a food & dining receipt parsing specialist. Extract accurate structured data from restaurant and food delivery receipts."
            ),
        )

        try:
            result_text = response.candidates[0].content.parts[0].text.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            parsed_data = json.loads(result_text)

            return {
                "billType": "Food & Dining",
                "uploadDate": datetime.now().isoformat(),
                "uploaderId": metadata.get("user_id", "unknown"),
                "imageUrl": metadata.get("image_url", ""),
                "parsedData": parsed_data
            }

        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse food receipt: {e}")
            return {
                "billType": "Food & Dining",
                "uploadDate": datetime.now().isoformat(),
                "uploaderId": metadata.get("user_id", "unknown"),
                "imageUrl": metadata.get("image_url", ""),
                "parsedData": {},
                "error": f"Parsing failed: {str(e)}"
            }

    async def calculate_tip_percentage(self, subtotal: float, tip_amount: float) -> Dict[str, Any]:
        """Calculate tip percentage and provide insights."""
        if subtotal <= 0:
            return {"tip_percentage": 0, "tip_category": "no_tip"}

        tip_percentage = (tip_amount / subtotal) * 100

        if tip_percentage == 0:
            category = "no_tip"
        elif tip_percentage < 10:
            category = "low_tip"
        elif tip_percentage <= 20:
            category = "standard_tip"
        else:
            category = "generous_tip"

        return {
            "tip_percentage": round(tip_percentage, 2),
            "tip_category": category,
            "tip_amount": tip_amount
        }

    async def extract_delivery_info(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure delivery-specific information."""
        delivery_info = {}

        if "deliveryAddress" in parsed_data and parsed_data["deliveryAddress"]:
            delivery_info["is_delivery"] = True
            delivery_info["delivery_address"] = parsed_data["deliveryAddress"]
            delivery_info["delivery_charge"] = parsed_data.get(
                "deliveryCharge", 0)
            delivery_info["packaging_charge"] = parsed_data.get(
                "packagingCharge", 0)
        else:
            delivery_info["is_delivery"] = False
            delivery_info["dining_type"] = "dine_in" if parsed_data.get(
                "tableNumber") else "takeaway"

        return delivery_info


# Create the food parser agent instance
food_parser_agent = FoodParserAgent()
