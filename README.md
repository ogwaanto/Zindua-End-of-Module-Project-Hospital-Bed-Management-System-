Hospital Bed Management System (CLI Version)

A fully self-contained command-line Hospital Bed Management System built in Python.
It provides:

Bed, patient, and admission management

Role-based access control (Admin / Clerk)

Undo stack for reversible actions

Database persistence (SQLite)

Backup system (JSON-based, rotating last 7 backups)

Twilio-based alerting (optional; safe fallbacks included)

Basic reporting tools

Input validation using regex

TDD-ready unit test structure (suggested directory tree support)

Features Overview
 Bed Management

Add beds (admins only)

View all beds

Search beds (ward, equipment, availability)

Track occupied vs free beds automatically

 Patient Management

Add patient records

Regex-based search for patient names

View full patient list

 Admission Control

Admit patients to beds

Transfer patients between beds

Discharge patients with automatic bed cleanup

 Undo Stack

Every destructive action pushes an undo operation, allowing you to revert:

Admissions

Transfers

Discharges

 User Authentication

Role-based access (admin, clerk)

Password hashing via SHA-256

Automatic bootstrap admin user (admin / admin)

 Backup System

Saves database state to JSON

Keeps the last 7 backups

Admin-only operation

 Alert System (Twilio)

Optional SMS alerts when ICU/HDU reach full capacity

Auto-detects Twilio credentials

Safe fallback mode prints alerts instead of sending SMS

 Reports

Ward occupancy statistics

List of free beds

