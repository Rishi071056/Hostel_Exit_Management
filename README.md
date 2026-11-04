
# Hostel Exit Management System

A web-based Hostel Exit Management System designed to digitize and simplify hostel exit permissions, student registration, warden approvals, and security guard monitoring.

The system provides separate dashboards for Students, Wardens, and Security Guards to make hostel exit and entry management more efficient, secure, and transparent.

## Team Members

| Name | Role |
|---|---|
| Rishi | Developer |
| Saksham | Developer |

## Features

### Student
- Student registration with email OTP verification.
- Face recognition-based registration and login.
- Password-based login.
- Student dashboard.
- Submit hostel exit requests.
- View exit request approval status.
- Submit and track complaints.
- View digital exit receipt numbers.
- Track exit and return status.

### Warden
- Warden registration and email verification.
- Warden dashboard.
- Review and approve student registrations.
- Approve or reject student exit requests.
- Manage student complaints.
- Approve security guard registrations.
- Monitor students currently outside the hostel.

### Security Guard
- Guard registration.
- Warden approval for guard accounts.
- Guard login and dashboard.
- View approved exit requests.
- Mark students as exited.
- Generate digital receipt numbers.
- Verify receipt numbers when students return.
- View students currently outside.
- Monitor daily exit and return activity.

## Technology Stack

### Backend
- Python
- FastAPI
- Supabase
- PostgreSQL
- JWT Authentication
- Face Recognition
- Brevo Email API

### Frontend
- HTML
- CSS
- JavaScript

### Tools
- Visual Studio Code
- Git
- GitHub
- Swagger UI

## Project Structure

```text
Hostel_Exit_Management/
│
├── backend/
│   ├── routers/
│   │   ├── student.py
│   │   ├── warden.py
│   │   └── guard.py
│   │
│   ├── services/
│   ├── auth.py
│   ├── config.py
│   ├── crud.py
│   ├── database.py
│   ├── dependencies.py
│   └── schemas.py
│
├── frontend/
│   ├── index.html
│   ├── register.html
│   ├── student-dashboard.html
│   ├── warden-dashboard.html
│   ├── guard-dashboard.html
│   ├── script.js
│   ├── register.js
│   ├── student.js
│   ├── warden.js
│   ├── guard.js
│   └── style.css
│
├── main.py
├── requirements.txt
├── .env
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Rishi071056/Hostel_Exit_Management.git
```

Move into the project directory:

```bash
cd Hostel_Exit_Management
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

Add the required configuration values:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SECRET_KEY=your_jwt_secret
BREVO_API_KEY=your_brevo_api_key
```

Use the exact variable names required by `backend/config.py` and the application code.

**Important:** Never upload your actual `.env` file or expose API keys, database credentials, or JWT secrets on GitHub.

### 5. Run the Backend

From the project root directory:

```bash
uvicorn main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Run the Frontend

Open the `frontend` folder in Visual Studio Code.

Open `index.html` using the Live Server extension.

The frontend will open in your browser.

Make sure the frontend API configuration points to the running backend.

## Database

The project uses Supabase with PostgreSQL for storing application data.

Database functionality includes:
- Student records.
- Pending student registrations.
- Registration OTP verification.
- Warden records.
- Security guard records.
- Exit requests.
- Complaints.
- Exit and return information.
- Digital receipt numbers.

The database tables must be configured in Supabase before running the application.

## GitHub Collaboration Workflow

This project is maintained collaboratively by Rishi and Saksham.

### Rishi's Repository

```text
https://github.com/Rishi071056/Hostel_Exit_Management
```

### Saksham's Repository

```text
https://github.com/saksham2806/Hostel_Exit_Management
```

### Rishi: Push Your Changes

```bash
git add .
git commit -m "Describe your changes"
git push origin main
```

### Saksham: Get Rishi's Latest Changes

Fetch Rishi's repository:

```bash
git fetch teammate
```

Merge the changes:

```bash
git merge teammate/main
```

Push the merged project to Saksham's repository:

```bash
git push origin main
```

### Both Developers: Update Local Code

```bash
git pull origin main
```

Always commit or back up your local work before merging changes.

## Security

- Passwords are stored as hashes.
- JWT authentication is used for protected routes.
- Role-based authorization separates Student, Warden, and Guard access.
- OTP verification is used during registration.
- Sensitive credentials must be stored in environment variables.
- Never commit `.env` files to GitHub.

## Future Improvements

- Improved notification system.
- Enhanced reporting and analytics.
- Better deployment and production monitoring.
- Additional security and audit features.

## License

This project is developed as a collaborative academic project by Rishi and Saksham.
