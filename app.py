from flask import Flask, jsonify, request, render_template
import os, uuid, filetype
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()
connection_string = os.environ.get('STORAGE_KEY')
SENDGRID_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = "noreply@yourdomain.com"  # change this to a verified sender in SendGrid

app = Flask(__name__)

if not connection_string:
    raise ValueError("STORAGE_KEY not found in environment variables")

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
CONTAINER_NAME = "images-demo"

def send_email(to, subject, html_content):
    """Send email through SendGrid."""
    if not SENDGRID_KEY:
        print("ERROR: SendGrid API key not configured!")
        return False

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_KEY)
        response = sg.send(message)
        print(f"Email sent to {to} — Status {response.status_code}")
        return True
    except Exception as e:
        print(f"Email error to {to}: {e}")
        return False


@app.route('/api/v1/health')
def health():
    return jsonify({'status': 'ok'}), 200


@app.route('/api/v1/upload', methods=['POST'])
def upload():
    try:
        file = request.files.get("file")
        item_name = request.form.get("name")
        price = request.form.get("price")
        seller = request.form.get("seller")

        if not file:
            return jsonify({"ok": False, "error": "No file uploaded"}), 400
        
        file_bytes = file.read()

        kind = filetype.guess(file_bytes)
        if not kind or kind.mime not in ["image/jpeg", "image/png"]:
            return jsonify({"ok": False, "error": "File must be JPEG or PNG"}), 400

        blob_name = f"{seller}-{uuid.uuid4()}.jpg"

        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_name)

        blob_client.upload_blob(
            file_bytes,
            overwrite=True,
            metadata={
                "item_name": item_name or "Unknown",
                "price": price or "N/A",
                "seller": seller or "unknown"
            },
            content_settings=ContentSettings(content_type="image/jpeg")
        )

        return jsonify({"ok": True, "url": blob_client.url}), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/v1/load-gallery', methods=['GET'])
def load_gallery():
    try:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blobs = container_client.list_blobs()
        
        items = []
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob.name)
            properties = blob_client.get_blob_properties()
            
            items.append({
                "name": blob.name,
                "url": blob_client.url,
                "item_name": properties.metadata.get("item_name", "Unknown"),
                "price": properties.metadata.get("price", "N/A"),
                "seller": properties.metadata.get("seller", "Unknown")
            })

        return jsonify({"ok": True, "items": items}), 200
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/v1/delete/<blob_name>', methods=['DELETE'])
def delete_item(blob_name):
    try:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        return jsonify({"ok": True, "message": "Item deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# -------------------------
# CHECKOUT 
# -------------------------
@app.route('/api/v1/checkout', methods=['POST'])
def checkout():
    try:
        data = request.json
        
        buyer_name = data.get('buyer_name')
        buyer_email = data.get('buyer_email')
        buyer_phone = data.get('buyer_phone')
        cart_items = data.get('cart_items', [])
        
        print(f"=== CHECKOUT REQUEST ===")
        print(f"Buyer: {buyer_name} ({buyer_email}, {buyer_phone})")
        print(f"Items: {len(cart_items)}")
        
        for item in cart_items:
            print(f"  - {item.get('item_name')} (${item.get('price')}) from {item.get('seller')}")
        
        return jsonify({
            "ok": True, 
            "message": "Order placed! Check your email for seller contact info.",
            "order_id": str(uuid.uuid4())
        }), 200
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
