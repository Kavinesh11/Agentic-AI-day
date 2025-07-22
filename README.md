# Google Wallet API Integration

## This project creates digital passes in Google Wallet from barcode/QR code images using the Google Wallet API.

## Need to make sure that, service account authentication provided has been added to wallet business console. Else it'll raise 403
## 🎫 Features

- **Barcode/QR Code Detection**: Automatically extracts data from barcode and QR code images
- **Google Wallet Integration**: Creates digital passes that can be added to Google Wallet
- **Multiple Format Support**: Supports various barcode formats (QR Code, Code 128, Code 39, EAN, UPC, etc.)
- **Batch Processing**: Create multiple passes from different images
- **Merchant Integration**: Uses your Google Merchant ID for pass creation

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Google Cloud Project with Wallet API enabled
- Google Merchant Account (Merchant ID: `BCR2DN7TZCMZFUAW`)
- OAuth 2.0 credentials (already configured in `token.json`)

### Common Issues

1. **"No barcode or QR code found"**
   - Ensure the image is clear and well-lit
   - Try different image formats (JPG, PNG)
   - Check if the barcode is not damaged or obscured

2. **Authentication errors**
   - Verify `token.json` exists and is valid
   - Re-run the script to refresh OAuth tokens
   - Check Google Cloud Console for API enablement

3. **API quota exceeded**
   - Check your Google Cloud Console quotas
   - Wait for quota reset or request increase

## 🎯 Supported Barcode Types

- **QR Code**: Most common for digital passes
- **Code 128**: Standard barcode format
- **Code 39**: Industrial barcode format
- **EAN-13**: European Article Number (13 digits)
- **EAN-8**: European Article Number (8 digits)
- **UPC-A**: Universal Product Code (12 digits)
- **UPC-E**: Universal Product Code (8 digits)

## 🔧 Configuration

### Merchant ID
Your Merchant ID is configured in the `GoogleWalletAPI` class:
```python
self.merchant_id = "BCR2DN7TZCMZFUAW"
```

### Pass Customization
You can customize the pass appearance by modifying the `create_generic_pass_class` and `create_generic_pass_object` methods:

- **Colors**: Change `hexBackgroundColor`
- **Logo**: Update the logo URL
- **Text**: Modify card titles and headers
- **Validity**: Adjust the `validTimeInterval`

## 🎉 Your First Pass

To create your first pass:

1. Take a photo of a barcode or QR code
2. Save it in the project directory (e.g., as `qrcode.jpg`)
3. Run: `python google_wallet_api_simple.py`
4. Enter the image filename when prompted
5. Open the generated Save URL on your phone
6. Add the pass to your Google Wallet!

**Merchant ID**: BCR2DN7TZCMZFUAW  
**Developer**: Sai Nivedh
