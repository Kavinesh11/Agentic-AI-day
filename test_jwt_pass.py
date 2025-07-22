#!/usr/bin/env python3
"""
Test script for JWT-based Google Wallet pass creation
This should work like the Node.js reference implementation
"""

from google_wallet_api import GoogleWalletAPI
import os

def test_jwt_pass_creation():
    """Test JWT-based pass creation functionality"""
    print("🎫 Testing JWT-based pass creation...")
    print("=" * 50)
    
    # Initialize API
    wallet_api = GoogleWalletAPI()
    
    # Check for image file
    image_path = "qrcode.jpg"
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        print("Please ensure you have a barcode/QR code image named 'qrcode.jpg' in this directory")
        return False
    
    print(f"📷 Using image: {image_path}")
    
    try:
        print("\n🚀 Creating pass using JWT method (like Node.js)...")
        
        # Create pass using JWT method
        result = wallet_api.create_pass_from_image_jwt(
            image_path=image_path,
            class_name="SAIEVENT",
            pass_title="new-test-1-sai-namma-dhaan"
        )
        
        if result:
            print("\n" + "="*60)
            print("🎉 SUCCESS! JWT-based pass creation worked!")
            print("="*60)
            
            print(f"\n📋 Pass Details:")
            print(f"   📝 Title: new-test-1-sai-namma-dhaan")
            print(f"   🆔 Pass ID: {result['pass_id']}")
            print(f"   📊 Barcode Type: {result['barcode_type']}")
            print(f"   📄 Barcode Data: {result['barcode_data'][:50]}{'...' if len(result['barcode_data']) > 50 else ''}")
            
            print(f"\n📱 ADD TO YOUR PHONE:")
            print(f"🔗 {result['save_url']}")
            
            print(f"\n📱 Instructions:")
            print(f"   1. Copy the URL above")
            print(f"   2. Open it on your mobile device")
            print(f"   3. Tap 'Add to Google Wallet'")
            print(f"   4. The pass should now work properly!")
            
            # Save details
            filename = "jwt_pass_details.txt"
            with open(filename, 'w') as f:
                f.write("JWT-Based Digital Pass - Details\n")
                f.write("===============================\n\n")
                f.write(f"Title: new-test-1-sai-namma-dhaan\n")
                f.write(f"Pass ID: {result['pass_id']}\n")
                f.write(f"Class ID: {result['class_id']}\n")
                f.write(f"Barcode Type: {result['barcode_type']}\n")
                f.write(f"Barcode Data: {result['barcode_data']}\n")
                f.write(f"Save URL: {result['save_url']}\n")
                f.write(f"JWT Token: {result['token']}\n")
                f.write(f"Image Used: {image_path}\n")
            
            print(f"\n💾 Pass details saved to: {filename}")
            
            print(f"\n🔍 Key Differences from Previous Implementation:")
            print(f"   ✅ Uses JWT tokens like Node.js reference")
            print(f"   ✅ Proper save URL format with token")
            print(f"   ✅ Includes text modules with barcode info")
            print(f"   ✅ Uses same image assets as working examples")
            
            return True
            
        else:
            print("\n❌ Failed to create JWT-based pass")
            print("💡 Check the error messages above for details")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during JWT pass creation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🎫 Google Wallet JWT Pass Creator")
    print("This implementation follows the working Node.js reference")
    print("-" * 60)
    
    success = test_jwt_pass_creation()
    
    if success:
        print(f"\n🎊 JWT-based pass creation successful!")
        print(f"This should resolve the 'Something went wrong' error you were seeing.")
    else:
        print(f"\n💡 Troubleshooting:")
        print(f"   - Ensure credentials.json is valid")
        print(f"   - Check that the image contains a clear barcode/QR code")
        print(f"   - Verify your issuer ID is correct")

if __name__ == "__main__":
    main() 