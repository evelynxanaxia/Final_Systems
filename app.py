from flask import Flask, jsonify, request, render_template, session
import os, uuid, filetype, bcrypt
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv
from pymongo import MongoClient
import resend

load_dotenv()
# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
resend.api_key = os.environ.get('RESEND_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'onboarding@resend.dev')

# Azure Blob Storage setup
connection_string = os.environ.get('STORAGE_KEY')
if not connection_string:
    raise ValueError("STORAGE_KEY not found in environment variables")

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
CONTAINER_NAME = "images-demo"

# MongoDB setup
mongo_uri = os.environ.get('MONGODB_URI')
if not mongo_uri:
    raise ValueError("MONGODB_URI not found in environment variables")

mongo_client = MongoClient(mongo_uri)
db = mongo_client['marketplace']
users_collection = db['users']


# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


# ------------------------------
# HEALTH CHECK
# ------------------------------
@app.route('/api/v1/health')
def health():
    return jsonify({'status': 'ok'}), 200


# ------------------------------
# AUTHENTICATION ROUTES
# ------------------------------
@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not email or not password:
            return jsonify({"ok": False, "error": "Email and password required"}), 400
        
        # Check if user exists
        if users_collection.find_one({"email": email}):
            return jsonify({"ok": False, "error": "Email already registered"}), 400
        
        # Create user
        hashed_pw = hash_password(password)
        users_collection.insert_one({
            "email": email,
            "password": hashed_pw,
            "name": name or "User",
            "created_at": datetime.now()
        })
        
        return jsonify({"ok": True, "message": "Registration successful"}), 200
    except Exception as e:
        print(f"Register error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"ok": False, "error": "Email and password required"}), 400
        
        # Find user
        user = users_collection.find_one({"email": email})
        if not user or not check_password(password, user['password']):
            return jsonify({"ok": False, "error": "Invalid credentials"}), 401
        
        # Set session
        session['user_email'] = email
        session['user_name'] = user.get('name', 'User')
        
        return jsonify({
            "ok": True, 
            "message": "Login successful",
            "user": {"email": email, "name": user.get('name')}
        }), 200
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/v1/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"ok": True, "message": "Logged out"}), 200


# ------------------------------
# UPLOAD ITEM LISTING
# ------------------------------
@app.route('/api/v1/upload', methods=['POST'])
def upload():
    try:
        file = request.files.get("file")
        item_name = request.form.get("name")
        price = request.form.get("price")
        seller = request.form.get("seller")
        seller_email = request.form.get("seller_email")  # NEW: get seller email

        if not file:
            return jsonify({"ok": False, "error": "No file uploaded"}), 400
        
        if not seller_email:
            return jsonify({"ok": False, "error": "Seller email required. Please login first."}), 400
        
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
                "seller": seller or "unknown",
                "seller_email": seller_email  # NEW: store seller email
            },
            content_settings=ContentSettings(content_type="image/jpeg")
        )

        return jsonify({"ok": True, "url": blob_client.url}), 200

    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

# ------------------------------
# LOAD GALLERY
# ------------------------------
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
        print(f"Gallery error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------
# DELETE ITEM
# ------------------------------
@app.route('/api/v1/delete/<blob_name>', methods=['DELETE'])
def delete_item(blob_name):
    try:
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        return jsonify({"ok": True, "message": "Item deleted successfully"}), 200
        
    except Exception as e:
        print(f"Delete error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------
# CHECKOUT
# ------------------------------
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
        
        # Send email to each seller
        sellers_notified = []
        for item in cart_items:
            seller_email = item.get('seller_email')
            item_name = item.get('item_name')
            price = item.get('price')
            seller_name = item.get('seller')
            
            if seller_email and seller_email not in sellers_notified:
                try:
                    # Send email to seller
                    resend.Emails.send({
                        "from": FROM_EMAIL,
                        "to": seller_email,
                        "subject": f"🎉 Someone wants to buy your {item_name}!",
                        "html": f"""
                        <h2>Great news!</h2>
                        <p>Someone is interested in buying your item on College Marketplace.</p>
                        
                        <h3>Item Details:</h3>
                        <ul>
                            <li><strong>Item:</strong> {item_name}</li>
                            <li><strong>Price:</strong> ${price}</li>
                        </ul>
                        
                        <h3>Buyer Contact Info:</h3>
                        <ul>
                            <li><strong>Name:</strong> {buyer_name}</li>
                            <li><strong>Email:</strong> {buyer_email}</li>
                            <li><strong>Phone:</strong> {buyer_phone}</li>
                        </ul>
                        
                        <p>Please reach out to them to arrange payment and pickup!</p>
                        """
                    })
                    sellers_notified.append(seller_email)
                    print(f"Email sent to {seller_email}")
                except Exception as e:
                    print(f"Failed to send email to {seller_email}: {e}")
        
        return jsonify({
            "ok": True, 
            "message": "Order placed! Sellers have been notified.",
            "order_id": str(uuid.uuid4())
        }), 200
        
    except Exception as e:
        print(f"Checkout error: {e}")
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
