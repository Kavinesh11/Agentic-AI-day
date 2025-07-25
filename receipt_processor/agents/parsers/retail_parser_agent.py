
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from google.adk.agents.llm_agent import Agent
from google.genai import types as genai_types
from google.genai import Client

logger = logging.getLogger(__name__)


class RetailReceiptData(BaseModel):
    """Schema for retail receipt parsed data."""
    billType: str = "Retail"
    uploadDate: str
    uploaderId: str
    imageUrl: str
    parsedData: Dict[str, Any]


class RetailParserAgent:
    def __init__(self):
        self.client = Client(vertexai=False)

        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="retail_parser_agent",
            description="Specialized parser for retail and e-commerce receipts",
            instruction="""  
            You are a retail receipt parser specialized in extracting structured data from:  
            - E-commerce receipts (Amazon, Flipkart, Myntra)  
            - Shopping mall receipts  
            - Electronics store receipts  
              
            Extract the following information:  
            - Invoice number/Order ID  
            - SKU codes for items  
            - Item details (name, price, quantity)  
            - Merchant information  
            - Payment details  
            - Shipping information (if applicable)  
            - Tax breakdown  
              
            Return structured JSON data following the retail receipt schema.  
            """,
            tools=[
                self.parse_retail_receipt,
                self.extract_sku_information,
                self.validate_retail_data
            ],
            generate_content_config=genai_types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for consistent parsing
                safety_settings=[
                    genai_types.SafetySetting(
                        category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
            ),
        )

    async def parse_retail_receipt(self, image_data: bytes, mime_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse retail receipt and extract structured data."""

        image_part = genai_types.Part.from_bytes(
            data=image_data, mime_type=mime_type
        )

        prompt_text = """  
        Parse this retail receipt and extract the following information in JSON format:  
        {  
            "invoiceNumber": "invoice or order number",  
            "merchantName": "store/website name",  
            "merchantAddress": "store address if visible",  
            "date": "purchase date in YYYY-MM-DD format",  
            "time": "purchase time if visible",  
            "items": [  
                {  
                    "sku": "product SKU/code if visible",  
                    "name": "item name",  
                    "quantity": "quantity purchased",  
                    "unitPrice": "price per unit",  
                    "totalPrice": "total price for this item",  
                    "category": "product category if identifiable"  
                }  
            ],  
            "subtotal": "subtotal amount",  
            "tax": "tax amount",  
            "shipping": "shipping cost if applicable",  
            "discount": "discount amount if applicable",  
            "grandTotal": "final total amount",  
            "paymentMethod": "payment method used",  
            "currency": "currency code (e.g., INR, USD)"  
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
                system_instruction="You are a retail receipt parsing specialist. Extract accurate structured data from retail receipts."
            ),
        )

        try:
            result_text = response.candidates[0].content.parts[0].text.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            parsed_data = json.loads(result_text)

            # Structure according to the system schema
            return {
                "billType": "Retail",
                "uploadDate": datetime.now().isoformat(),
                "uploaderId": metadata.get("user_id", "unknown"),
                "imageUrl": metadata.get("image_url", ""),
                "parsedData": parsed_data
            }

        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse retail receipt: {e}")
            return {
                "billType": "Retail",
                "uploadDate": datetime.now().isoformat(),
                "uploaderId": metadata.get("user_id", "unknown"),
                "imageUrl": metadata.get("image_url", ""),
                "parsedData": {},
                "error": f"Parsing failed: {str(e)}"
            }

    async def extract_sku_information(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and enrich SKU information for retail items."""
        enriched_items = []

        for item in items:
            enriched_item = item.copy()

            # Add additional SKU-based information if available
            if "sku" in item and item["sku"]:
                # This could integrate with product databases for enrichment
                enriched_item["skuValidated"] = True
            else:
                enriched_item["skuValidated"] = False

            enriched_items.append(enriched_item)

        return enriched_items

    async def validate_retail_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean retail receipt data."""
        validation_results = {
            "isValid": True,
            "warnings": [],
            "errors": []
        }

        # Validate required fields
        required_fields = ["merchantName", "grandTotal", "items"]
        for field in required_fields:
            if field not in parsed_data or not parsed_data[field]:
                validation_results["errors"].append(
                    f"Missing required field: {field}")
                validation_results["isValid"] = False

        # Validate numeric fields
        numeric_fields = ["subtotal", "tax", "grandTotal"]
        for field in numeric_fields:
            if field in parsed_data and parsed_data[field] is not None:
                try:
                    float(parsed_data[field])
                except (ValueError, TypeError):
                    validation_results["warnings"].append(
                        f"Invalid numeric value for {field}")

        return validation_results


# Create the retail parser agent instance
retail_parser_agent = RetailParserAgent()
