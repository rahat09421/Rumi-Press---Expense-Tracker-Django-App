# Rumi Press – Distribution Tracker

Rumi Press is a Django-based application to manage books, categories, and distribution expenses. It includes role-based access (Superuser vs Admin), audit logging for admin activity, and an admin management flow with email verification.

## Versions
- Python: 3.13
- Django: 5.2.7

## Quick Start
- Clone the project to your machine.
- Create and activate a virtual environment.
- Install dependencies: `pip install -r requirements.txt`
- Apply migrations: `python manage.py migrate`
- Start the server: `python manage.py runserver`
- Open the app: `http://127.0.0.1:8000/`

## Authentication
- Login is available at `/accounts/login/`.
- Inactive accounts see a clear alert explaining deactivation by the Superadmin.
- Logout is available from the navbar; it redirects back to the login page.

## Managing Admins
- Superusers can visit `/accounts/create-admin/` to create Admin users.
- New Admins receive a verification link via email; after verification, they can sign in.
- Superusers can set Admin status (active/inactive) from the same page.

## Bootstrap Superuser
- If no superuser exists yet, visit `/accounts/bootstrap-superuser/` to create the first one via a secure form.
- Alternatively, use `python manage.py createsuperuser`.

## Email Configuration
- Development uses the console backend to print emails to the server console.
- To enable SMTP, set environment variables before running the server:
  - `EMAIL_HOST`
  - `EMAIL_PORT`
  - `EMAIL_HOST_USER`
  - `EMAIL_HOST_PASSWORD`
  - `EMAIL_USE_TLS` (true/false)
  - `EMAIL_USE_SSL` (true/false)

## Running Tests
- Execute all tests: `python manage.py test`
- Accounts-only tests: `python manage.py test accounts`

## Notes
- Default database is SQLite; configure `DATABASES` in `rumipress/settings.py` for other engines.
- Static assets use Bootstrap via CDN. No extra asset build step is required.