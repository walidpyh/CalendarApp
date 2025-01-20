# CalendarApp

## Overview
CalendarApp is a small but robust web application that demonstrates secure web development practices. It allows users to create, view, and manage calendar events, while implementing multiple layers of security to protect against common web vulnerabilities.

## Key Features
- **Secure User Authentication**: Login with password hashing, CSRF protection, and optional two-factor authentication (2FA).
- **Event Management**: Add, edit, and delete events with permissions strictly limited to the event owner.
- **Interactive Calendar**: A dynamic and user-friendly interface using FullCalendar.
- **Rate Limiting**: Protects against brute-force and DoS attacks using Nginx rate limiting.

## Security Highlights
1. **Cross-Site Scripting (XSS) Prevention**:
   - User input is sanitized and escaped using Jinja2 templating to prevent malicious scripts from executing.

2. **Cross-Site Request Forgery (CSRF) Protection**:
   - All forms are secured with CSRF tokens to prevent unauthorized actions.

3. **SQL Injection Protection**:
   - SQL queries are managed with SQLAlchemy ORM, ensuring parameterized queries.

4. **Brute-Force and DoS Mitigation**:
   - Rate limiting configured with Nginx to restrict requests per IP, particularly on sensitive endpoints like `/login`.

5. **Two-Factor Authentication (2FA)**:
   - Adds an additional layer of security by requiring a one-time password (OTP) after login.

6. **Secure Deployment**:
   - Hosted on an isolated user account with minimal permissions.
   - Application runs in a virtual environment to ensure process isolation.

## Technologies Used
- **Frontend**: [FullCalendar](https://fullcalendar.io/), Bootstrap
- **Backend**: [Flask](https://flask.palletsprojects.com/en/stable/#user-s-guide)
- **Web Server**: [Nginx](https://nginx.org/en/)
- **Database**: SQLAlchemy with SQLite (or other supported databases)
- **Security**: [Google reCAPTCHA](https://www.google.com/recaptcha/about/), CSRF tokens, OTP, and Nginx rate limiting


## Getting Started
### Prerequisites
- Python 3.8+
- Virtualenv
- Nginx
