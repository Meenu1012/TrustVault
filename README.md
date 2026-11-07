# TrustVault - Secure Document Management System



## 1. Project Overview



TrustVault is a Flask-based secure document management application. It allows users to upload, view, download, share, and manage documents with access permissions.



Document owners can control whether other users have View or Edit access. The application also maintains audit logs of important activities.



## 2. Features



- User registration and login

- User and Admin roles

- Document upload, viewing, and downloading

- Document sharing with View and Edit permissions

- Text document editing

- PDF text editing using PyMuPDF

- Document replacement and deletion

- Admin dashboard and user management

- Audit logging

- File upload size restrictions



## 3. Technologies Used



- Python

- Flask

- Flask-SQLAlchemy

- Flask-Login

- Flask-WTF

- SQLite

- HTML and CSS

- PyMuPDF

- Pytest

## 4. Project Structure

TrustVault-GitHub/
|
|-- app/
|   |-- static/
|   |   |-- css/
|   |   |-- js/
|   |
|   |-- templates/
|   |   |-- admin.html
|   |   |-- dashboard.html
|   |   |-- documents.html
|   |   |-- edit_document.html
|   |   |-- edit_pdf.html
|   |   |-- shared_documents.html
|   |
|   |-- __init__.py
|   |-- auth.py
|   |-- documents.py
|   |-- admin.py
|   |-- audit.py
|   |-- models.py
|   |-- permissions.py
|
|-- tests/
|-- instance/
|-- requirements.txt
|-- run.py
|-- PROMPTS.md
|-- THREATS.md
|-- README.md


## 5. Installation and Setup



### Step 1: Clone the repository



```bash

git clone YOUR\_GITHUB\_REPOSITORY\_URL

cd TrustVault-GitHub

```



### Step 2: Create a virtual environment



```bash

python -m venv venv

```



### Step 3: Activate the environment



Windows PowerShell:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



### Step 4: Install dependencies



```bash

pip install -r requirements.txt

```



### Step 5: Run the application



```bash

python run.py

```



Open the browser at:



```text

http://127.0.0.1:5000

```



## 6. Running Tests



```bash

python -m pytest -v

```



## 7. Security Measures



- Authentication for protected pages

- Role-based authorization

- Document ownership checks

- Shared document permission checks

- View and Edit access restrictions

- CSRF protection

- Secure session cookie settings

- File upload size restrictions

- Audit logging



## 8. AI Tools Used



ChatGPT was used for development guidance, debugging, understanding Flask concepts, reviewing document permissions, considering security risks, and preparing documentation.



See `PROMPTS.md` for the development prompt record.



## 9. Threat Model



Security risks, mitigation strategies, and testing notes are documented in `THREATS.md`.



## 10. Current Limitations



- Public deployment and hosting configuration must be completed and verified.

- Local SQLite storage is intended for development and testing.

- PDF editing is limited to supported text-editing operations.

- Further security testing is required.



## 11. Future Enhancements



- Cloud-based document storage

- Advanced PDF editing

- Email notifications for document sharing

- Improved audit-log reporting

- Additional automated security tests



## 12. Project Information



- Project Name: TrustVault

- Project Type: Secure Document Management System

- Backend: Python Flask

- Database: SQLite




