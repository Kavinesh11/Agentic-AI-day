"""Food & Dining Parser Agent for Receipt Processing System."""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FoodDiningReceiptData(BaseModel):
  """Structured data model for food & dining receipts."""
  restaurant_name: str
  date: str
  time: str
  table_number: Optional[int] = None
  number_of_guests: Optional[int] = None
  order_id: Optional[str] = None
  items: List[Dict[str, Union[str, float]]]
  subtotal: float
  service_charge: Optional[float] = None
  gst: Optional[float] = None
  grand_total: float
  tip_amount: Optional[float] = None
  payment_method: Optional[str] = None


def extract_restaurant_name(receipt_text: str) -> str:
  """Extract restaurant name from receipt text."""
  # Common patterns for restaurant names
  patterns = [
      r"(?i)restaurant[:\s]+([^\n]+)",
      r"(?i)([A-Z][a-z\s&]+(?:restaurant|cafe|bistro|diner))",
      r"^([A-Z][A-Za-z\s&]+)(?:\n|$)"
  ]

  for pattern in patterns:
    match = re.search(pattern, receipt_text)
    if match:
      return match.group(1).strip()

  return "Unknown Restaurant"


def extract_order_details(receipt_text: str) -> Dict:
  """Extract order ID, table number, and guest count."""
  details = {}

  # Order ID patterns
  order_patterns = [
      r"(?i)order[#\s]*:?\s*([A-Z0-9\-]+)",
      r"(?i)bill[#\s]*:?\s*([A-Z0-9\-]+)",
      r"(?i)receipt[#\s]*:?\s*([A-Z0-9\-]+)"
  ]

  for pattern in order_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      details["order_id"] = match.group(1)
      break

  # Table number
  table_match = re.search(r"(?i)table[#\s]*:?\s*(\d+)", receipt_text)
  if table_match:
    details["table_number"] = int(table_match.group(1))

  # Number of guests
  guest_match = re.search(
      r"(?i)(?:guests?|pax|covers?)[#\s]*:?\s*(\d+)", receipt_text)
  if guest_match:
    details["number_of_guests"] = int(guest_match.group(1))

  return details


def extract_menu_items(receipt_text: str) -> List[Dict[str, Union[str, float]]]:
  """Extract menu items and prices."""
  items = []

  # Pattern for item lines: "Item Name ... Price"
  item_patterns = [
      r"([A-Za-z][A-Za-z\s&,'-]+?)\s+(?:\.{2,}|\s{2,})\s*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)",
      r"(\d+)\s+([A-Za-z][A-Za-z\s&,'-]+?)\s+(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)"
  ]

  lines = receipt_text.split('\n')
  for line in lines:
    for pattern in item_patterns:
      match = re.search(pattern, line)
      if match:
        if len(match.groups()) == 2:
          name, price = match.groups()
          items.append({
              "name": name.strip(),
              "price": float(price)
          })
        elif len(match.groups()) == 3:
          qty, name, price = match.groups()
          items.append({
              "name": f"{qty}x {name.strip()}",
              "price": float(price)
          })

  return items


def extract_financial_totals(receipt_text: str) -> Dict[str, float]:
  """Extract subtotal, charges, taxes, and total."""
  totals = {}

  # Subtotal patterns
  subtotal_match = re.search(
      r"(?i)sub[- ]?total[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", receipt_text)
  if subtotal_match:
    totals["subtotal"] = float(subtotal_match.group(1))

  # Service charge
  service_match = re.search(
      r"(?i)service[- ]?charge[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", receipt_text)
  if service_match:
    totals["service_charge"] = float(service_match.group(1))

  # GST/Tax
  tax_patterns = [
      r"(?i)gst[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)tax[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)cgst[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)sgst[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)"
  ]

  total_tax = 0
  for pattern in tax_patterns:
    matches = re.findall(pattern, receipt_text)
    for match in matches:
      total_tax += float(match)

  if total_tax > 0:
    totals["gst"] = total_tax

  # Grand total
  total_patterns = [
      r"(?i)(?:grand[- ]?)?total[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)amount[- ]?payable[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)"
  ]

  for pattern in total_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      totals["grand_total"] = float(match.group(1))
      break

  # Tip amount
  tip_match = re.search(
      r"(?i)tip[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", receipt_text)
  if tip_match:
    totals["tip_amount"] = float(tip_match.group(1))

  return totals


def extract_payment_method(receipt_text: str) -> Optional[str]:
  """Extract payment method."""
  payment_patterns = [
      r"(?i)payment[- ]?method[:\s]*([A-Za-z\s]+)",
      r"(?i)paid[- ]?by[:\s]*([A-Za-z\s]+)",
      r"(?i)(cash|card|upi|credit|debit|wallet)"
  ]

  for pattern in payment_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      return match.group(1).strip().title()

  return None


def parse_food_dining_receipt(receipt_text: str, image_url: str, user_id: str) -> Dict:
  """Parse food & dining receipt and return structured data."""
  try:
    # Extract all components
    restaurant_name = extract_restaurant_name(receipt_text)
    order_details = extract_order_details(receipt_text)
    items = extract_menu_items(receipt_text)
    totals = extract_financial_totals(receipt_text)
    payment_method = extract_payment_method(receipt_text)

    # Extract date and time
    current_time = datetime.now()
    date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", receipt_text)
    time_match = re.search(
        r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)", receipt_text)

    parsed_data = FoodDiningReceiptData(
        restaurant_name=restaurant_name,
        date=date_match.group(
            1) if date_match else current_time.strftime("%d-%m-%Y"),
        time=time_match.group(
            1) if time_match else current_time.strftime("%H:%M"),
        table_number=order_details.get("table_number"),
        number_of_guests=order_details.get("number_of_guests"),
        order_id=order_details.get("order_id"),
        items=items,
        subtotal=totals.get("subtotal", 0.0),
        service_charge=totals.get("service_charge"),
        gst=totals.get("gst"),
        grand_total=totals.get("grand_total", 0.0),
        tip_amount=totals.get("tip_amount"),
        payment_method=payment_method
    )

    return {
        "bill_type": "Food & Dining",
        "upload_date": current_time.isoformat(),
        "uploader_id": user_id,
        "image_url": image_url,
        "parsed_data": parsed_data.dict(),
        "status": "success"
    }

  except Exception as e:
    logger.error(f"Food dining parsing failed: {e}")
    return {
        "status": "error",
        "message": str(e),
        "bill_type": "Food & Dining"
    }


# Create function tool
parse_food_dining_tool = FunctionTool(parse_food_dining_receipt)

# Food & Dining Parser Agent
food_dining_parser_agent = Agent(
    model="gemini-2.0-flash",
    name="food_dining_parser_agent",
    description="Specialized agent for parsing food & dining receipts from restaurants, Zomato, and Swiggy.",
    instruction="""  
    You are the Food & Dining Parser Agent. Your role is to extract structured data from restaurant receipts.  
      
    Key fields to extract:  
    - Restaurant name  
    - Date and time  
    - Table number (if available)  
    - Number of guests (if available)  
    - Order ID  
    - Menu items with prices  
    - Subtotal, service charge, GST/taxes  
    - Grand total  
    - Tip amount (if any)  
    - Payment method  
      
    Always use the parse_food_dining_receipt tool to process receipts.  
    Ensure all monetary values are accurately extracted and validated.  
    Handle variations in receipt formats from different restaurants and food delivery platforms.  
    """,
    tools=[parse_food_dining_tool],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,  # Low temperature for deterministic parsing
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)

# Export for A2A discovery
root_agent = food_dining_parser_agent
