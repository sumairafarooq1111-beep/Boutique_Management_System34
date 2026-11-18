# 👗 Boutique Management System

A full-stack, cloud-deployed database application designed to digitize and automate the daily operations of a clothing boutique. This system manages customers, product inventory, order processing, and custom tailoring, replacing manual paperwork with a secure, centralized database.

## 🚀 Live Demo
**Website Link:** [https://boutique-system-three.vercel.app](https://boutique-system-three.vercel.app)
**Login Credentials:**
*   **Username:** `admin`
*   **Password:** `admin123` *(or your custom password)*

## ✨ Key Features
*   **Authentication & Security:** Secure login system to protect boutique data.
*   **Dashboard:** Real-time analytics showing total customers, products, orders, and pending tailoring jobs. Includes low-stock alerts.
*   **Customer Management:** Store detailed profiles including exact measurements (chest, waist, hip, shoulder) for custom tailoring.
*   **Inventory Management:** Track ready-made products, prices, and stock levels. Auto-alerts when stock is low.
*   **Order Processing:** Place orders with automatic stock deduction and status tracking (Pending, Processing, Ready, Delivered).
*   **Tailoring Management:** Manage custom stitching orders with advance payments and auto-calculated balances.
*   **AI Chatbot (Groq):** A floating customer support assistant powered by Llama 3.3 (via Groq API) to answer user queries instantly.

## 🛠️ Tech Stack
*   **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2
*   **Backend:** Python 3, Flask
*   **Database:** PostgreSQL
*   **Cloud Deployment:** Vercel (Web Hosting), Neon (Cloud PostgreSQL)
*   **AI Integration:** Groq API (Llama 3.3-70b-versatile model)

## 🗄️ Database Schema (10 Tables)
The system uses a highly relational PostgreSQL database with strict Foreign Key constraints:
1.  `users` (Authentication)
2.  `customers` (Profiles & Measurements)
3.  `categories` (Product Categories)
4.  `suppliers` (Fabric/Product Suppliers)
5.  `products` (Inventory)
6.  `employees` (Tailors and Staff)
7.  `orders` (Ready-made sales)
8.  `order_items` (Specific items in an order)
9.  `tailoring_orders` (Custom stitching jobs with auto-calculated balance)
10. `payments` (Transaction history)

## ☁️ Cloud Deployment Architecture
This project is fully deployed to the cloud using a free-tier, modern architecture, allowing access from anywhere in the world without needing local servers.

*   **1. Database Hosting (Neon):** 
    The local PostgreSQL database was migrated to **Neon** (a serverless PostgreSQL platform). The connection string is securely passed to the backend using environment variables (`DATABASE_URL`).
*   **2. Application Hosting (Vercel):** 
    The Flask backend and HTML frontend are hosted on **Vercel**. A `vercel.json` file is used to route serverless function requests directly to `app.py`. 
*   **3. Environment Variables:** 
    Sensitive data (Database URL, Secret Keys, and Groq API Key) are securely stored in the Vercel dashboard, preventing exposure in the source code.
*   **4. Serverless Execution:** 
    The application runs via `gunicorn` (defined in the `Procfile`) and is dynamically built and deployed every time a change is pushed to the `main` branch of this GitHub repository.

## 💻 How to Run Locally
If you want to run this project on your local machine:

1.  Clone the repository: `git clone https://github.com/sumairafarooq1111-beep/boutique-system.git`
2.  Install dependencies: `pip install -r requirements.txt`
3.  Set up the `.env` file with your local PostgreSQL credentials and Groq API key.
4.  Run the app: `python app.py`
5.  Open `http://127.0.0.1:5000` in your browser.

---
*Developed as a University DBMS Project.*