import json
import jwt
from google.auth.crypt import RSASigner
import datetime

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
            'issuerName': 'Rasheed',  # Replace with your company name
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
            'state': 'ACTIVE',
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
            'barcode': {
                'type': 'QR_CODE',
                'value': 'https://example.com/full_bill_details_link'
            },
            'locations': [
                {
                    'latitude': 37.424015499999996,
                    'longitude': -122.09259560000001
                }
            ],
            'imageModulesData': [
                {
                    'id': 'bill_image',
                    'image': {
                        'sourceUri': {
                            'uri': 'https://example.com/path_to_your_bill_image.jpg',  # <-- Replace with your actual image URL
                            'description': 'Bill Image'
                        }
                    }
                }
            ],
            # ...other fields...
        
            'validTimeInterval': { # Optional: if the bill has a validity period
                'start': {
                    'date': '2023-01-01T00:00:00Z'
                },
                'end': '2023-12-31T23:59:59Z'
            }
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

if __name__ == '__main__':
    SERVICE_ACCOUNT_KEY_FILE = 'rasheedagenticai-168f43733e00.json' # e.g., 'my-google-wallet-api-key.json'
    SERVICE_ACCOUNT_EMAIL = 'walletapi@rasheedagenticai.iam.gserviceaccount.com'
    YOUR_ISSUER_ID = '3388000000022969075' # e.g., '1234567890123456789'

    # Predefined parsed content of a bill (simulating OCR output)
    sample_bill_content = {
        "merchant_name": "Walmart Palace",
            "date": "2025-07-24",
            "total_amount": 346.50,
            "currency": "INR",
            "items": [
                {"name": "Large Pepperoni", "price": 18.00},
                {"name": "Soda", "price": 2.50}
            ],
            "notes": "Birthday dinner"
    }

    # Initialize the Google Wallet Bill Pass creator
    wallet_creator = GoogleWalletBillPass(SERVICE_ACCOUNT_KEY_FILE, SERVICE_ACCOUNT_EMAIL)

    # Generate the Google Wallet pass link
    add_to_wallet_link = wallet_creator.create_jwt_for_bill_pass(YOUR_ISSUER_ID, sample_bill_content)

    print(f"\nShare this link with your user: {add_to_wallet_link}")
    print("When the user clicks this link, they will be prompted to add the bill details to their Google Wallet.")