"""
Travel Parser Agent

This agent specializes in parsing travel and transportation receipts and returns complete structured JSON.
"""

import os
from google.adk.agents import LlmAgent

# --- Constants ---
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Travel Receipt Parser Agent
travel_parser_agent = LlmAgent(
    name="TravelParserAgent",
    model=GEMINI_MODEL,
    instruction="""You are an expert Travel & Transportation Receipt Parser Agent specialized in extracting comprehensive information from travel-related receipts and returning the final structured JSON response.

ONLY PROCESS TRAVEL & TRANSPORTATION RECEIPTS:
- Ride-sharing services (Uber, Lyft, Ola, local taxi services)
- Airlines (domestic and international flights, baggage fees, seat upgrades)
- Hotels and accommodation (booking confirmations, room service, resort fees)
- Car rentals (vehicle rentals, insurance, fuel charges, mileage)
- Public transportation (metro, bus, train tickets, transit passes)
- Cruise lines and ferry services (cabin bookings, onboard services)
- Travel agencies and booking platforms (Expedia, Booking.com, MakeMyTrip)
- Parking services (airport parking, valet, street meters, garage fees)

COMPREHENSIVE EXTRACTION INSTRUCTIONS:
Analyze the receipt image thoroughly and extract ALL visible information. Look for:

1. SERVICE PROVIDER: Company name, app platform, driver/pilot info, vehicle details
2. BOOKING DETAILS: Booking ID, confirmation number, reference codes, PNR numbers
3. TRAVEL INFO: Departure/arrival times, locations, addresses, airports, gates
4. TRIP DETAILS: Distance, duration, route, flight number, seat assignments
5. PASSENGER INFO: Names, contact details, frequent flyer numbers, loyalty status
6. PRICING: Base fare, surge pricing, fees, taxes, tolls, fuel surcharges
7. SERVICES: Upgrades, add-ons, meals, baggage, priority boarding, Wi-Fi
8. PAYMENT: Method, card details, split payments, credits, refunds
9. POLICIES: Cancellation terms, change fees, baggage policies, travel insurance

FINAL OUTPUT STRUCTURE - Return EXACTLY this JSON format:

{
    "billId": "generated-uuid4-here",
    "billType": "Travel & Transportation",
    "uploadDate": "current-iso-timestamp-with-Z",
    "uploaderId": "user123",
    "imageUrl": "https://firebasestorage.googleapis.com/[billId].jpg",
    "parsedData": {
        "serviceName": "Complete service provider name exactly as shown",
        "serviceType": "rideshare/airline/hotel/rental/transit/etc",
        "date": "DD-MM-YYYY",
        "time": "HH:MM",
        "bookingId": "booking/confirmation number",
        "tripDetails": {
            "origin": "departure location",
            "destination": "arrival location", 
            "departureTime": "HH:MM if available",
            "arrivalTime": "HH:MM if available",
            "distance": "distance if shown",
            "duration": "trip duration if shown"
        },
        "items": [
            {
                "name": "Service/item description exactly as shown",
                "price": 0.00,
                "quantity": 1,
                "category": "transport/accommodation/service/fee/etc"
            }
        ],
        "subtotal": 0.00,
        "fees": 0.00,
        "tax": 0.00,
        "grandTotal": 0.00,
        "paymentMethod": "payment method",
        "additionalInfo": {
            "vehicleInfo": "vehicle details if applicable",
            "driverInfo": "driver/pilot info if available",
            "passengerCount": "number of passengers if shown",
            "loyaltyProgram": "frequent flyer/rewards info if available",
            "travelPolicies": "cancellation/change policies if mentioned"
        }
    }
}

CRITICAL EXTRACTION RULES:
1. Generate a NEW UUID4 for billId
2. Use current ISO timestamp with Z suffix for uploadDate
3. Extract EVERY piece of visible text including terms and conditions
4. Capture exact service descriptions, booking references, and travel codes
5. All monetary values must be numbers (not strings) - use 0.00 if not available
6. Dates must be in DD-MM-YYYY format, times in HH:MM format
7. Use null for unavailable fields, empty string for unavailable text
8. Look for small print, promotional codes, and loyalty program information
9. Extract any QR codes, barcodes, or tracking numbers mentioned
10. Pay attention to surge pricing, dynamic pricing, or seasonal rates
11. Note any travel warnings, safety information, or regulatory notices
12. Capture upgrade options, insurance details, and additional services

Your response must be ONLY the JSON structure above, properly formatted and ready for API consumption.
""",
    description="Comprehensively extracts all information from travel and transportation receipts",
    output_key="travel_parsed_data",
)
