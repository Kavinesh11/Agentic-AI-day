import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from pydantic import BaseModel

from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools import ToolContext
from google.genai import types as genai_types
from google.genai import Client

logger = logging.getLogger(__name__)


class MiscReceiptData(BaseModel):
    """Schema for miscellaneous receipt parsed data."""
    billType: str = "Miscellaneous"
    uploadDate: str
    uploaderId: str
    imageUrl: str
    parsedData: Dict[str, Any]


class MiscParserAgent:
    def __init__(self):
        self.client = Client(vertexai=False)

        # Create the ADK agent following LlmAgent patterns
        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="misc_parser_agent",
            description="Specialized parser for miscellaneous receipts including utilities, transportation, healthcare, and services",
            instruction="""  
            You are a miscellaneous receipt parser specialized in extracting structured data from:  
            - Utility bills (electricity, gas, water, internet, phone)  
            - Transportation receipts (gas, parking, public transit, rideshare)  
            - Healthcare receipts (medical, dental, pharmacy, insurance)  
            - Entertainment receipts (movies, concerts, streaming services)  
            - Service receipts (repairs, maintenance, professional services)  
            - Government fees and taxes  
            - Insurance payments  
            - Educational expenses  
              
            Your role is to:  
            1. Identify the specific type of miscellaneous receipt  
            2. Extract relevant information based on receipt type  
            3. Structure data according to the miscellaneous receipt schema  
            4. Validate extracted information for accuracy  
              
            Always focus on accuracy and only extract clearly visible information.  
            """,
            tools=[
                self.parse_misc_receipt,
                self.categorize_misc_type,
                self.extract_service_details,
                self.validate_misc_data,
                self.save_parsed_receipt
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

    async def parse_misc_receipt(self, image_data: bytes, mime_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse miscellaneous receipt and extract structured data."""

        # Create image part from receipt data
        image_part = genai_types.Part.from_bytes(
            data=image_data, mime_type=mime_type
        )

        prompt_text = """  
        Parse this miscellaneous receipt and extract the following information in JSON format:  
        {  
            "receiptType": "specific type (utility, transportation, healthcare, entertainment, service, government, insurance, education)",  
            "providerName": "service provider or company name",  
            "providerAddress": "provider address if visible",  
            "date": "service/transaction date in YYYY-MM-DD format",  
            "dueDate": "due date if applicable in YYYY-MM-DD format",  
            "accountNumber": "account or reference number if applicable",  
            "invoiceNumber": "invoice or bill number if visible",  
            "serviceDetails": {  
                "description": "description of service or product",  
                "servicePeriod": "service period if applicable (e.g., 'Jan 2025 - Feb 2025')",  
                "quantity": "quantity or usage amount",  
                "unit": "unit of measurement if applicable (kWh, gallons, minutes, etc.)",  
                "serviceAddress": "service address if different from billing address"  
            },  
            "charges": {  
                "baseAmount": "base service charge",  
                "usageCharges": "usage-based charges",  
                "additionalFees": "additional fees or charges",  
                "tax": "tax amount",  
                "lateFees": "late fees if applicable",  
                "previousBalance": "previous balance if applicable",  
                "payments": "payments made if shown",  
                "adjustments": "adjustments if any",  
                "total": "total amount due"  
            },  
            "paymentMethod": "payment method used if shown",  
            "paymentDueDate": "payment due date if different from service date",  
            "currency": "currency code (e.g., INR, USD)",  
            "customerInfo": {  
                "name": "customer name if visible",  
                "address": "billing address if visible",  
                "phone": "phone number if visible"  
            }  
        }  
          
        Focus on accuracy and only extract clearly visible information. If information is not visible, use null.  
        """

        contents = genai_types.Content(
            role="user",
            parts=[image_part, genai_types.Part.from_text(text=prompt_text)],
        )

        response = await self.client.models.generate_content_async(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction="You are a miscellaneous receipt parsing specialist. Extract accurate structured data from various types of service and utility receipts. Return valid JSON only."
            ),
        )

        try:
            result_text = response.candidates[0].content.parts[0].text.strip()
            # Clean up the response to extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            parsed_data = json.loads(result_text)

            # Structure according to the system schema
            return {
                "billType": "Miscellaneous",
                "uploadDate": datetime.now().isoformat(),
                "uploaderId": metadata.get("user_id", "unknown"),
                "imageUrl": metadata.get("image_url", ""),
                "parsedData": parsed_data
            }

        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse miscellaneous receipt: {e}")
            return {
                "billType": "Miscellaneous",
                "uploadDate": datetime.now().isoformat(),
                "uploaderId": metadata.get("user_id", "unknown"),
                "imageUrl": metadata.get("image_url", ""),
                "parsedData": {},
                "error": f"Parsing failed: {str(e)}"
            }

    async def categorize_misc_type(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize the miscellaneous receipt into specific subtypes."""

        receipt_type = parsed_data.get("receiptType", "unknown")
        provider_name = parsed_data.get("providerName", "").lower()

        # Enhanced categorization logic
        category_mapping = {
            "utility": {
                "subcategories": ["electricity", "gas", "water", "internet", "phone", "cable"],
                "keywords": ["electric", "power", "gas", "water", "internet", "telecom", "cable", "broadband"]
            },
            "transportation": {
                "subcategories": ["fuel", "parking", "transit", "rideshare", "tolls"],
                "keywords": ["gas", "fuel", "parking", "metro", "bus", "uber", "lyft", "toll"]
            },
            "healthcare": {
                "subcategories": ["medical", "dental", "pharmacy", "insurance"],
                "keywords": ["hospital", "clinic", "pharmacy", "dental", "medical", "health"]
            },
            "entertainment": {
                "subcategories": ["streaming", "movies", "concerts", "sports"],
                "keywords": ["netflix", "spotify", "cinema", "theater", "concert", "sports"]
            },
            "service": {
                "subcategories": ["repair", "maintenance", "professional", "cleaning"],
                "keywords": ["repair", "service", "maintenance", "cleaning", "professional"]
            }
        }

        detected_category = "other"
        confidence = 0.5

        for category, details in category_mapping.items():
            if receipt_type == category:
                detected_category = category
                confidence = 0.9
                break

            # Check provider name against keywords
            for keyword in details["keywords"]:
                if keyword in provider_name:
                    detected_category = category
                    confidence = 0.7
                    break

        return {
            "detectedCategory": detected_category,
            "confidence": confidence,
            "availableSubcategories": category_mapping.get(detected_category, {}).get("subcategories", [])
        }

    async def extract_service_details(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and enrich service-specific details."""

        service_details = parsed_data.get("serviceDetails", {})
        receipt_type = parsed_data.get("receiptType", "")

        enriched_details = service_details.copy()

        # Add type-specific enrichments
        if receipt_type == "utility":
            # Calculate usage if possible
            if "quantity" in service_details and "unit" in service_details:
                enriched_details["usageCalculated"] = True
                enriched_details["usageDisplay"] = f"{service_details['quantity']} {service_details['unit']}"

        elif receipt_type == "transportation":
            # Add distance/time calculations if available
            if "quantity" in service_details:
                enriched_details["distanceOrTime"] = service_details["quantity"]

        elif receipt_type == "healthcare":
            # Add medical coding if available
            enriched_details["medicalService"] = True

        return enriched_details

    async def validate_misc_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean miscellaneous receipt data."""

        validation_results = {
            "isValid": True,
            "warnings": [],
            "errors": [],
            "completeness": 0.0
        }

        # Check required fields
        required_fields = ["providerName", "date"]
        optional_important_fields = ["total", "receiptType", "accountNumber"]

        present_fields = 0
        total_fields = len(required_fields) + len(optional_important_fields)

        for field in required_fields:
            if field not in parsed_data or not parsed_data[field]:
                validation_results["errors"].append(
                    f"Missing required field: {field}")
                validation_results["isValid"] = False
            else:
                present_fields += 1

        for field in optional_important_fields:
            if field in parsed_data and parsed_data[field]:
                present_fields += 1

        validation_results["completeness"] = present_fields / total_fields

        # Validate date formats
        date_fields = ["date", "dueDate", "paymentDueDate"]
        for field in date_fields:
            if field in parsed_data and parsed_data[field]:
                try:
                    datetime.fromisoformat(parsed_data[field])
                except ValueError:
                    validation_results["warnings"].append(
                        f"Invalid date format for {field}")

        # Validate numeric fields
        charges = parsed_data.get("charges", {})
        numeric_fields = ["baseAmount", "usageCharges", "tax", "total"]
        for field in numeric_fields:
            if field in charges and charges[field] is not None:
                try:
                    float(charges[field])
                except (ValueError, TypeError):
                    validation_results["warnings"].append(
                        f"Invalid numeric value for charges.{field}")

        return validation_results

    async def save_parsed_receipt(
        self,
        tool_context: ToolContext,
        parsed_receipt: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """Save parsed receipt data as artifact."""

        try:
            # Save parsed data as JSON artifact
            receipt_json = json.dumps(parsed_receipt, indent=2)
            receipt_artifact = genai_types.Part(
                inline_data=genai_types.Blob(
                    mime_type='application/json',
                    data=receipt_json.encode('utf-8')
                )
            )

            await tool_context.save_artifact(f'parsed_misc_receipt_{filename}', receipt_artifact)

            return {
                "status": "saved",
                "filename": f'parsed_misc_receipt_{filename}',
                "data": parsed_receipt
            }

        except Exception as e:
            logger.error(f"Failed to save parsed receipt: {e}")
            return {
                "status": "error",
                "filename": filename,
                "error": str(e)
            }

    async def get_supported_types(self) -> Dict[str, str]:
        """Get supported miscellaneous receipt types with descriptions."""
        return {
            "utility": "Electricity, gas, water, internet, phone bills",
            "transportation": "Gas, parking, public transit, rideshare receipts",
            "healthcare": "Medical, dental, pharmacy, insurance receipts",
            "entertainment": "Movies, concerts, streaming services",
            "service": "Repairs, maintenance, professional services",
            "government": "Government fees, taxes, permits",
            "insurance": "Insurance premium payments",
            "education": "Educational expenses, tuition, books"
        }


# Create the misc parser agent instance
misc_parser_agent = MiscParserAgent()

# Export the ADK agent for use in the system
root_agent = misc_parser_agent.agent
