"""Miscellaneous Parser Agent for Receipt Processing System."""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MiscellaneousReceiptData(BaseModel):
  """Structured data model for miscellaneous receipts."""
  vendor_name: str
  receipt_type: Optional[str] = None
  date: str
  time: Optional[str] = None
  transaction_id: Optional[str] = None
  items: List[Dict[str, Any]]
  subtotal: Optional[float] = None
  taxes: Optional[float] = None
  total_amount: float
  payment_method: Optional[str] = None
  additional_fields: Dict[str, Any] = {}


def extract_vendor_name(receipt_text: str) -> str:
  """Extract vendor/business name from receipt."""
  # Try to find business name patterns
  patterns = [
      r"^([A-Z][A-Za-z\s&,.-]+)(?:\n|$)",  # First line capitalized
      r"(?i)(?:from|to|vendor|business)[:\s]+([A-Za-z\s&,.-]+)",
      r"([A-Z][A-Za-z\s&,.-]+)(?:\s+(?:Inc|LLC|Ltd|Corp|Co))",
      r"(?i)bill[- ]?to[:\s]*([A-Za-z\s&,.-]+)"
  ]

  lines = receipt_text.split('\n')

  # Check first few lines for business name
  for i, line in enumerate(lines[:5]):
    line = line.strip()
    if len(line) > 3 and not re.match(r'^\d+', line):
      # Skip common header words
      if not any(word in line.lower() for word in ['receipt', 'invoice', 'bill', 'date', 'time']):
        if re.match(r'^[A-Z][A-Za-z\s&,.-]+$', line):
          return line.strip()

  # Try pattern matching
  for pattern in patterns:
    match = re.search(pattern, receipt_text)
    if match:
      return match.group(1).strip()

  return "Unknown Vendor"


def determine_receipt_type(receipt_text: str, vendor_name: str) -> Optional[str]:
  """Determine the type of miscellaneous receipt."""
  text_lower = receipt_text.lower()
  vendor_lower = vendor_name.lower()

  # Common receipt type indicators
  if any(keyword in text_lower for keyword in ["service", "repair", "maintenance"]):
    return "Service"
  elif any(keyword in text_lower for keyword in ["donation", "charity", "contribution"]):
    return "Donation"
  elif any(keyword in text_lower for keyword in ["parking", "toll", "fine"]):
    return "Transportation"
  elif any(keyword in text_lower for keyword in ["office", "supplies", "stationery"]):
    return "Office Supplies"
  elif any(keyword in text_lower for keyword in ["hardware", "tools", "equipment"]):
    return "Hardware"
  elif any(keyword in text_lower for keyword in ["gift", "present", "card"]):
    return "Gift"
  elif any(keyword in text_lower for keyword in ["membership", "club", "association"]):
    return "Membership"
  else:
    return "General"


def extract_transaction_id(receipt_text: str) -> Optional[str]:
  """Extract transaction or reference ID."""
  id_patterns = [
      r"(?i)transaction[- ]?(?:id|number)[:\s]*([A-Z0-9\-]+)",
      r"(?i)reference[- ]?(?:id|number)[:\s]*([A-Z0-9\-]+)",
      r"(?i)receipt[- ]?(?:id|number)[:\s]*([A-Z0-9\-]+)",
      r"(?i)confirmation[- ]?(?:id|number)[:\s]*([A-Z0-9\-]+)",
      r"(?i)ref[:\s]*([A-Z0-9\-]+)"
  ]

  for pattern in id_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      return match.group(1)

  return None


def extract_items_generic(receipt_text: str) -> List[Dict[str, Any]]:
  """Extract items from miscellaneous receipts using generic patterns."""
  items = []
  lines = receipt_text.split('\n')

  # Look for item patterns
  item_patterns = [
      r"([A-Za-z][A-Za-z\s&,'-]+?)\s+(?:\.{2,}|\s{2,})\s*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)",
      r"(\d+)\s+([A-Za-z][A-Za-z\s&,'-]+?)\s+(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)",
      r"([A-Za-z][A-Za-z\s&,'-]+?)\s*(?:₹|Rs\.?|INR|\$)\s*(\d+(?:\.\d{2})?)"
  ]

  for line in lines:
    line = line.strip()
    if len(line) < 5:  # Skip very short lines
      continue

    for pattern in item_patterns:
      match = re.search(pattern, line)
      if match:
        if len(match.groups()) == 2:
          name, price = match.groups()
          items.append({
              "name": name.strip(),
              "price": float(price),
              "quantity": 1
          })
        elif len(match.groups()) == 3:
          qty, name, price = match.groups()
          items.append({
              "name": name.strip(),
              "price": float(price),
              "quantity": int(qty) if qty.isdigit() else 1
          })
        break

  return items


def extract_financial_details(receipt_text: str) -> Dict[str, Optional[float]]:
  """Extract financial details from miscellaneous receipts."""
  details = {}

  # Subtotal patterns
  subtotal_match = re.search(
      r"(?i)sub[- ]?total[:\s]*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)", receipt_text)
  if subtotal_match:
    details["subtotal"] = float(subtotal_match.group(1))

  # Tax patterns
  tax_patterns = [
      r"(?i)tax[:\s]*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)gst[:\s]*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)vat[:\s]*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)"
  ]

  total_tax = 0
  for pattern in tax_patterns:
    matches = re.findall(pattern, receipt_text)
    for match in matches:
      total_tax += float(match)

  if total_tax > 0:
    details["taxes"] = total_tax

  # Total amount patterns
  total_patterns = [
      r"(?i)(?:grand[- ]?)?total[:\s]*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)amount[- ]?(?:due|payable)[:\s]*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)final[- ]?amount[:\s]*(?:₹|Rs\.?|INR|\$)?\s*(\d+(?:\.\d{2})?)"
  ]

  for pattern in total_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      details["total_amount"] = float(match.group(1))
      break

  return details


def extract_payment_method_generic(receipt_text: str) -> Optional[str]:
  """Extract payment method from miscellaneous receipts."""
  payment_patterns = [
      r"(?i)payment[- ]?method[:\s]*([A-Za-z\s]+)",
      r"(?i)paid[- ]?(?:by|via)[:\s]*([A-Za-z\s]+)",
      r"(?i)(cash|card|credit|debit|upi|wallet|cheque|check|online)"
  ]

  for pattern in payment_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      return match.group(1).strip().title()

  return None


def extract_additional_fields(receipt_text: str) -> Dict[str, Any]:
  """Extract any additional fields that might be relevant."""
  additional = {}

  # Contact information
  phone_match = re.search(
      r"(?i)(?:phone|tel|mobile)[:\s]*([0-9\-\+\s]+)", receipt_text)
  if phone_match:
    additional["phone"] = phone_match.group(1).strip()

  email_match = re.search(
      r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", receipt_text)
  if email_match:
    additional["email"] = email_match.group(1)

  # Address
  address_patterns = [
      r"(?i)address[:\s]*([A-Za-z0-9\s,.-]+)",
      r"(?i)location[:\s]*([A-Za-z0-9\s,.-]+)"
  ]

  for pattern in address_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      additional["address"] = match.group(1).strip()
      break

  # Website
  website_match = re.search(
      r"(?i)(?:www\.|https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", receipt_text)
  if website_match:
    additional["website"] = website_match.group(1)

  return additional


def parse_miscellaneous_receipt(receipt_text: str, image_url: str, user_id: str) -> Dict:
  """Parse miscellaneous receipt and return structured data."""
  try:
    # Extract all components
    vendor_name = extract_vendor_name(receipt_text)
    receipt_type = determine_receipt_type(receipt_text, vendor_name)
    transaction_id = extract_transaction_id(receipt_text)
    items = extract_items_generic(receipt_text)
    financial_details = extract_financial_details(receipt_text)
    payment_method = extract_payment_method_generic(receipt_text)
    additional_fields = extract_additional_fields(receipt_text)

    # Extract date and time
    current_time = datetime.now()
    date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", receipt_text)
    time_match = re.search(
        r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)", receipt_text)

    parsed_data = MiscellaneousReceiptData(
        vendor_name=vendor_name,
        receipt_type=receipt_type,
        date=date_match.group(
            1) if date_match else current_time.strftime("%d-%m-%Y"),
        time=time_match.group(
            1) if time_match else current_time.strftime("%H:%M"),
        transaction_id=transaction_id,
        items=items,
        subtotal=financial_details.get("subtotal"),
        taxes=financial_details.get("taxes"),
        total_amount=financial_details.get("total_amount", 0.0),
        payment_method=payment_method,
        additional_fields=additional_fields
    )

    return {
        "bill_type": "Miscellaneous",
        "upload_date": current_time.isoformat(),
        "uploader_id": user_id,
        "image_url": image_url,
        "parsed_data": parsed_data.dict(),
        "status": "success"
    }

  except Exception as e:
    logger.error(f"Miscellaneous parsing failed: {e}")
    return {
        "status": "error",
        "message": str(e),
        "bill_type": "Miscellaneous"
    }


# Create function tool
parse_miscellaneous_tool = FunctionTool(parse_miscellaneous_receipt)

# Miscellaneous Parser Agent
miscellaneous_parser_agent = Agent(
    model="gemini-2.0-flash",
    name="miscellaneous_parser_agent",
    description="Catch-all agent for parsing uncategorized receipts and general business transactions.",
    instruction="""  
    You are the Miscellaneous Parser Agent. Your role is to extract structured data from any receipt that doesn't fit into the other specialized categories.  
      
    Key fields to extract:  
    - Vendor/business name  
    - Receipt type (Service, Donation, Transportation, Office Supplies, Hardware, Gift, Membership, General)  
    - Date and time  
    - Transaction/reference ID  
    - Items or services with prices  
    - Subtotal, taxes, and total amount  
    - Payment method  
    - Additional fields (contact info, address, website)  
      
    Always use the parse_miscellaneous_receipt tool to process receipts.  
    Be flexible in parsing as this agent handles diverse receipt formats.  
    Extract as much structured information as possible while maintaining accuracy.  
    """,
    tools=[parse_miscellaneous_tool],
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
root_agent = miscellaneous_parser_agent
