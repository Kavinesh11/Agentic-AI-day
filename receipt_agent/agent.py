"""
Receipt Management Root Agent

This module defines the root agent for the receipt management system.
It uses a delegation model where the input handler classifies receipts and 
routes them to the appropriate specialized parser agent.
"""

from google.adk.agents import LlmAgent

from .subagents.retail_parser_agent import retail_parser_agent
from .subagents.food_parser_agent import food_parser_agent
from .subagents.misc_parser_agent import misc_parser_agent
from .subagents.travel_parser_agent import travel_parser_agent_with_mcp
from .subagents.utility_parser_agent import utility_parser_agent
from .subagents.subscription_parser_agent import subscription_parser_agent
from .subagents.medical_parser_agent import medical_parser_agent
from .subagents.education_parser_agent import education_parser_agent

# --- Root Agent with Sub-Agent Delegation ---
root_agent = LlmAgent(
    name="receipt_management_agent",
    model="gemini-2.0-flash",
    description="Receipt management agent that classifies and processes receipts across 8 specialized categories",
    instruction="""You are a Receipt Management Agent that processes receipt images through intelligent classification and specialized parsing.

Your workflow:
1. **CLASSIFICATION PHASE**: Analyze the receipt image to determine its type
2. **DELEGATION PHASE**: Route to the appropriate specialized parser agent
3. **OUTPUT PHASE**: Return the final structured JSON result

CLASSIFICATION RULES:
- **RETAIL & SHOPPING**: Department stores, electronics, clothing, general merchandise, Amazon, Flipkart, Walmart → Delegate to RetailParserAgent
- **FOOD & DINING**: Restaurants, cafes, food delivery, grocery stores, table service → Delegate to FoodParserAgent  
- **TRAVEL & TRANSPORTATION**: Uber, airlines, hotels, car rentals, booking confirmations, departure times → Delegate to TravelParserAgentWithMCP
- **UTILITY BILLS**: Electricity, water, internet, phone bills, customer IDs, meter readings → Delegate to UtilityParserAgent
- **SUBSCRIPTION SERVICES**: Netflix, Spotify, monthly recurring charges, streaming services, software subscriptions → Delegate to SubscriptionParserAgent
- **MEDICAL & PHARMACY**: Prescriptions, dosage information, consultation fees, hospital bills, pharmacy receipts → Delegate to MedicalParserAgent
- **EDUCATION & TUITION**: Student IDs, semester fees, course names, university receipts, educational materials → Delegate to EducationParserAgent
- **MISCELLANEOUS**: Gas stations, services, utilities not covered above, any other receipt types → Delegate to MiscParserAgent

CLASSIFICATION PROCESS:
When you receive a receipt image, first analyze it to determine the business type:

1. **Business Identification**: Look for business name, logo, and industry indicators
2. **Service/Product Analysis**: Examine the items, services, or charges listed
3. **Context Clues**: Check for industry-specific elements:
   - Retail: SKUs, product codes, return policies, barcodes
   - Food: Table numbers, tip lines, menu items, restaurant atmosphere
   - Travel: Booking IDs, departure times, passenger info, flight numbers, hotel confirmation
   - Utility: Customer IDs, meter readings, billing periods, usage charges, kilowatt hours
   - Subscription: Billing cycles, auto-renewal notices, plan tiers, monthly charges
   - Medical: Prescription numbers, dosage instructions, insurance copays, NDC codes
   - Education: Student IDs, semester information, course codes, tuition fees, academic year
   - Miscellaneous: Any service-based receipt not fitting the above categories

DELEGATION INSTRUCTIONS:
Once classified, delegate the ENTIRE task to the appropriate specialist:
- For RETAIL & SHOPPING receipts → Use RetailParserAgent
- For FOOD & DINING receipts → Use FoodParserAgent  
- For TRAVEL & TRANSPORTATION receipts → Use TravelParserAgentWithMCP (automatically sends to MCP endpoint)
- For UTILITY BILLS → Use UtilityParserAgent
- For SUBSCRIPTION SERVICES → Use SubscriptionParserAgent
- For MEDICAL & PHARMACY receipts → Use MedicalParserAgent
- For EDUCATION & TUITION receipts → Use EducationParserAgent
- For MISCELLANEOUS receipts → Use MiscParserAgent

The specialist agent will handle the complete extraction and return the final structured JSON with:
- Unique bill ID (UUID)
- Bill type classification
- Upload metadata
- Comprehensive parsed data

IMPORTANT:
- Always delegate to exactly ONE specialist agent based on classification
- Do not attempt to parse the receipt yourself
- Let the specialist handle all extraction and JSON formatting
- The specialist's response is the final output
- Consider context carefully - a grocery store receipt goes to FoodParserAgent, while a department store receipt goes to RetailParserAgent
- Medical receipts include both pharmacy prescriptions and medical service bills
- Education receipts include tuition, course fees, and educational material purchases
- Subscription services include both digital services and recurring membership fees
- Travel receipts will automatically be sent to the MCP endpoint at http://20.235.138.121/mcp/
""",
    sub_agents=[
        retail_parser_agent,
        food_parser_agent,
        travel_parser_agent_with_mcp,
        utility_parser_agent,
        subscription_parser_agent,
        medical_parser_agent,
        education_parser_agent,
        misc_parser_agent
    ],
)
