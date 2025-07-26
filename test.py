import asyncio
from fastmcp import Client

async def main():
    # Connect to your running FastMCP server
    client = Client("http://127.0.0.1:8000/mcp/")

    async with client:
        print("Connected to FastMCP server.")
        
        # Example parsed data for a "Food & Dining" bill
        # with open("parsed_data.json", 'r') as pars:
        #     parsed_data = pars.read()
        #     print(parsed_data)
        parsed_data = {
            "restaurantName": "Pizza Palace",
            "date": "2025-07-24",
            "totalAmount": 25.50,
            "currency": "USD",
            "items": [
                {"name": "Large Pepperoni", "price": 18.00},
                {"name": "Soda", "price": 2.50}
            ],
            "notes": "Birthday dinner"
        }

        try:
            result = await client.call_tool(
                "store_parsed_bill",
                {
                    "bill_type": "Food & Dining",
                    "parsed_data": parsed_data,
                    "uploader_id": "user_abc_123",
                    "image_url": "https://example.com/images/food_bill_1.jpg"
                }
            )
            print(f"Tool call successful: {result.data}")
        except Exception as e:
            print(f"Tool call failed: {e}")

asyncio.run(main())