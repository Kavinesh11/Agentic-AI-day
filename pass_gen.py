import json
import jwt
from google.auth.crypt import RSASigner
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

class GoogleWalletBillPass:
    def __init__(self, key_file_path: str, service_account_email: str):
        """
        Initializes the GoogleWalletBillPass class with service account credentials.

        Args:
            key_file_path (str): Path to your service account JSON key file.
            service_account_email (str): Service account email from the key file.
        """
        self.key_file_path = key_file_path
        self.credentials = self._load_credentials(key_file_path, service_account_email)

    def _load_credentials(self, key_file_path: str, service_account_email: str):
        """
        Loads service account credentials. In a real application, you'd use
        google.oauth2.service_account.Credentials.from_service_account_file.
        For this example, we're mocking it to extract necessary parts.
        """
        try:
            with open(key_file_path, 'r') as f:
                key_data = json.load(f)
            return {
                "client_email": key_data.get("client_email", service_account_email),
                "private_key": key_data.get("private_key")
            }
        except FileNotFoundError:
            print(f"Error: Key file not found at {key_file_path}. Please check the path.")
            exit()
        except KeyError:
            print("Error: 'private_key' or 'client_email' not found in the key file. "
                  "Ensure it's a valid Google service account JSON key.")
            exit()


    def create_jwt_for_bill_pass(self, issuer_id: str, bill_data: dict) -> str:
        """
        Generates a signed JWT that creates a new generic pass class and object
        for a bill/receipt in Google Wallet.

        When the user opens the "Add to Google Wallet" URL and saves the pass to
        their wallet, the pass class and object defined in the JWT are created.

        Args:
            issuer_id (str): Your Google Wallet issuer ID.
            bill_data (dict): A dictionary containing the parsed bill content.

        Returns:
            str: An "Add to Google Wallet" link.
        """

        # Generate unique suffixes for the class and object based on current time or a unique bill ID
        class_suffix = f"bill_class_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        object_suffix = f"bill_object_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Construct the class and object IDs
        class_id = f'{issuer_id}.{class_suffix}'
        object_id = f'{issuer_id}.{object_suffix}'

        # Define the Generic Class for the bill pass (template)
        # This defines the overall look and feel, shared across all your bill passes
        new_class = {
            'id': class_id,
            'issuerName': 'Your Company Name',  # Replace with your company name
            'reviewStatus': 'UNDER_REVIEW',  # Or 'APPROVED' if your class is already approved
            'hexBackgroundColor': '#F0F0F0',  # Light grey background
            'logo': {
                'sourceUri': {
                    'uri': 'https://example.com/your_company_logo.png' # Replace with your company logo URL
                },
                'contentDescription': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': 'Company Logo'
                    }
                }
            }
        }

        # Define the Generic Object for the specific bill (instance)
        # This will contain the extracted details from the bill/receipt
        # We will use textModulesData to display the bill content
        text_modules = []
        for key, value in bill_data.items():
            if key == "items" and isinstance(value, list):
                # Special formatting for items list
                items_body = "\n".join([f"{item.get('name', '')}: {item.get('price', '')}" for item in value])
                text_modules.append({'header': 'Items', 'body': items_body, 'id': 'bill_items'})
            else:
                # Add all other fields generically
                header = key.replace("_", " ").title()
                text_modules.append({'header': header, 'body': str(value), 'id': key})

        # Fallback if nothing was added
        if not text_modules:
            text_modules.append({'header': 'Bill Details', 'body': 'No specific details extracted.', 'id': 'generic_details'})

        new_object = {
            'id': object_id,
            'classId': class_id,
            'state': 'ACTIVE',  # Or 'EXPIRED', 'INACTIVE'
            'cardTitle': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': f'Receipt from {bill_data.get("merchant_name", "Unknown Merchant")}'
                }
            },
            'header': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': f'{bill_data.get("total_amount", "N/A")} {bill_data.get("currency", "")}'
                }
            },
            'textModulesData': text_modules,
            'barcode': { # Example: QR code with a link to the original image or more details
                'type': 'QR_CODE',
                'value': 'https://example.com/full_bill_details_link' # Replace with actual link
            },
            'locations': [ # Optional: if you have location data from the bill
                {
                    'latitude': 37.424015499999996,
                    'longitude': -122.09259560000001
                }
            ],
            # 'validTimeInterval': { # Optional: if the bill has a validity period
            #     'start': {
            #         'date': '2023-01-01T00:00:00Z'
            #     },
            #     'end': '2023-12-31T23:59:59Z'
            # }
        }

        # Create the JWT claims
        claims = {
            'iss': self.credentials['client_email'],
            'aud': 'google',
            'origins': ['www.example.com'],  # Replace with your website's origin
            'typ': 'savetowallet',
            'payload': {
                'genericClasses': [new_class],
                'genericObjects': [new_object]
            }
        }

        # The service account credentials are used to sign the JWT
        # For a real application, ensure self.key_file_path points to your service account key file
        signer = RSASigner.from_service_account_file(self.key_file_path)
        token = jwt.encode(claims, self.credentials['private_key'], algorithm='RS256')

        wallet_link = f'https://pay.google.com/gp/v/save/{token}'
        print('Add to Google Wallet link:')
        print(wallet_link)

        return wallet_link

# --- Example Usage ---
if __name__ == '__main__':
    # REPLACE WITH YOUR ACTUAL CREDENTIALS AND ISSUER ID
    # You will get these from your Google Cloud Project and Google Pay & Wallet Console
    SERVICE_ACCOUNT_KEY_FILE = 'cred.json' # e.g., 'my-google-wallet-api-key.json'
    SERVICE_ACCOUNT_EMAIL = 'walletapi@raseed-466617.iam.gserviceaccount.com'
    YOUR_ISSUER_ID = '3388000000022958613' # e.g., '1234567890123456789'

    cred = credentials.Certificate("agentic-ai-day-c4dda-firebase-adminsdk-fbsvc-0ea01b341e.json")
    firebase_admin.initialize_app(cred)
    print("Done with the creds, now creating the db")
    db = firestore.client() 
    print(f"Firestore client initialized. Project ID: {db.project}")

    # Fetch the top document from the "bills" collection (ordered by timestamp or any field you prefer)
    bill_docs = db.collection("bills")
    docs = bill_docs.order_by("uploadDate", direction=firestore.Query.DESCENDING).limit(1).stream()
    for doc in docs:
        sample_bill_content = doc.to_dict()
        break

    if not sample_bill_content:
        print("No bill found in the 'bills' collection.")
        exit()
    
    sample_bill_content = sample_bill_content.get('parsedData', {})
    print(f"Fetched bill content: {sample_bill_content}")
    # # Predefined parsed content of a bill (simulating OCR output)
    # sample_bill_content = {
    #     "merchant_name": "Cafe Delicious",
    #     "total_amount": "25.75",
    #     "currency": "INR",
    #     "date": "2024-07-26",
    #     "invoice_number": "INV-2024-00123",
    #     "tax_amount": "2.25",
    #     "items": [
    #         {"name": "Coffee", "price": "4.50"},
    #         {"name": "Sandwich", "price": "12.00"},
    #         {"name": "Dessert", "price": "7.00"}
    #     ],
    #     "daily": "monday"
    # }

    # Initialize the Google Wallet Bill Pass creator
    wallet_creator = GoogleWalletBillPass(SERVICE_ACCOUNT_KEY_FILE, SERVICE_ACCOUNT_EMAIL)

    # Generate the Google Wallet pass link
    add_to_wallet_link = wallet_creator.create_jwt_for_bill_pass(YOUR_ISSUER_ID, sample_bill_content)

    print(f"\nShare this link with your user: {add_to_wallet_link}")
    print("When the user clicks this link, they will be prompted to add the bill details to their Google Wallet.")
