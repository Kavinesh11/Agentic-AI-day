import os
import firebase_admin
from firebase_admin import credentials, firestore
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult

# --- Firebase Admin SDK Initialization ---
try:
    # Attempt to initialize Firebase Admin SDK using GOOGLE_APPLICATION_CREDENTIALS
    # This environment variable should point to the path of your service account key file.
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        raise EnvironmentError(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. "
            "For local development, please set this to the path of your "
            "Firebase service account key JSON file."
        )
    
    cred = credentials.Certificate("rasheedagenticai-firebase-adminsdk-fbsvc-95c5e1c711.json")
    firebase_admin.initialize_app(cred)
    print("Done with the creds, now creating the db")
    db = firestore.client() 
    print(f"Firestore client initialized. Project ID: {db.project}")
    print("Firebase Admin SDK initialized successfully.")

except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    # Depending on your deployment, you might want to exit or handle this more gracefully
    # For this example, we'll let the application continue but Firebase operations will fail.
    db = None
    print("Firebase operations will be unavailable due to initialization error.")


# --- FastMCP Server Setup ---
mcp = FastMCP(name="Firebase-MCP-Server")

@mcp.tool
async def store_parsed_bill(
    bill_type: str,
    parsed_data: dict,
    uploader_id: str,
    image_url: str,
    ctx: Context # Context for logging
) -> ToolResult:
    """
    Stores structured bill data into Firestore.

    This tool receives already-structured bill data from a parsing agent
    and persists it directly to the /bills collection in Firestore.
    The 'parsed_data' dictionary is stored as-is without further schema
    validation or transformation by this server.

    Args:
        bill_type: The detected bill category (e.g., "Food & Dining", "Utilities").
        parsed_data: The already-structured, category-specific bill details.
        uploader_id: The ID of the user who uploaded the bill.
        image_url: The URL where the bill image is stored.

    Returns:
        A ToolResult containing the Firestore document ID (bill_id) and a success message.

    Raises:
        ValueError: If the data cannot be persisted to Firestore.
    """
    if db is None:
        await ctx.error("Firestore client is not initialized. Cannot store bill.")
        raise ValueError("Firestore is not available. Check server logs for details.")

    try:
        bill_data = {
            "billType": bill_type,
            "uploadDate": firestore.SERVER_TIMESTAMP,
            "uploaderId": uploader_id,
            "imageUrl": image_url,
            "parsedData": parsed_data,
        }

        # Add a new document with an auto-generated ID to the 'bills' collection
        doc_ref, write_time = db.collection("bills").add(bill_data)
        bill_id = doc_ref.id
        
        await ctx.info(f"Bill '{bill_id}' of type '{bill_type}' stored successfully for uploader '{uploader_id}'.")
        
        return ToolResult(
            data={"bill_id": bill_id, "message": "Bill report stored successfully."},
            structured_content={"bill_id": bill_id, "message": "Bill report stored successfully."}
        )

    except Exception as e:
        await ctx.error(f"Failed to store bill of type '{bill_type}' for uploader '{uploader_id}': {e}")
        raise ValueError(f"Failed to persist bill data to Firestore: {e}")

@mcp.tool
async def signup_user(
    email: str,
    password: str,
    username: str,
    phone_number: str,
    ctx: Context
) -> ToolResult:
    """
    Creates a new user document in the 'users' collection.

    Args:
        email: User's email address.    
        password: User's password (should be hashed in production).
        username: Chosen username.
        phone_number: User's phone number.

    Returns:
        ToolResult containing the user document ID and a success message.

    Raises:
        ValueError: If the user cannot be created.
    """
    if db is None:
        await ctx.error("Firestore client is not initialized. Cannot create user.")
        raise ValueError("Firestore is not available. Check server logs for details.")

    try:
        user_data = {
            "email": email,
            "password": password,  # In production, hash this!
            "username": username,
            "phone_number": phone_number,
            "signupDate": firestore.SERVER_TIMESTAMP,
        }

        doc_ref = db.collection("users").document()
        doc_ref.set(user_data)
        user_id = doc_ref.id

        await ctx.info(f"User '{user_id}' signed up with email '{email}'.")
        return ToolResult(
            data={"user_id": user_id, "message": "User signed up successfully."},
            structured_content={"user_id": user_id, "message": "User signed up successfully."}
        )
    except Exception as e:
        await ctx.error(f"Failed to sign up user '{email}': {e}")
        raise ValueError(f"Failed to create user: {e}")


if __name__ == "__main__":
    print("Starting FastMCP Bill Persistence Server...")
    # Run the server via HTTP on port 8000
    mcp.run(transport="http", port=8000)