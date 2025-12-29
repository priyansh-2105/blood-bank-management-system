# Blood Bank Management System

A full-stack web application developed to streamline blood bank operations by providing a secure, centralized platform for managing donors, hospitals, blood inventory, and requests.
This project focuses on clean backend architecture, secure authentication, and practical database-driven workflows commonly used in real-world systems.

## 📌 Overview

Managing blood availability efficiently is critical in healthcare systems. This application digitizes the core processes of a blood bank, reducing manual effort and improving accessibility, accuracy, and traceability of data.
The system supports multiple user roles and provides dashboards to monitor inventory and requests in real time.

## 🚀 Key Features

- Secure user authentication and session management  
- Donor and hospital registration and management  
- Blood inventory tracking by group and quantity  
- Blood request and approval workflow  
- Admin dashboard with visual analytics  
- Email notifications for important actions  

## 🛠️ Tech Stack

### Backend
- Python  
- Flask  
- SQLAlchemy  
- Flask-Login  
- Flask-Mail  

### Frontend
- HTML5  
- Bootstrap 5  
- JavaScript  
- Chart.js  

### Database
- SQLite (easily extendable to MySQL or PostgreSQL)
  
## 🧩 Project Structure

blood-bank-management-system/
│
├── app/
│ ├── models/ # Database models
│ ├── routes/ # Application routes
│ ├── services/ # Business logic
│ ├── templates/ # HTML templates
│ └── static/ # CSS, JS, assets
│
├── migrations/
├── tests/
├── config.py
├── run.py
└── README.md

yaml
Copy code

## ⚙️ Setup Instructions

1. Clone the repository  
   ```bash
   git clone https://github.com/your-username/blood-bank-management-system.git
Create and activate a virtual environment

Install dependencies

bash
Copy code
pip install -r requirements.txt
Run the application

bash
Copy code
python run.py

http://localhost:5000

🎯 Learning Outcomes
Designed a modular Flask backend architecture
Implemented secure authentication and session handling
Applied ORM-based database modeling
Built reusable service and data-access layers
Created interactive dashboards for data visualization
Followed clean code and repository organization practices

🔮 Future Improvements
Role-based access control
REST API versioning
Docker-based deployment
Cloud database integration
Performance and security enhancements

👤 Author
Priyansh Patel
Computer Engineering Undergraduate

This project was developed as part of hands-on learning and practical application of full-stack web development concepts.
