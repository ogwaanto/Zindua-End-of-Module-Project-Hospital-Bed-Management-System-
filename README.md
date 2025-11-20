Complete Python CLI application to manage hospital beds, patients, admissions, reports, backups, alerts, and users. Features:
- Bed, Patient, Admission management
- SQLite database
- Regex validation
- Role-based access (admin, clerk)
- Undo stack
- Automatic daily backup (JSON)
- SMS/WhatsApp alerts placeholder (Twilio)
- Colorized terminal UI using rich
- Unit tests (unittest)

Setup
1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate # on Windows: venv\Scripts\activate
pip install -r requirements.txt