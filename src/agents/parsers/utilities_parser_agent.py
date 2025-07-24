"""Utilities Parser Agent for Receipt Processing System."""

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


class UtilitiesReceiptData(BaseModel):
  """Structured data model for utilities receipts."""
  utility_provider: str
  utility_type: str  # electricity, internet, gas, water
  customer_id: str
  account_number: Optional[str] = None
  billing_period: str
  due_date: Optional[str] = None
  meter_reading: Optional[Dict[str, Union[str, float]]] = None
  usage_details: Optional[Dict[str, Union[str, float]]] = None
  charges_breakdown: List[Dict[str, Union[str, float]]]
  total_amount: float
  previous_balance: Optional[float] = None
  payment_status: Optional[str] = None


def extract_utility_provider(receipt_text: str) -> str:
  """Extract utility provider name."""
  # Common utility provider patterns
  patterns = [
      r"(?i)(BESCOM|KSEB|MSEB|PSEB|TNEB|WBSEDCL)",  # Electricity boards
      r"(?i)(Airtel|Jio|BSNL|Vodafone|ACT|Hathway)",  # Internet providers
      r"(?i)([A-Z][A-Za-z\s]+(?:Electric|Power|Broadband|Internet|Gas|Water))",
      r"^([A-Z][A-Za-z\s&]+)(?:\n|Limited|Ltd)"
  ]

  for pattern in patterns:
    match = re.search(pattern, receipt_text)
    if match:
      return match.group(1).strip()

  return "Unknown Provider"


def determine_utility_type(receipt_text: str, provider: str) -> str:
  """Determine the type of utility service."""
  text_lower = receipt_text.lower()
  provider_lower = provider.lower()

  if any(keyword in text_lower for keyword in ["electricity", "electric", "power", "kwh", "units"]):
    return "electricity"
  elif any(keyword in text_lower for keyword in ["internet", "broadband", "wifi", "data", "mbps"]):
    return "internet"
  elif any(keyword in text_lower for keyword in ["gas", "lpg", "pipeline"]):
    return "gas"
  elif any(keyword in text_lower for keyword in ["water", "municipal", "corporation"]):
    return "water"
  elif any(keyword in provider_lower for keyword in ["electric", "power", "seb"]):
    return "electricity"
  elif any(keyword in provider_lower for keyword in ["airtel", "jio", "bsnl", "broadband"]):
    return "internet"
  else:
    return "utilities"


def extract_customer_details(receipt_text: str) -> Dict[str, str]:
  """Extract customer ID and account number."""
  details = {}

  # Customer ID patterns
  customer_patterns = [
      r"(?i)customer[- ]?(?:id|number)[:\s]*([A-Z0-9\-]+)",
      r"(?i)consumer[- ]?(?:id|number)[:\s]*([A-Z0-9\-]+)",
      r"(?i)account[- ]?(?:id|number)[:\s]*([A-Z0-9\-]+)",
      r"(?i)service[- ]?(?:id|number)[:\s]*([A-Z0-9\-]+)"
  ]

  for pattern in customer_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      details["customer_id"] = match.group(1)
      break

  # Account number patterns
  account_patterns = [
      r"(?i)account[- ]?no[:\s]*([A-Z0-9\-]+)",
      r"(?i)a/c[- ]?no[:\s]*([A-Z0-9\-]+)",
      r"(?i)meter[- ]?no[:\s]*([A-Z0-9\-]+)"
  ]

  for pattern in account_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      details["account_number"] = match.group(1)
      break

  return details


def extract_billing_period(receipt_text: str) -> str:
  """Extract billing period from receipt."""
  period_patterns = [
      r"(?i)billing[- ]?period[:\s]*([A-Za-z0-9\s\-/]+)",
      r"(?i)bill[- ]?period[:\s]*([A-Za-z0-9\s\-/]+)",
      r"(?i)from[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})[- ]?to[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
  ]

  for pattern in period_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      if len(match.groups()) == 2:  # From-to pattern
        return f"{match.group(1)} to {match.group(2)}"
      else:
        return match.group(1).strip()

  return "Unknown Period"


def extract_meter_reading(receipt_text: str) -> Optional[Dict[str, Union[str, float]]]:
  """Extract meter reading details."""
  reading_data = {}

  # Current reading
  current_match = re.search(
      r"(?i)current[- ]?reading[:\s]*(\d+(?:\.\d+)?)", receipt_text)
  if current_match:
    reading_data["current"] = float(current_match.group(1))

  # Previous reading
  previous_match = re.search(
      r"(?i)previous[- ]?reading[:\s]*(\d+(?:\.\d+)?)", receipt_text)
  if previous_match:
    reading_data["previous"] = float(previous_match.group(1))

  # Units consumed
  units_match = re.search(
      r"(?i)units[- ]?consumed[:\s]*(\d+(?:\.\d+)?)", receipt_text)
  if units_match:
    reading_data["units_consumed"] = float(units_match.group(1))

  return reading_data if reading_data else None


def extract_usage_details(receipt_text: str, utility_type: str) -> Optional[Dict[str, Union[str, float]]]:
  """Extract usage details specific to utility type."""
  usage_data = {}

  if utility_type == "electricity":
    # Extract kWh usage
    kwh_match = re.search(r"(?i)(\d+(?:\.\d+)?)\s*kwh", receipt_text)
    if kwh_match:
      usage_data["kwh_consumed"] = float(kwh_match.group(1))

    # Extract rate per unit
    rate_match = re.search(
        r"(?i)rate[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d+)?)", receipt_text)
    if rate_match:
      usage_data["rate_per_unit"] = float(rate_match.group(1))

  elif utility_type == "internet":
    # Extract data usage
    data_patterns = [
        r"(?i)(\d+(?:\.\d+)?)\s*gb",
        r"(?i)data[- ]?usage[:\s]*(\d+(?:\.\d+)?)",
        r"(?i)(\d+(?:\.\d+)?)\s*mbps"
    ]

    for pattern in data_patterns:
      match = re.search(pattern, receipt_text)
      if match:
        usage_data["data_usage"] = float(match.group(1))
        break

  return usage_data if usage_data else None


def extract_charges_breakdown(receipt_text: str) -> List[Dict[str, Union[str, float]]]:
  """Extract detailed charges breakdown."""
  charges = []

  # Common charge patterns
  charge_patterns = [
      (r"(?i)energy[- ]?charge[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "Energy Charge"),
      (r"(?i)fixed[- ]?charge[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "Fixed Charge"),
      (r"(?i)fuel[- ]?surcharge[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "Fuel Surcharge"),
      (r"(?i)electricity[- ]?duty[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "Electricity Duty"),
      (r"(?i)rental[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "Rental"),
      (r"(?i)installation[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "Installation"),
      (r"(?i)maintenance[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "Maintenance"),
      (r"(?i)tax[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "Tax"),
      (r"(?i)gst[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", "GST")
  ]

  for pattern, charge_name in charge_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      charges.append({
          "charge_type": charge_name,
          "amount": float(match.group(1))
      })

  return charges


def extract_total_amount(receipt_text: str) -> float:
  """Extract total amount from receipt."""
  total_patterns = [
      r"(?i)total[- ]?amount[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)amount[- ]?payable[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)",
      r"(?i)net[- ]?amount[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)"
  ]

  for pattern in total_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      return float(match.group(1))

  return 0.0


def extract_due_date(receipt_text: str) -> Optional[str]:
  """Extract due date from receipt."""
  due_patterns = [
      r"(?i)due[- ]?date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
      r"(?i)pay[- ]?by[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
      r"(?i)last[- ]?date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
  ]

  for pattern in due_patterns:
    match = re.search(pattern, receipt_text)
    if match:
      return match.group(1)

  return None


def parse_utilities_receipt(receipt_text: str, image_url: str, user_id: str) -> Dict:
  """Parse utilities receipt and return structured data."""
  try:
    # Extract all components
    provider = extract_utility_provider(receipt_text)
    utility_type = determine_utility_type(receipt_text, provider)
    customer_details = extract_customer_details(receipt_text)
    billing_period = extract_billing_period(receipt_text)
    meter_reading = extract_meter_reading(receipt_text)
    usage_details = extract_usage_details(receipt_text, utility_type)
    charges_breakdown = extract_charges_breakdown(receipt_text)
    total_amount = extract_total_amount(receipt_text)
    due_date = extract_due_date(receipt_text)

    # Extract previous balance
    prev_balance_match = re.search(
        r"(?i)previous[- ]?balance[:\s]*(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d{2})?)", receipt_text)
    previous_balance = float(prev_balance_match.group(
        1)) if prev_balance_match else None

    # Extract payment status
    payment_status = None
    if re.search(r"(?i)(paid|payment[- ]?received)", receipt_text):
      payment_status = "Paid"
    elif re.search(r"(?i)(pending|unpaid|due)", receipt_text):
      payment_status = "Pending"

    parsed_data = UtilitiesReceiptData(
        utility_provider=provider,
        utility_type=utility_type,
        customer_id=customer_details.get("customer_id", "Unknown"),
        account_number=customer_details.get("account_number"),
        billing_period=billing_period,
        due_date=due_date,
        meter_reading=meter_reading,
        usage_details=usage_details,
        charges_breakdown=charges_breakdown,
        total_amount=total_amount,
        previous_balance=previous_balance,
        payment_status=payment_status
    )

    return {
        "bill_type": "Utilities",
        "upload_date": datetime.now().isoformat(),
        "uploader_id": user_id,
        "image_url": image_url,
        "parsed_data": parsed_data.dict(),
        "status": "success"
    }

  except Exception as e:
    logger.error(f"Utilities parsing failed: {e}")
    return {
        "status": "error",
        "message": str(e),
        "bill_type": "Utilities"
    }


# Create function tool
parse_utilities_tool = FunctionTool(parse_utilities_receipt)

# Utilities Parser Agent
utilities_parser_agent = Agent(
    model="gemini-2.0-flash",
    name="utilities_parser_agent",
    description="Specialized agent for parsing utilities receipts including electricity, internet, gas, and water bills.",
    instruction="""  
    You are the Utilities Parser Agent. Your role is to extract structured data from utility bills.  
      
    Key fields to extract:  
    - Utility provider name  
    - Utility type (electricity, internet, gas, water)  
    - Customer ID and account number  
    - Billing period  
    - Due date  
    - Meter readings (current, previous, units consumed)  
    - Usage details specific to utility type  
    - Detailed charges breakdown  
    - Total amount  
    - Previous balance  
    - Payment status  
      
    Always use the parse_utilities_receipt tool to process receipts.  
    Handle variations in bill formats from different utility providers.  
    Ensure accurate extraction of customer identification numbers and billing details.  
    """,
    tools=[parse_utilities_tool],
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
root_agent = utilities_parser_agent
