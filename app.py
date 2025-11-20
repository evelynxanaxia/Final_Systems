from flask import Flask, jsonify, request, render_template
import os, uuid, filetype
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()
connection_string = os.environ.get('STORAGE_KEY')

print(f"Connection string loaded: {connection_string[:50] if connection_string else 'NOT FOUND'}...")
print(f"Connection string length: {len(connection_string) if connection_string else 0}")

app = Flask(__name__)

if not connection_string:
    raise ValueError("STORAGE_KEY not found in environment variables")

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
CONTAINER_NAME = "images-demo"


# ------------------------------
# HEALTH CHECK
# ------------------------------
@app.route('/api/v1/health')
def health():
    return jsonify({'status': 'ok'}), 200


# ------------------------------
# UPLOAD ITEM LISTING
# ------------------------------
@app.route('/api/v1/upload', methods=['POST'])
def upload():
    try:
        print("=== UPLOAD REQUEST RECEIVED ===")
        
        file = request.files.get("file")
        item_name = request.form.get("name")
        price = request.form.get("price")
        seller = request.form.get("seller")

        print(f"Name: {item_name}")
        print(f"Price: {price}")
        print(f"Seller: {seller}")
        print(f"File: {file}")

        if not file:
            return jsonify({"ok": False, "error": "No file uploaded"}), 400
        
        # Read file into bytes
        file_bytes = file.read()
        print(f"File bytes length: {len(file_bytes)}")

        # Validate file type
        kind = filetype.guess(file_bytes)
        if not kind or kind.mime not in ["image/jpeg", "image/png"]:
            return jsonify({"ok": False, "error": "File must be JPEG or PNG"}), 400

        # Generate unique filename
        blob_name = f"{seller}-{uuid.uuid4()}.jpg"
        print(f"Blob name: {blob_name}")

        # Upload to Azure
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

        print(f"Upload successful! URL: {blob_client.url}")
        return jsonify({"ok": True, "url": blob_client.url}), 200

    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------
# LOAD GALLERY
# ------------------------------
@app.route('/api/v1/load-gallery', methods=['GET'])
def load_gallery():
    try:
        print("=== LOAD GALLERY REQUEST RECEIVED ===")
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
        
        print(f"Found {len(items)} items")
        return jsonify({"ok": True, "items": items}), 200
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------
# DELETE ITEM
# ------------------------------
@app.route('/api/v1/delete/<blob_name>', methods=['DELETE'])
def delete_item(blob_name):
    try:
        print(f"=== DELETE REQUEST FOR: {blob_name} ===")
        
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_name)
        
        # Delete the blob
        blob_client.delete_blob()
        
        print(f"Successfully deleted: {blob_name}")
        return jsonify({"ok": True, "message": "Item deleted successfully"}), 200
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------
# CHECKOUT - Contact Seller
# ------------------------------
@app.route('/api/v1/checkout', methods=['POST'])
def checkout():
    try:
        print("=== CHECKOUT REQUEST RECEIVED ===")
        data = request.json
        
        buyer_name = data.get('buyer_name')
        buyer_email = data.get('buyer_email')
        buyer_phone = data.get('buyer_phone')
        cart_items = data.get('cart_items', [])
        
        print(f"Buyer: {buyer_name} ({buyer_email}, {buyer_phone})")
        print(f"Items: {len(cart_items)}")
        
        for item in cart_items:
            print(f"  - {item.get('item_name')} (${item.get('price')}) from {item.get('seller')}")
        
        # In a real app, you'd send emails here to connect buyer and sellers
        
        return jsonify({
            "ok": True, 
            "message": "Order placed! Sellers will contact you soon.",
            "order_id": str(uuid.uuid4())
        }), 200
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------
# FRONTEND ROUTE
# ------------------------------
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)