
from getpass import getpass
import os
from database.db_handler import DatabaseHandler
from managers.alert_manager import AlertManager
from managers.auth_manager import AuthManager
from managers.backup_manager import BackupManager
from managers.bed_manager import BedManager
from managers.patient_manager import PatientManager
from managers.admission_manager import AdmissionManager
from utils.report_generator import ReportGenerator
from utils.undo_stack import UndoStack
from utils.validators import Validators


def main():
    db = DatabaseHandler(os.getenv("HOSP_DB", "hospital.db"))
    db.initialize_db()
    bed_mgr = BedManager(db)
    pat_mgr = PatientManager(db)
    adm_mgr = AdmissionManager(db, bed_mgr)
    auth = AuthManager(db)
    backup_mgr = BackupManager(db)
    alert_mgr = AlertManager(db)
    report = ReportGenerator(db)
    undo = UndoStack()

    # ensure at least one admin exists
    auth.ensure_admin_exists()

    # Login loop
    user = None
    while not user:
        print("=== Login ===")
        username = input("Username: ").strip()
        password = getpass("Password: ")
        user = auth.authenticate(username, password)
        if not user:
            print("Invalid credentials, try again.\n")

    role = user["role"]
    print(f"Welcome {username} ({role})")

    while True:
        print("\n--- Menu ---")
        print("1. View available beds")
        print("2. Add bed")
        print("3. Admit patient")
        print("4. Transfer patient")
        print("5. Discharge patient")
        print("6. Search patients")
        print("7. Generate reports")
        print("8. Send alerts (check capacity)")
        print("9. Run backup")
        print("10. Undo last action")
        if role == "admin":
            print("11. Create user")
        print("0. Exit")

        choice = input("> ").strip()
        try:
            if choice == "1":
                beds = bed_mgr.list_beds()
                if not beds:
                    print("<no beds>")
                else:
                    for r in beds:
                        print(dict(r))
            elif choice == "2":
                if role != "admin":
                    print("Only admins can add beds")
                    continue
                ward = input("Ward (ICU/HDU/Maternity/General): ").strip()
                if not Validators.validate_ward(ward):
                    print("Invalid ward")
                    continue
                eq = input("Comma-separated equipment (or empty): ").strip().split(",") if input(
                    "Add equipment? (y/n) ").lower() == "y" else []
                bed_mgr.add_bed(ward, [e.strip() for e in eq if e.strip()])
                print("Bed added.")
            elif choice == "3":
                name = input("Patient name: ").strip()
                if not Validators.validate_name(name):
                    print("Invalid name")
                    continue
                age = input("Age: ").strip()
                if not Validators.validate_age(age):
                    print("Invalid age")
                    continue
                diag = input("Diagnosis: ").strip()
                pat_mgr.add_patient(name, age, diag)
                patient = db.fetch_one(
                    "SELECT * FROM patients ORDER BY patient_id DESC LIMIT 1")
                frees = bed_mgr.get_available_beds()
                if not frees:
                    print("No free beds")
                    continue
                print("Free beds:")
                for b in frees:
                    print(dict(b))
                bed_id = int(input("Enter bed_id to assign: ").strip())
                adm = adm_mgr.admit(patient["patient_id"], bed_id)
                # Push undo: discharge the admission

                def _undo_discharge(adm_mgr, adm_id):
                    # attempt to discharge (this will free bed) -- to undo an admit we discharge immediately
                    try:
                        adm_mgr.discharge(adm_id)
                        return True
                    except Exception as e:
                        return e
                undo.push(_undo_discharge, adm_mgr, adm["admission_id"])
                print("Patient admitted. Admission id:", adm["admission_id"])
            elif choice == "4":
                adm_id = int(input("Admission id: ").strip())
                new_bed = int(input("New bed id: ").strip())
                # save old bed for undo
                old = db.fetch_one(
                    "SELECT * FROM admissions WHERE admission_id=?", (adm_id,))
                if not old:
                    print("Admission not found")
                    continue
                adm_mgr.transfer(adm_id, new_bed)
                # push undo: transfer back
                undo.push(adm_mgr.transfer, adm_id, old["bed_id"])
                print("Transferred")
            elif choice == "5":
                adm_id = int(input("Admission id to discharge: ").strip())
                # push undo: re-admit (clear date_out and re-occupy bed)
                adm_row = db.fetch_one(
                    "SELECT * FROM admissions WHERE admission_id=?", (adm_id,))
                if not adm_row:
                    print("Admission not found")
                    continue
                if adm_row["date_out"]:
                    print("Already discharged")
                    continue
                adm_mgr.discharge(adm_id)
                # define undo: set date_out to NULL and reassign bed

                def _undo_reinstate(adm_mgr, db, admission_id):
                    row = db.fetch_one(
                        "SELECT * FROM admissions WHERE admission_id=?", (admission_id,))
                    if not row:
                        return "Admission row gone"
                    # set date_out to NULL and reassign bed
                    db.execute_query(
                        "UPDATE admissions SET date_out=NULL WHERE admission_id=?", (admission_id,))
                    # no-op to set attribute available to closure
                    adm_mgr.assign_bed = bed_mgr.assign_bed
                    bed_mgr.assign_bed(row["bed_id"])
                    return True
                undo.push(_undo_reinstate, adm_mgr, db, adm_id)
                print("Discharged")
            elif choice == "6":
                rx = input("Regex for patient name: ").strip()
                res = pat_mgr.find_patient_by_name(rx)
                if not res:
                    print("<no patients>")
                else:
                    for r in res:
                        print(dict(r))
            elif choice == "7":
                occ = report.generate_occupancy()
                print("Occupancy by ward:")
                for r in occ:
                    print(r)
                free = report.list_free_beds()
                print("Free beds count:", len(free))
            elif choice == "8":
                alert_mgr.alert_if_critical_full()
            elif choice == "9":
                if role != "admin":
                    print("Only admins can run backups")
                    continue
                path = backup_mgr.create_backup()
                print("Backup created at", path)
            elif choice == "10":
                res = undo.undo()
                print("Undo result:", res)
            elif choice == "11" and role == "admin":
                uname = input("New username: ")
                pw = getpass.getpass("Password: ")
                r = input("Role (admin/clerk): ")
                auth.create_user(uname, pw, role=r)
                print("User created")
            elif choice == "0":
                print("Goodbye")
                break
            else:
                print("Invalid option")
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
