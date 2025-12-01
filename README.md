# Final_Systems

## 1) Executive Summary

**Problem:** UVA Students have a GroupMe called WahooSwaps, the concept is to post anything that you no longer want or are selling at a discounted price. However, if you see something that you liked in the morning and then go to look at it again in the afternoon you will find that many other things have been posted since then making it hard to find what it is you wanted. This is inconvenient because sometimes you see something you like but don't have the time to text the person then and there.

**Solution:** My solution to this would be creating a website in which you don't have to scroll through what people texted in response to an item, but just scroll through the items like a shopping website. This makes it easier to find what it is that you are looking for and contact the person about possibly inquiring more information than already provided. You would also be able to reach out directly to the person that posted an item via email, which they are more likely to see as opposed to GroupMe messages. 

## 2) System Overview

**Course Concept(s):** Cloud Storage (Azure Blob Storage for images), RESTful API Design (Flask endpoints), Web Application Development (Full-stack Flask app), Cloud Deployment (Azure App Service)

**Architecture Diagram:** 
![System Architecture](assets/architecture.png)

**Data/Models/Services:** 
- **Azure Blob Storage** (`images-demo` container) - Stores user-uploaded product images (JPEG/PNG format, typically 500KB-5MB per image). Images include metadata (item name, price, seller info). Free tier: 5GB storage.
- **MongoDB Atlas** (Free tier, 512MB) - NoSQL database storing user accounts with fields: email, hashed password (bcrypt), name, registration timestamp.
- **Python Libraries:** Flask 3.0+ (web framework, MIT license), pymongo 4.6+ (MongoDB driver, Apache 2.0), azure-storage-blob 12.20+ (Azure SDK, MIT license), bcrypt 4.1+ (password hashing, Apache 2.0), gunicorn 21.0+ (production server, MIT license)
- **Resend API** (Optional, Free tier: 3,000 emails/month) - Email service for buyer-seller notifications.
- **No external datasets** - All data is user-generated content.

## 3) How to Run (Local)

**Docker:**
```bash
# build
docker build -t college-marketplace:latest .

# run
docker run --rm -p 5000:5000 --env-file .env college-marketplace:latest

# health check
curl http://localhost:5000/api/v1/health
```

**Without Docker:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Health check
curl http://127.0.0.1:5000/api/v1/health
```

**Note:** Requires `.env` file with `STORAGE_KEY`, `MONGODB_URI`, `SECRET_KEY`, and optionally `RESEND_API_KEY`.

## 4) Design Decisions

**Why this concept?** I chose to make a website because it is convenient. It is better than maintaining a GroupMe chat. GroupMe requires endless scrolling through messages and responses to find items, while a web interface displays items in a searchable gallery format, meant to be as convenient as a regular shopping website. Students would not lose track of posts buried in chat history because the chat would take place through email therefore preventing any disruption to finding items. A website also allows data such as images, prices and seller info to be easier to filter and search than through text messages.

**Why Azure Blob Storage over local file storage?**
- **Scalability:** Handles unlimited image uploads without server disk constraints.
- **Cost:** Free tier provides 5GB storage, sufficient for student marketplace use.
- **Integration:** Native compatibility with Azure App Service deployment.

**Why MongoDB over SQL database?**
- **Flexibility:** NoSQL schema allows easy addition of user fields (e.g., verified status, reputation scores) without migrations.

**Tradeoffs:** 
- **Performance:** Storing image metadata in Azure Blob metadata limits query capabilities (can't filter by price without loading all items). 
- **Cost:** Current setup is free tier only. At scale (>5GB images, >512MB users), would need paid plans (~$10-25/month). 
- **Complexity:** Added authentication and email features increase moving parts. Startup requires 3 external services (Azure, MongoDB, Resend) to be properly configured. 
- **Maintainability:** No automated tests currently. Manual testing required before each deployment.

**Security/Privacy:** 
- **Secrets Management:** All API keys stored in environment variables (`.env` locally, Azure Application Settings in production). No credentials committed to GitHub. 
- **Password Security:** Passwords never stored or logged which prevents plaintext password exposure. 
- **Input Validation:** File type checking restricts uploads to JPEG/PNG only. Email validation on registration prevents malformed addresses. 
- **Session Security:** Flask sessions use SECRET_KEY for cryptographic signing. Sessions expire on browser close. 
- **PII Handling:** User emails stored securely in MongoDB. Seller emails shared only during checkout (buyer-initiated action). No email addresses displayed publicly on site. 
- **Known Limitations:** No HTTPS enforcement on custom domains (relies on Azure's default HTTPS), vulnerable to spam uploads, vulnerable to bot accounts.

**Ops:** 
- **Logging:** Print statements to stdout/stderr captured by Azure Application Insights. Shows upload attempts, checkout events, authentication attempts. 
- **Monitoring:** Azure App Service health checks via `/api/v1/health` endpoint. Manual monitoring only - no alerts configured. 
- **Scaling:** Free tier App Service runs on single instance (no auto-scaling). Handles ~10-20 concurrent users adequately. Would need Basic tier ($13/month) for auto-scaling if usage grows beyond 100 daily active users. 
- **Known Limitations:** No database backups configured (MongoDB Atlas free tier has limited restore options). No CDN for image delivery (images served directly from Azure Blob, could be slow for international users). Session state not persisted (users logged out if App Service restarts). No database connection pooling (could cause slowdowns under heavy concurrent load).

## 5) Results & Evaluation

**Screenshots:**
See `/assets` folder for:
- `homepage.png` - Main marketplace gallery view
- `upload-form.png` - Seller item upload interface
- `cart-checkout.png` - Shopping cart and checkout flow
- `login-modal.png` - User authentication interface

**Performance:**
- **Page Load Time:** ~1.2s for gallery with 10-20 items (includes Azure Blob image loading)
- **Upload Time:** ~2-3s per image upload (500KB-2MB files)
- **Database Queries:** User login <200ms, gallery load <500ms
- **Resource Footprint:** Flask app uses ~150MB RAM, minimal CPU usage at low traffic

**Validation & Testing:**

*Manual Testing Performed:*
- User registration and login with valid/invalid credentials
- Image upload with JPEG/PNG files (success) and non-image files (rejected)
- Gallery loads all uploaded items with correct metadata
- Cart functionality: add items, remove items, calculate totals
- Checkout flow sends email notifications to sellers (when Resend configured)
- Delete functionality removes items from Azure Blob Storage
- Authentication required for upload but not for browsing

*Edge Cases Tested:*
- Large file uploads (>5MB) succeed but take longer
- Empty form submissions properly show error messages
- Duplicate email registration prevented
- Checkout without items in cart prevented
- Special characters in item names handled correctly

*Known Issues:*
- No automated test suite (time constraint)
- Email delivery not tested at scale (only 2-3 test emails sent)
- Mobile responsiveness needs improvement (primarily tested on desktop)

## 6) What's Next

**Planned Improvements:**
I plan to add text search by item name, filter by price range, and category tags such as textbooks, furniture, electronics, and clothing. I would also like to add seller ratings/reviews so that those who sell frequently can receive a verified student status with their .edu email. Another thing I'd add is integration so that you can receive emails from the website if there is anything similar to things purchased before and an optional PayPal or ApplePay integration for secure in-app payments would also improve the application. 

**Refactors:**
For refactors I'd plan to migrate item metadata from Azure Blob metadata to MongoDB for better querying/indexing. As well as adding automated testing suite (pytest for backend, Selenium for frontend). I'd also implement CI/CD pipeline with GitHub Actions for automated deployments, add Redis caching for frequently accessed gallery data and containerize with proper Dockerfile and docker-compose for easier local development.

**Stretch Features:**
I'd like to create a mobile app version of this website, item expiration dates like auto-remove listings after 30 days, show "sold" marking without deletion (keep transaction history) and have analytics dashboard for sellers (views, favorites, conversion rate.)

## 7) Links
- **GitHub Repo:** https://github.com/evelynxanaxia/Final_Systems
- **Public Cloud App:** https://collegemarketplace-grdnfmfwayddbva2.canadacentral-01.azurewebsites.net/