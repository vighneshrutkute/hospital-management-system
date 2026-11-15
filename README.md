# 🏥 Hospital Management System

A web-based **Hospital Management System** developed using Python, Flask, PostgreSQL, HTML and CSS. This project is designed to simplify and organize hospital operations by providing a centralized platform to manage patients, doctors, appointments, treatments, prescriptions, rooms, medicines and billing.

## 📌 Project Overview

The Hospital Management System helps manage essential hospital activities through a user-friendly web interface. It allows hospital staff to maintain patient and doctor records, schedule appointments, manage room allocations, record treatments and prescriptions, and generate bills.

The application uses **Flask** for backend development and **PostgreSQL** for database management.

## ✨ Features

- **Dashboard:** Displays an overview of hospital records, including patients, doctors, appointments and available rooms.
- **Patient Management:** Add, view, update and delete patient records.
- **Doctor Management:** Maintain doctor details, qualifications, specializations and consultation fees.
- **Department Management:** Organize hospital departments and their information.
- **Appointment Management:** Schedule and manage patient appointments with doctors.
- **Treatment Management:** Record patient diagnoses and treatment details.
- **Prescription Management:** Maintain prescriptions, medicines, dosage and instructions.
- **Room Management:** Manage hospital rooms and their availability.
- **Room Allocation:** Allocate rooms to patients and track admission details.
- **Medicine Management:** Maintain medicine records, prices and expiry dates.
- **Billing Management:** Generate and manage patient bills with calculated charges.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| PostgreSQL | Relational database |
| HTML5 | Webpage structure |
| CSS3 | Styling and layout |
| Jinja2 | Dynamic HTML templating |
| psycopg2 | PostgreSQL connectivity |
| Gunicorn | WSGI production server |

## 📂 Project Structure

```text
hospital-management-system/
│
├── static/
│   └── css/
│
├── templates/
│   ├── index.html
│   ├── patients.html
│   ├── doctors.html
│   └── ...
│
├── app.py
├── requirements.txt
└── .gitignore
```

## ⚙️ Installation and Setup

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/vighneshrutkute/hospital-management-system.git
```

### 2. Navigate to the Project Directory

```bash
cd hospital-management-system
```

### 3. Create a Virtual Environment

```bash
python3 -m venv venv
```

Activate the virtual environment:

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure PostgreSQL

- Install and start PostgreSQL.
- Create a database named `hospital`.
- Set up the required database tables before running the application.
- Configure the database connection details in `app.py` or use the `DATABASE_URL` environment variable.

### 6. Run the Application

```bash
python app.py
```

### 7. Open in Browser

Visit:

```text
http://127.0.0.1:5000/
```

The Hospital Management System should now be accessible locally.

## 🗄️ Database

The application uses PostgreSQL to store and manage hospital information.

The database includes records related to:

- Patients
- Doctors
- Departments
- Appointments
- Treatments
- Prescriptions
- Medicines
- Rooms
- Room Allocations
- Bills

## 🎯 Project Objectives

- Simplify hospital administration and daily operations.
- Maintain organized patient and doctor records.
- Improve appointment scheduling and management.
- Track treatments, prescriptions and room allocations.
- Manage medicine information and billing.
- Provide a centralized system for hospital data management.

## 🚀 Future Enhancements

- User authentication and role-based access.
- Improved reporting and analytics.
- Enhanced database security.
- Online appointment booking.
- Patient medical history and report management.
- Deployment on a free cloud hosting platform.

## 👨‍💻 Author

**Vighnesh Rutkute**

- GitHub: [@vighneshrutkute](https://github.com/vighneshrutkute)
- Project Repository: [Hospital Management System](https://github.com/vighneshrutkute/hospital-management-system)

---

*Developed as a Mini Project to demonstrate the practical application of Python, Flask, PostgreSQL and web development concepts.*
