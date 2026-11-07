# TrustVault - Secure Document Management System

## 1. Project Overview

TrustVault is a Flask-based secure document management application that allows users to upload, view, download, share, edit, and manage documents with access permissions.

Document owners can control whether other users receive View or Edit access. The application also maintains audit logs of important activities.

## 2. Live Application

**Live Website:** https://trustvault-iygr.onrender.com

**GitHub Repository:** https://github.com/Meenu1012/TrustVault

**Note:** The Render free service may take some time to start after a period of inactivity.

## 3. Features

- User registration and login
- User and Admin roles
- Document upload, viewing, and downloading
- Document sharing with View and Edit permissions
- Text document editing
- PDF text editing using PyMuPDF
- Document replacement and deletion
- Admin dashboard and user management
- Security audit logging
- File upload size restrictions
- Access control for shared documents

## 4. Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- SQLite
- HTML, CSS, and JavaScript
- PyMuPDF
- Pytest
- Gunicorn
- Supabase (optional configuration)

## 5. Installation and Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/Meenu1012/TrustVault.git
cd TrustVault
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

### Step 3: Activate the environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure environment variables

Create a `.env` file in the project root if you need custom configuration.

Supported environment variables:

- `SECRET_KEY` – Flask application secret key. Set a strong random value, especially in production.
- `ADMIN_SETUP_KEY` – Key used to protect the initial admin setup route.
- `DATABASE_URL` – Optional database connection URL. SQLite is used when this is not configured.
- `SUPABASE_URL` and `SUPABASE_KEY` – Optional Supabase Storage configuration. Both must be provided to initialize the Supabase client.
- `FLASK_ENV` and `RENDER` – Used to detect production deployment and configure secure session cookies.

Do not commit `.env` files, passwords, API keys, or other secrets to GitHub.

### Step 6: Run the application

```bash
python run.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

## 6. Running Tests

Run the automated test suite:

```bash
python -m pytest -v
```

The current automated test suite contains seven tests covering:

- Application startup
- Home page access
- User registration
- User login
- Unauthorized document access
- Document upload
- View-only replacement restrictions

## 7. Security Measures

- Authentication for protected pages
- Role-based authorization
- Document ownership checks
- Shared document permission checks
- View and Edit access restrictions
- CSRF protection
- Secure session cookie settings
- File upload size restrictions
- Security audit logging

## 8. AI Tools Used

ChatGPT was used for development guidance, debugging, understanding Flask concepts, reviewing document permissions, considering security risks, and preparing documentation.

See `PROMPTS.md` for the development prompt record.

## 9. Threat Model

Security risks, mitigation strategies, and testing notes are documented in `THREATS.md`.

## 10. Current Limitations

- The Render free service may experience cold-start delays after inactivity.
- SQLite and local file storage are used by the application. Persistence across hosting restarts or redeployments has not been independently verified.
- PDF editing is limited to supported text-editing operations and is not a full-featured PDF editor.
- Additional automated security and deployment testing would improve reliability.

## 11. Future Enhancements

- Persistent cloud-based document storage
- Advanced PDF editing
- Email notifications for document sharing
- Improved audit-log reporting
- Additional automated security tests
- Enhanced document version management

## 12. Project Information

- **Project Name:** TrustVault
- **Project Type:** Secure Document Management System
- **Backend:** Python Flask
- **Database:** SQLite
- **Deployment:** Render
- **Source Code:** GitHub