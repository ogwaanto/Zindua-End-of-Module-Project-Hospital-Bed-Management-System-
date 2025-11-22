Setup
Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate # on Mac or Linux: source venv/bin/activate 
pip install -r requirements.txt
Hospital Bed Management System (CLI Version)
```

A fully self-contained command-line Hospital Bed Management System built in Python.
It supports bed management, patient handling, admissions, authentication, backups, alerts, reporting, and more.

Core Features
1. Bed Management

Add new beds (Admin only)

View all beds

Search beds by:

Ward

Equipment

Availability

Automatic tracking of occupied vs free beds

2. Patient Management

Add patient records

Regex-based search for patient names

View complete patient list

3. Admission Control

Admit patients to beds

Transfer patients between beds

Discharge patients with automatic bed cleanup

Undo Stack

Every action that modifies data is recorded, enabling safe rollbacks:

Admissions

Transfers

Discharges

This provides protection against accidental operations.

User Authentication

Role-based access:

Admin

Clerk

Password hashing using SHA-256

Automatic bootstrap admin account:

Username: admin

Password: admin

Database and Persistence

Uses SQLite for all system data

Automatically initializes on first run

Reliable storage for patients, beds, and admissions

Backup System

Saves entire database into a JSON snapshot

Maintains the last 7 rotating backups

Backup actions restricted to Admin users

Designed to avoid overwriting the last valid backup

Alert System (Twilio)

Optional SMS alerts for ICU/HDU full-capacity notifications.

Modes:

Live Twilio Mode
Activated when valid Twilio credentials are detected.

Safe Fallback Mode
Prints alerts to the console when Twilio credentials are missing.

Reporting Tools

Provides essential operational reports such as:

Ward occupancy statistics

List of free beds

Admission summaries

Input Validation

Uses regular expressions to validate user inputs

Prevents invalid names, bed identifiers, and other improper entries
