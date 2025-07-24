"""Input Handler Agent for Receipt Processing System."""

import base64
import logging
import random
from typing import Dict, List, Optional, Union

from google.adk.agents import Agent, RemoteA2aAgent
from google.adk.tools import FunctionTool
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Receipt classification constants
RECEIPT_TYPES = [
    "retail_shopping",
    "food_dining",
    "travel_transport",
    "utilities",
    "subscriptions",
    "medical_pharmacy",
    "education",
    "miscellaneous"
]

# Input mode processing tools


def process_camera_input(image_data: str, user_context: Optional[str] = None) -> Dict:
    """Process receipt from camera input.  

    Args:  
        image_data: Base64 encoded image data  
        user_context: Optional user-provided context hint  

    Returns:  
        Dict containing processed image metadata and classification hint  
    """
    # Decode and validate image
    try:
        image_bytes = base64.b64decode(image_data)
        image_size = len(image_bytes)

        return {
            "input_mode": "camera",
            "image_size": image_size,
            "user_context": user_context,
            "status": "processed",
            "classification_hint": _extract_classification_hint(image_bytes, user_context)
        }
    except Exception as e:
        logger.error(f"Camera input processing failed: {e}")
        return {"status": "error", "message": str(e)}


def process_screenshot_overlay(screenshot_data: str, user_context: Optional[str] = None) -> Dict:
    """Process receipt from screenshot overlay.  

    Args:  
        screenshot_data: Base64 encoded screenshot data  
        user_context: Optional user-provided context hint  

    Returns:  
        Dict containing processed screenshot metadata and classification hint  
    """
    try:
        screenshot_bytes = base64.b64decode(screenshot_data)
        screenshot_size = len(screenshot_bytes)

        return {
            "input_mode": "screenshot",
            "image_size": screenshot_size,
            "user_context": user_context,
            "status": "processed",
            "classification_hint": _extract_classification_hint(screenshot_bytes, user_context)
        }
    except Exception as e:
        logger.error(f"Screenshot processing failed: {e}")
        return {"status": "error", "message": str(e)}


def process_email_automation(email_data: Dict, user_context: Optional[str] = None) -> Dict:
    """Process receipt from email automation.  

    Args:  
        email_data: Email metadata and attachment data  
        user_context: Optional user-provided context hint  

    Returns:  
        Dict containing processed email metadata and classification hint  
    """
    try:
        sender = email_data.get("sender", "")
        subject = email_data.get("subject", "")
        attachments = email_data.get("attachments", [])

        # Extract classification hints from email metadata
        classification_hint = _classify_from_email_metadata(
            sender, subject, user_context)

        return {
            "input_mode": "email",
            "sender": sender,
            "subject": subject,
            "attachment_count": len(attachments),
            "user_context": user_context,
            "status": "processed",
            "classification_hint": classification_hint
        }
    except Exception as e:
        logger.error(f"Email processing failed: {e}")
        return {"status": "error", "message": str(e)}


def classify_receipt_type(
    input_data: Dict,
    classification_hint: Optional[str] = None
) -> str:
    """Classify receipt into one of the 8 predefined types.  

    Args:  
        input_data: Processed input data from any input mode  
        classification_hint: Optional hint from preprocessing  

    Returns:  
        Classified receipt type  
    """
    # Use ML-based classification logic here
    # For demo purposes, using rule-based classification

    user_context = input_data.get("user_context", "").lower()
    hint = classification_hint or ""

    # Combine context and hint for comprehensive analysis
    combined_text = f"{user_context} {hint}".lower()

    # Indian Food & Dining keywords
    food_dining_keywords = [
        # Popular Indian food delivery apps
        "zomato", "swiggy", "dominos", "pizzahut", "kfc", "mcdonalds", "burgerking",
        "foodpanda", "ubereats", "dunzo",
        # Restaurant types
        "restaurant", "hotel", "dhaba", "cafe", "canteen", "mess", "tiffin",
        "food court", "food stall", "street food", "chaat", "dosa", "idli",
        # Food categories
        "biryani", "thali", "curry", "roti", "naan", "paratha", "samosa",
        "vada pav", "pani puri", "bhel puri", "masala", "tandoor",
        # Dining context
        "dining", "breakfast", "lunch", "dinner", "snacks", "beverage",
        "food", "meal", "eat", "hungry", "order"
    ]

    # Indian Retail & Shopping keywords
    retail_keywords = [
        # Major Indian e-commerce
        "amazon", "flipkart", "myntra", "ajio", "meesho", "snapdeal",
        "paytm mall", "shopclues", "nykaa", "bigbasket", "grofers", "blinkit",
        "zepto", "dunzo", "swiggy instamart",
        # Physical retail
        "reliance digital", "croma", "vijay sales", "more", "dmart", "big bazaar",
        "spencer's", "lifestyle", "pantaloons", "westside", "max fashion",
        # Shopping categories
        "shopping", "purchase", "buy", "order", "delivery", "courier",
        "electronics", "mobile", "laptop", "clothing", "fashion", "grocery",
        "home", "kitchen", "appliance", "book", "toy", "gift"
    ]

    # Indian Travel & Transport keywords
    travel_keywords = [
        # Transportation apps
        "uber", "ola", "rapido", "bounce", "vogo", "yulu", "metro",
        "auto", "rickshaw", "taxi", "cab", "bus", "train", "flight",
        # Travel booking
        "makemytrip", "cleartrip", "goibibo", "yatra", "easemytrip", "ixigo",
        "redbus", "abhibus", "paytm travel", "irctc", "railyatri",
        # Airlines
        "indigo", "spicejet", "air india", "vistara", "go air", "alliance air",
        # Travel context
        "travel", "trip", "journey", "booking", "ticket", "reservation",
        "hotel", "accommodation", "stay", "check-in", "airport", "station"
    ]

    # Indian Utilities keywords
    utilities_keywords = [
        # Electricity boards
        "mseb", "kseb", "tneb", "pseb", "gseb", "uppcl", "bseb", "electricity board",
        "power", "current", "bijli", "vidyut", "urja",
        # Telecom operators
        "jio", "airtel", "vi", "vodafone idea", "bsnl", "mtnl",
        "mobile", "phone", "internet", "broadband", "wifi", "data",
        # Gas & Water
        "indane", "bharat gas", "hp gas", "lpg", "cylinder", "gas",
        "water", "municipal", "corporation", "panchayat",
        # Other utilities
        "electricity", "utility", "bill", "recharge", "top-up", "prepaid", "postpaid",
        "dth", "cable", "tv", "tata sky", "dish tv", "sun direct", "d2h"
    ]

    # Indian Subscription services keywords
    subscription_keywords = [
        # OTT Platforms
        "netflix", "amazon prime", "disney hotstar", "zee5", "sonyliv", "voot",
        "mx player", "alt balaji", "eros now", "jio cinema", "jio saavn",
        # Music streaming
        "spotify", "gaana", "wynk", "hungama", "apple music", "youtube music",
        # Other subscriptions
        "subscription", "monthly", "annual", "premium", "pro", "plus",
        "membership", "plan", "package", "service", "renewal", "auto-pay"
    ]

    # Indian Medical & Pharmacy keywords
    medical_keywords = [
        # Pharmacy chains
        "apollo pharmacy", "medplus", "netmeds", "1mg", "pharmeasy", "practo",
        "tata 1mg", "myra", "wellness forever", "guardian", "cipla",
        # Medical context
        "medicine", "tablet", "syrup", "injection", "prescription", "doctor",
        "hospital", "clinic", "dispensary", "medical", "pharmacy", "chemist",
        "health", "treatment", "consultation", "checkup", "test", "lab",
        "pathology", "diagnostic", "x-ray", "scan", "blood test", "urine test"
    ]

    # Indian Education keywords
    education_keywords = [
        # Educational platforms
        "byju's", "unacademy", "vedantu", "toppr", "khan academy", "coursera",
        "udemy", "skillshare", "linkedin learning", "upgrad", "simplilearn",
        # Educational institutions
        "school", "college", "university", "institute", "academy", "coaching",
        "tuition", "classes", "course", "training", "workshop", "seminar",
        # Educational context
        "education", "study", "learn", "exam", "test", "admission", "fee",
        "book", "notebook", "stationery", "uniform", "bag", "supplies"
    ]

    # Classification logic with Indian context
    if any(keyword in combined_text for keyword in food_dining_keywords):
        return "food_dining"
    elif any(keyword in combined_text for keyword in retail_keywords):
        return "retail"
    elif any(keyword in combined_text for keyword in travel_keywords):
        return "travel"
    elif any(keyword in combined_text for keyword in utilities_keywords):
        return "utilities"
    elif any(keyword in combined_text for keyword in subscription_keywords):
        return "subscriptions"
    elif any(keyword in combined_text for keyword in medical_keywords):
        return "medical"
    elif any(keyword in combined_text for keyword in education_keywords):
        return "education"
    else:
        return "miscellaneous"


def route_to_parser_agent(receipt_type: str, receipt_data: Dict) -> str:
    """Route classified receipt to appropriate parser agent.  

    Args:  
        receipt_type: Classified receipt type  
        receipt_data: Complete receipt data for processing  

    Returns:  
        Parser agent endpoint URL  
    """
    parser_endpoints = {
        "retail_shopping": "http://localhost:8001/a2a/retail_parser_agent",
        "food_dining": "http://localhost:8002/a2a/food_dining_parser_agent",
        "travel_transport": "http://localhost:8003/a2a/travel_parser_agent",
        "utilities": "http://localhost:8004/a2a/utilities_parser_agent",
        "subscriptions": "http://localhost:8005/a2a/subscriptions_parser_agent",
        "medical_pharmacy": "http://localhost:8006/a2a/medical_parser_agent",
        "education": "http://localhost:8007/a2a/education_parser_agent",
        "miscellaneous": "http://localhost:8008/a2a/miscellaneous_parser_agent"
    }

    endpoint = parser_endpoints.get(
        receipt_type, parser_endpoints["miscellaneous"])
    logger.info(f"Routing {receipt_type} receipt to {endpoint}")
    return endpoint

# Helper functions


def _extract_classification_hint(image_bytes: bytes, user_context: Optional[str]) -> str:
    """Extract classification hints from image data."""
    # Placeholder for ML-based image analysis
    # In production, this would use OCR and image recognition
    return user_context or "unknown"


def _classify_from_email_metadata(sender: str, subject: str, user_context: Optional[str]) -> str:
    """Extract classification hints from email metadata."""
    sender_lower = sender.lower()
    subject_lower = subject.lower()

    if any(domain in sender_lower for domain in ["amazon", "flipkart", "myntra"]):
        return "retail_shopping"
    elif any(domain in sender_lower for domain in ["zomato", "swiggy"]):
        return "food_dining"
    elif any(domain in sender_lower for domain in ["uber", "airlines"]):
        return "travel_transport"
    elif any(keyword in subject_lower for keyword in ["bill", "invoice", "electricity", "internet"]):
        return "utilities"
    elif any(domain in sender_lower for domain in ["netflix", "spotify"]):
        return "subscriptions"

    return user_context or "unknown"


# Create function tools following ADK pattern
camera_input_tool = FunctionTool(process_camera_input)
screenshot_tool = FunctionTool(process_screenshot_overlay)
email_tool = FunctionTool(process_email_automation)
classify_tool = FunctionTool(classify_receipt_type)
routing_tool = FunctionTool(route_to_parser_agent)

# Define remote parser agents using RemoteA2aAgent pattern
retail_parser_agent = RemoteA2aAgent(
    name="retail_parser_agent",
    description="Agent that handles retail/shopping receipt parsing.",
    agent_card="http://localhost:8001/a2a/retail_parser_agent/.well-known/agent_card"
)

food_dining_parser_agent = RemoteA2aAgent(
    name="food_dining_parser_agent",
    description="Agent that handles food & dining receipt parsing.",
    agent_card="http://localhost:8002/a2a/food_dining_parser_agent/.well-known/agent_card"
)

travel_parser_agent = RemoteA2aAgent(
    name="travel_parser_agent",
    description="Agent that handles travel/transport receipt parsing.",
    agent_card="http://localhost:8003/a2a/travel_parser_agent/.well-known/agent_card"
)

utilities_parser_agent = RemoteA2aAgent(
    name="utilities_parser_agent",
    description="Agent that handles utilities receipt parsing.",
    agent_card="http://localhost:8004/a2a/utilities_parser_agent/.well-known/agent_card"
)

subscriptions_parser_agent = RemoteA2aAgent(
    name="subscriptions_parser_agent",
    description="Agent that handles subscription receipt parsing.",
    agent_card="http://localhost:8005/a2a/subscriptions_parser_agent/.well-known/agent_card"
)

medical_parser_agent = RemoteA2aAgent(
    name="medical_parser_agent",
    description="Agent that handles medical/pharmacy receipt parsing.",
    agent_card="http://localhost:8006/a2a/medical_parser_agent/.well-known/agent_card"
)

education_parser_agent = RemoteA2aAgent(
    name="education_parser_agent",
    description="Agent that handles education receipt parsing.",
    agent_card="http://localhost:8007/a2a/education_parser_agent/.well-known/agent_card"
)

miscellaneous_parser_agent = RemoteA2aAgent(
    name="miscellaneous_parser_agent",
    description="Agent that handles miscellaneous receipt parsing.",
    agent_card="http://localhost:8008/a2a/miscellaneous_parser_agent/.well-known/agent_card"
)

# Main Input Handler Agent following ADK delegation pattern
input_handler_agent = Agent(
    model="gemini-2.0-flash",
    name="input_handler_agent",
    description="Handles receipt input processing, classification, and routing to specialized parser agents.",
    instruction="""  
    You are the Input Handler Agent for a receipt processing system. Your responsibilities:  
      
    1. INPUT PROCESSING: Accept receipts via three input modes:  
       - Camera input (mobile scan): Use process_camera_input tool  
       - Screenshot overlay (desktop): Use process_screenshot_overlay tool    
       - Email automation: Use process_email_automation tool  
      
    2. RECEIPT CLASSIFICATION: Classify receipts into 8 types:  
       - retail_shopping (Amazon, Flipkart, Myntra)  
       - food_dining (Restaurants, Zomato, Swiggy)  
       - travel_transport (Uber, Airlines)  
       - utilities (Electricity, Internet)  
       - subscriptions (Netflix, Spotify)  
       - medical_pharmacy (Prescriptions, Medical)  
       - education (School, University fees)  
       - miscellaneous (Catch-all)  
      
    3. CONTEXT INTEGRATION: Use optional user context hints to improve classification accuracy.  
      
    4. A2A ROUTING: Route classified receipts to appropriate parser agents:  
       - For retail_shopping: delegate to retail_parser_agent  
       - For food_dining: delegate to food_dining_parser_agent  
       - For travel_transport: delegate to travel_parser_agent  
       - For utilities: delegate to utilities_parser_agent  
       - For subscriptions: delegate to subscriptions_parser_agent  
       - For medical_pharmacy: delegate to medical_parser_agent  
       - For education: delegate to education_parser_agent  
       - For miscellaneous: delegate to miscellaneous_parser_agent  
      
    Always process input first, classify the receipt type, then route to the appropriate parser agent.  
    Include user context and classification confidence in your routing decisions.  
    """,
    tools=[
        camera_input_tool,
        screenshot_tool,
        email_tool,
        classify_tool,
        routing_tool
    ],
    sub_agents=[
        retail_parser_agent,
        food_dining_parser_agent,
        travel_parser_agent,
        utilities_parser_agent,
        subscriptions_parser_agent,
        medical_parser_agent,
        education_parser_agent,
        miscellaneous_parser_agent
    ],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)

# Export the root agent for ADK discovery
root_agent = input_handler_agent
