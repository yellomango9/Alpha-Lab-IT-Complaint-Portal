# AMC Complaint Portal

A full-stack web application built with Django and MySQL for managing complaints within an organization. The system allows users to submit complaints, staff to resolve them, and administrators to monitor and report on system usage.

---

## 🚀 Features

- User authentication and role-based access (User, Engineer, Admin)
- Submit IT complaints with optional file attachments
- Status tracking and reassignment of complaints
- Complaint type and urgency categorization
- Feedback submission and FAQ support
- Dynamic filters and search on complaint listing
- Weekly/monthly reporting with export options (TBD)
- Admin panel for managing data

---

## 🛠 Tech Stack

- **Backend:** Django 4.x (Python 3.12)
- **Database:** MySQL
- **Frontend:** Django templates (HTML, CSS, optional Bootstrap)
- **Auth:** Django's built-in authentication
- **File Uploads:** Handled via `MEDIA_ROOT`
- **Environment Config:** `python-decouple`

---

## 📂 Project Structure

Alpha-Lab-IT-Complaint-Portal/
│
├── complaints/ # Complaint app (models, views, forms, templates)
├── core/ # Core app (Department, Role)
├── faq/ # FAQ app
├── feedback/ # Feedback app
├── config/ # Django settings and root URLs
├── templates/ # Shared HTML templates
├── static/ # Static files (CSS, JS)
├── media/ # Uploaded files
├── scripts/ # Custom scripts like seed_db.py
├── requirements.txt # Python dependencies
├── .env # Environment variables
└── manage.py


---

## ⚙️ Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/yourname/Alpha-Lab-IT-Complaint-Portal.git
cd Alpha-Lab-IT-Complaint-Portal

### 2. Create and Activate Virtual Environment
python3 -m venv venv
source venv/bin/activate

### Install Dependencies
pip install -r requirements.txt


### 4. Configure Environment
Create a .env file in the root:

DEBUG=True
SECRET_KEY=your_secret_key_here
DB_NAME=alpha_lab_it_portal
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

### 5. Set Up Database
Make sure MySQL is running, then:

python manage.py makemigrations
python manage.py migrate

### 6. Seed Initial Data
python manage.py shell < scripts/seed_db.py

### 7. Create Superuser
python manage.py createsuperuser

8. Run the Server
python manage.py runserver
Then visit http://127.0.0.1:8000

🧪 Testing Features
Login as different roles

Submit complaints and attach files

Track complaints via list view

Submit feedback after resolution

Explore FAQs

Access Django admin at /admin/

📊 Reporting (Planned)
Weekly/monthly complaint stats

Filters by department/type/user/status

CSV/Excel export

Dashboard charts (future)

📦 Deployment (Checklist)
Setup Gunicorn + Nginx

Secure .env and secrets

Run with DEBUG=False

Configure MySQL backups

👨‍💻 Developed By
~vsc