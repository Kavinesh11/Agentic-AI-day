import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from google.adk.agents.llm_agent import Agent
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools import ToolContext
from google.genai import types as genai_types
from google.genai import Client

logger = logging.getLogger(__name__)


class PassData(BaseModel):
    """Schema for wallet pass data."""
    passType: str
    passId: str
    merchantName: str
    amount: float
    date: str
    description: str
    metadata: Dict[str, Any]


class PassGeneratorAgent:
    def __init__(self):
        self.client = Client(vertexai=False)

        # Create the ADK agent following LlmAgent patterns
        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="pass_generator_agent",
            description="Generates personalized wallet passes from parsed receipt data",
            instruction="""  
            You are a wallet pass generator that creates beautiful, descriptive passes for receipts.  
              
            Your responsibilities:  
            1. Receive parsed receipt data from parser agents  
            2. Generate contextual and insightful pass descriptions  
            3. Create structured pass metadata for wallet integration  
            4. Provide spending insights and categorization  
            5. Generate notifications for significant purchases  
              
            For each receipt, create:  
            - A descriptive pass title and summary  
            - Spending insights and patterns  
            - Category-specific metadata  
            - Contextual recommendations  
            - Beautiful visual descriptions for the pass  
              
            Always focus on providing value to the user through insights and organization.  
            """,
            tools=[
                self.generate_pass_from_receipt,
                self.create_spending_insights,
                self.generate_pass_metadata,
                self.create_notification_content,
                self.save_pass_data
            ],
            generate_content_config=genai_types.GenerateContentConfig(
                temperature=0.3,  # Slightly higher for creative pass descriptions
                safety_settings=[
                    genai_types.SafetySetting(
                        category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
            ),
        )

    async def generate_pass_from_receipt(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a wallet pass from parsed receipt data."""

        bill_type = receipt_data.get("billType", "Unknown")
        parsed_data = receipt_data.get("parsedData", {})

        # Create contextual pass based on receipt type
        if bill_type == "Retail":
            return await self._generate_retail_pass(receipt_data)
        elif bill_type == "Food & Dining":
            return await self._generate_food_pass(receipt_data)
        elif bill_type == "Miscellaneous":
            return await self._generate_misc_pass(receipt_data)
        else:
            return await self._generate_generic_pass(receipt_data)

    async def _generate_retail_pass(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pass for retail receipts."""

        parsed_data = receipt_data.get("parsedData", {})
        merchant_name = parsed_data.get("merchantName", "Store")
        grand_total = parsed_data.get("grandTotal", 0)
        items = parsed_data.get("items", [])

        # Generate descriptive content
        item_count = len(items)
        item_summary = f"{item_count} item{'s' if item_count != 1 else ''}"

        pass_data = {
            "passType": "retail",
            "passId": f"retail_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": f"Shopping at {merchant_name}",
            "description": f"Purchased {item_summary} for ₹{grand_total}",
            "merchantName": merchant_name,
            "amount": grand_total,
            "date": parsed_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "category": "Shopping",
            "items": items,
            "insights": {
                "itemCount": item_count,
                "averageItemPrice": grand_total / max(item_count, 1),
                "category": "retail_shopping"
            }
        }

        return pass_data

    async def _generate_food_pass(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pass for food & dining receipts."""

        parsed_data = receipt_data.get("parsedData", {})
        restaurant_name = parsed_data.get("restaurantName", "Restaurant")
        grand_total = parsed_data.get("grandTotal", 0)
        tip_amount = parsed_data.get("tipAmount", 0)

        # Calculate tip insights
        tip_percentage = 0
        if grand_total > 0 and tip_amount > 0:
            tip_percentage = (tip_amount / (grand_total - tip_amount)) * 100

        pass_data = {
            "passType": "dining",
            "passId": f"dining_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": f"Dining at {restaurant_name}",
            "description": f"Meal for ₹{grand_total}" + (f" (tip: {tip_percentage:.1f}%)" if tip_amount > 0 else ""),
            "merchantName": restaurant_name,
            "amount": grand_total,
            "date": parsed_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "category": "Food & Dining",
            "diningDetails": {
                "tableNumber": parsed_data.get("tableNumber"),
                "numberOfGuests": parsed_data.get("numberOfGuests"),
                "tipAmount": tip_amount,
                "tipPercentage": tip_percentage
            },
            "insights": {
                "tipCategory": "generous" if tip_percentage > 20 else "standard" if tip_percentage > 10 else "minimal",
                "diningType": "delivery" if parsed_data.get("deliveryAddress") else "dine_in"
            }
        }

        return pass_data

    async def _generate_misc_pass(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pass for miscellaneous receipts."""

        parsed_data = receipt_data.get("parsedData", {})
        provider_name = parsed_data.get("providerName", "Service Provider")
        receipt_type = parsed_data.get("receiptType", "service")
        charges = parsed_data.get("charges", {})
        total = charges.get("total", 0)

        pass_data = {
            "passType": "utility",
            "passId": f"misc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": f"{receipt_type.title()} - {provider_name}",
            "description": f"{receipt_type.title()} payment of ₹{total}",
            "merchantName": provider_name,
            "amount": total,
            "date": parsed_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "category": receipt_type.title(),
            "serviceDetails": parsed_data.get("serviceDetails", {}),
            "insights": {
                "serviceType": receipt_type,
                "hasUsageCharges": bool(charges.get("usageCharges")),
                "accountNumber": parsed_data.get("accountNumber")
            }
        }

        return pass_data

    async def create_spending_insights(self, pass_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate spending insights for the pass."""

        amount = pass_data.get("amount", 0)
        category = pass_data.get("category", "Unknown")

        insights = {
            "spendingCategory": category,
            "amount": amount,
            "date": pass_data.get("date"),
            "insights": []
        }

        # Add category-specific insights
        if category == "Food & Dining":
            if amount > 1000:
                insights["insights"].append("High-value dining expense")
            if pass_data.get("diningDetails", {}).get("tipPercentage", 0) > 20:
                insights["insights"].append("Generous tipper!")

        elif category == "Shopping":
            item_count = pass_data.get("insights", {}).get("itemCount", 0)
            if item_count > 5:
                insights["insights"].append("Bulk shopping trip")
            if amount > 2000:
                insights["insights"].append("Major purchase")

        return insights

    async def generate_pass_metadata(self, pass_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for wallet integration."""

        metadata = {
            "passTypeIdentifier": f"pass.receipt.{pass_data.get('passType', 'generic')}",
            "serialNumber": pass_data.get("passId"),
            "organizationName": pass_data.get("merchantName"),
            "description": pass_data.get("description"),
            "logoText": pass_data.get("merchantName"),
            "foregroundColor": "rgb(255, 255, 255)",
            "backgroundColor": self._get_category_color(pass_data.get("category")),
            "labelColor": "rgb(255, 255, 255)",
            "generic": {
                "primaryFields": [
                    {
                        "key": "amount",
                        "label": "Amount",
                        "value": f"₹{pass_data.get('amount', 0)}"
                    }
                ],
                "secondaryFields": [
                    {
                        "key": "date",
                        "label": "Date",
                        "value": pass_data.get("date")
                    },
                    {
                        "key": "category",
                        "label": "Category",
                        "value": pass_data.get("category")
                    }
                ]
            }
        }

        return metadata

    def _get_category_color(self, category: str) -> str:
        """Get color scheme based on category."""
        color_map = {
            "Food & Dining": "rgb(255, 149, 0)",  # Orange
            "Shopping": "rgb(52, 199, 89)",       # Green
            "Transportation": "rgb(0, 122, 255)",  # Blue
            "Healthcare": "rgb(255, 59, 48)",     # Red
            "Entertainment": "rgb(175, 82, 222)",  # Purple
            "Utilities": "rgb(255, 204, 0)"       # Yellow
        }
        return color_map.get(category, "rgb(142, 142, 147)")  # Default gray

    async def create_notification_content(self, pass_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create notification content for significant purchases."""

        amount = pass_data.get("amount", 0)
        category = pass_data.get("category", "")
        merchant = pass_data.get("merchantName", "")

        notification = {
            "shouldNotify": False,
            "title": "",
            "body": "",
            "priority": "normal"
        }

        # Determine if notification is needed
        if amount > 1000:  # High-value purchases
            notification["shouldNotify"] = True
            notification["title"] = f"Large {category} Purchase"
            notification["body"] = f"₹{amount} spent at {merchant}"
            notification["priority"] = "high"

        elif category == "Food & Dining" and amount > 500:
            notification["shouldNotify"] = True
            notification["title"] = "Dining Expense"
            notification["body"] = f"₹{amount} meal at {merchant}"

        return notification

    async def save_pass_data(
        self,
        tool_context: ToolContext,
        pass_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save pass data and metadata as artifacts."""

        try:
            pass_id = pass_data.get("passId", "unknown")

            # Save pass data
            pass_json = json.dumps(pass_data, indent=2)
            pass_artifact = genai_types.Part(
                inline_data=genai_types.Blob(
                    mime_type='application/json',
                    data=pass_json.encode('utf-8')
                )
            )

            await tool_context.save_artifact(f'wallet_pass_{pass_id}', pass_artifact)

            # Save metadata
            metadata_json = json.dumps(metadata, indent=2)
            metadata_artifact = genai_types.Part(
                inline_data=genai_types.Blob(
                    mime_type='application/json',
                    data=metadata_json.encode('utf-8')
                )
            )

            await tool_context.save_artifact(f'pass_metadata_{pass_id}', metadata_artifact)

            return {
                "status": "saved",
                "passId": pass_id,
                "passData": pass_data,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Failed to save pass data: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Create the pass generator agent instance
pass_generator_agent = PassGeneratorAgent()

# Export the ADK agent for use in the system
root_agent = pass_generator_agent.agent
