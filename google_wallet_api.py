#!/usr/bin/env python3
"""
Google Wallet API Integration Script
Creates digital passes from barcode/QR code photos
"""

import os
import json
import cv2
import numpy as np
from pyzbar import pyzbar
from PIL import Image
import uuid
from datetime import datetime, timedelta
import jwt  # Add PyJWT for token creation
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# Replace with the path to your downloaded service account key
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Replace with your actual Issuer ID (find it in Wallet Console)
ISSUER_ID = '3388000000022966480'

# Scopes required for Google Wallet API
SCOPES = ['https://www.googleapis.com/auth/wallet_object.issuer']

class GoogleWalletAPI:
    def __init__(self, service_account_file=SERVICE_ACCOUNT_FILE, issuer_id=ISSUER_ID):
        self.service_account_file = service_account_file
        self.issuer_id = issuer_id
        self.authed_session = None
        self.credentials = None
        self.credentials_json = None  # Store raw JSON credentials like Node.js
        
    def authenticate(self):
        """Authenticate with Google Wallet API using service account"""
        try:
            # Load credentials JSON directly (like Node.js implementation)
            with open(self.service_account_file, 'r') as f:
                self.credentials_json = json.load(f)
            
            # Also create service account credentials for API calls
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES)
            
            # Create an authorized session
            self.authed_session = AuthorizedSession(self.credentials)
            
            print("✅ Successfully authenticated with Google Wallet API")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def extract_barcode_data(self, image_path):
        """Extract barcode/QR code data from image"""
        try:
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ Could not read image: {image_path}")
                return None, None
            
            # Convert to RGB (pyzbar works better with RGB)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Try to decode barcodes
            barcodes = pyzbar.decode(image_rgb)
            
            if not barcodes:
                # Try with PIL as fallback
                pil_image = Image.open(image_path)
                barcodes = pyzbar.decode(pil_image)
            
            if barcodes:
                barcode = barcodes[0]  # Use the first barcode found
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                
                print(f"✅ Found {barcode_type}: {barcode_data}")
                return barcode_data, barcode_type
            else:
                print("❌ No barcode or QR code found in the image")
                return None, None
                
        except Exception as e:
            print(f"❌ Error extracting barcode data: {e}")
            return None, None
    
    def create_generic_pass_class(self, class_id, class_name="Digital Pass"):
        """Create a generic pass class"""
        try:
            if not self.authed_session:
                if not self.authenticate():
                    return None
            
            full_class_id = f'{self.issuer_id}.{class_id}'
            
            # Create generic class exactly like Node.js implementation
            generic_class = {
                'id': full_class_id,
                'classTemplateInfo': {
                    'cardTemplateOverride': {
                        'cardRowTemplateInfos': [
                            {
                                'twoItems': {
                                    'startItem': {
                                        'firstValue': {
                                            'fields': [
                                                {
                                                    'fieldPath': 'object.textModulesData["points"]'
                                                }
                                            ]
                                        }
                                    },
                                    'endItem': {
                                        'firstValue': {
                                            'fields': [
                                                {
                                                    'fieldPath': 'object.textModulesData["contacts"]'
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    },
                    'detailsTemplateOverride': {
                        'detailsItemInfos': [
                            {
                                'item': {
                                    'firstValue': {
                                        'fields': [
                                            {
                                                'fieldPath': 'class.imageModulesData["event_banner"]'
                                            }
                                        ]
                                    }
                                }
                            },
                            {
                                'item': {
                                    'firstValue': {
                                        'fields': [
                                            {
                                                'fieldPath': 'class.textModulesData["game_overview"]'
                                            }
                                        ]
                                    }
                                }
                            },
                            {
                                'item': {
                                    'firstValue': {
                                        'fields': [
                                            {
                                                'fieldPath': 'class.linksModuleData.uris["official_site"]'
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                },
                'imageModulesData': [
                    {
                        'mainImage': {
                            'sourceUri': {
                                'uri': 'https://storage.googleapis.com/wallet-lab-tools-codelab-artifacts-public/google-io-2021-card.png'
                            },
                            'contentDescription': {
                                'defaultValue': {
                                    'language': 'en-US',
                                    'value': 'Google I/O 2022 Banner'
                                }
                            }
                        },
                        'id': 'event_banner'
                    }
                ],
                'textModulesData': [
                    {
                        'header': 'Gather points meeting new people at Google I/O',
                        'body': 'Join the game and accumulate points in this badge by meeting other attendees in the event.',
                        'id': 'game_overview'
                    }
                ],
                'linksModuleData': {
                    'uris': [
                        {
                            'uri': 'https://io.google/2022/',
                            'description': 'Official I/O \'22 Site',
                            'id': 'official_site'
                        }
                    ]
                }
            }
            
            url = 'https://walletobjects.googleapis.com/walletobjects/v1/genericClass'
            response = self.authed_session.post(url, json=generic_class)
            
            if response.status_code == 200:
                print(f"✅ Created generic class: {full_class_id}")
                return response.json()
            elif response.status_code == 409:  # Already exists
                print(f"ℹ️  Class {class_id} already exists")
                return {'id': full_class_id}
            else:
                print(f"❌ Error creating generic class: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Error creating generic class: {e}")
            return None
    
    def create_jwt_pass_object(self, class_id, object_id, barcode_data, barcode_type, pass_title="Digital Pass"):
        """Create a generic pass object using JWT method (like Node.js implementation)"""
        try:
            if not self.credentials_json:
                if not self.authenticate():
                    return None
            
            # Convert barcode type to Google Wallet format
            barcode_type_map = {
                'QRCODE': 'QR_CODE',
                'CODE128': 'CODE_128',
                'CODE39': 'CODE_39',
                'EAN13': 'EAN_13',
                'EAN8': 'EAN_8',
                'UPCA': 'UPC_A',
                'UPCE': 'UPC_E',
                'DATAMATRIX': 'DATA_MATRIX',
                'PDF417': 'PDF_417'
            }
            
            wallet_barcode_type = barcode_type_map.get(str(barcode_type), 'QR_CODE')
            full_object_id = f'{self.issuer_id}.{object_id}'
            full_class_id = f'{self.issuer_id}.{class_id}'
            
            # Create the pass object (exactly like Node.js implementation)
            generic_object = {
                'id': full_object_id,
                'classId': full_class_id,
                'genericType': 'GENERIC_TYPE_UNSPECIFIED',
                'hexBackgroundColor': '#4285f4',
                'logo': {
                    'sourceUri': {
                        'uri': 'https://storage.googleapis.com/wallet-lab-tools-codelab-artifacts-public/pass_google_logo.jpg'
                    }
                },
                'cardTitle': {
                    'defaultValue': {
                        'language': 'en',
                        'value': pass_title
                    }
                },
                'subheader': {
                    'defaultValue': {
                        'language': 'en',
                        'value': 'Header'
                    }
                },
                'header': {
                    'defaultValue': {
                        'language': 'en',
                        'value': 'Sai Nivedh'
                    }
                },
                'barcode': {
                    'type': wallet_barcode_type,
                    'value': barcode_data
                },
                'heroImage': {
                    'sourceUri': {
                        'uri': 'https://storage.googleapis.com/wallet-lab-tools-codelab-artifacts-public/google-io-hero-demo-only.jpg'
                    }
                },
                'textModulesData': [
                    {
                        'header': 'POINTS',
                        'body': '1234',
                        'id': 'points'
                    },
                    {
                        'header': 'CONTACTS',
                        'body': '20',
                        'id': 'contacts'
                    }
                ]
            }
            
            # Create JWT claims (exactly like Node.js implementation)
            claims = {
                'iss': self.credentials_json['client_email'],  # Use JSON directly like Node.js
                'aud': 'google',
                'origins': [],
                'typ': 'savetowallet',
                'payload': {
                    'genericObjects': [generic_object]
                }
            }
            
            # Sign the JWT token using private_key from JSON (like Node.js)
            token = jwt.encode(claims, self.credentials_json['private_key'], algorithm='RS256')
            
            print(f"✅ Created JWT token for pass object: {full_object_id}")
            return {
                'id': full_object_id,
                'token': token,
                'object': generic_object
            }
                
        except Exception as e:
            print(f"❌ Error creating JWT pass object: {e}")
            return None
    
    def create_pass_from_image_jwt(self, image_path, class_name="MyFirstPass", pass_title="My Digital Pass"):
        """Create a digital pass from a barcode/QR code image using JWT method"""
        try:
            print(f"🎫 Creating digital pass from: {image_path}")
            
            # Authenticate
            if not self.authed_session:
                if not self.authenticate():
                    return None
            
            # Extract barcode data
            barcode_data, barcode_type = self.extract_barcode_data(image_path)
            if not barcode_data:
                return None
            
            # Generate IDs
            class_id = f"{class_name}Class"
            object_id = f"{class_name}Object_{uuid.uuid4().hex[:8]}"
            
            print(f"🏗️  Creating pass class: {class_id}")
            # Create pass class
            class_response = self.create_generic_pass_class(class_id, pass_title)
            if not class_response:
                return None
            
            print(f"🏗️  Creating pass object with JWT: {object_id}")
            # Create pass object using JWT method
            object_response = self.create_jwt_pass_object(
                class_id, object_id, barcode_data, barcode_type, pass_title
            )
            
            if object_response:
                full_object_id = object_response['id']
                token = object_response['token']
                
                print(f"\n🎉 Digital pass created successfully!")
                print(f"📋 Pass ID: {full_object_id}")
                print(f"📋 Class ID: {class_response['id']}")
                print(f"📋 Barcode Data: {barcode_data}")
                print(f"📋 Barcode Type: {barcode_type}")
                
                # Generate save URL using JWT token (like Node.js implementation)
                save_url = f"https://pay.google.com/gp/v/save/{token}"
                print(f"💾 Save URL: {save_url}")
                
                return {
                    'pass_id': full_object_id,
                    'class_id': class_response['id'],
                    'barcode_data': barcode_data,
                    'barcode_type': barcode_type,
                    'save_url': save_url,
                    'token': token
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error creating pass from image: {e}")
            return None

def main():
    """Main function to demonstrate usage"""
    print("🎫 Google Wallet Digital Pass Creator")
    print("=" * 50)
    
    # Initialize API
    wallet_api = GoogleWalletAPI()
    
    # Example usage
    image_path = input("Enter the path to your barcode/QR code image: ").strip()
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    pass_title = input("Enter a title for your pass (or press Enter for default): ").strip()
    if not pass_title:
        pass_title = "My Digital Pass"
    
    # Create pass
    print(f"\n🚀 Creating pass with title: {pass_title}")
    result = wallet_api.create_pass_from_image_jwt(image_path, pass_title=pass_title)
    
    if result:
        print("\n" + "="*50)
        print("🎉 SUCCESS! Your digital pass has been created!")
        print("="*50)
        print(f"📱 Open this URL on your phone to save the pass:")
        print(f"🔗 {result['save_url']}")
        print("\n📱 Instructions:")
        print("   1. Copy the URL above")
        print("   2. Open it on your mobile device")
        print("   3. Tap 'Add to Google Wallet'")
        print("   4. The pass will be added to your Google Wallet app")
    else:
        print("❌ Failed to create digital pass")

if __name__ == "__main__":
    main() 