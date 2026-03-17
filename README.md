# 🛒 Django Full Stack E-Commerce Web Application

A full-stack e-commerce web application built using Django. It includes user authentication, product management, cart functionality, and online payment integration. The project is deployed and accessible online.

---

## 🔗 Live Demo
👉 https://django-full-stack-ecommerce-project.onrender.com

---

## 📌 Features

- User authentication (Signup, Login, Logout)
- Email-based login system
- Google OAuth login using Django Allauth
- Product listing and category-wise browsing
- Add to cart and remove from cart
- Order placement and order history
- Razorpay payment integration
- Password reset via email
- Responsive UI using Bootstrap
- Stock management and out-of-stock handling
- Order cancellation feature
- Wishlist functionality
- Admin analytics dashboard
---

## 🛠 Tech Stack

**Backend:** Django (Python)  
**Frontend:** HTML, CSS, JavaScript, Bootstrap  
**Database:** PostgreSQL  
**Authentication:** Django Allauth  
**Payments:** Razorpay  
**Deployment:** Render  

---

## ⚙️ Installation (Run Locally)

### 1. Clone the repository
```bash
git clone https://github.com/apoorvabhardwaj28/Django-Full-Stack-Ecommerce-Project.git
cd Django-Full-Stack-Ecommerce-Project
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate   # For Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup environment variables

Create a `.env` file in the root directory:

```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=your_database_url

EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_password

RAZORPAY_KEY_ID=your_key
RAZORPAY_KEY_SECRET=your_secret

DOMAIN=127.0.0.1:8000
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Run server
```bash
python manage.py runserver
```

---

## 📂 Project Structure

```
ecommerce/
│── config/        # Settings and URLs
│── products/      # Product logic
│── cart/          # Cart functionality
│── accounts/      # Authentication
│── order/         # Orders and payments
│── templates/     # HTML templates
│── static/        # CSS, JS, images
```

## 🚀 Deployment

- Deployed on Render
- PostgreSQL used for production database
- Static files handled using WhiteNoise
- Environment variables configured securely

## 👨‍💻 Author

**Apoorva Bhardwaj**  
GitHub: https://github.com/apoorvabhardwaj28  
LinkedIn: https://linkedin.com/in/apoorva-bhardwajj  

---
