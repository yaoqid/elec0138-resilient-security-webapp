"""
Synthetic data generator for the hospital demo database.
Generates 100 realistic patients, assigns them to doctors, and creates
medical records using real ICD-10 diagnosis codes.

Usage:
    pip install faker
    python generate_data.py
"""

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from faker import Faker
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "instance" / "hospital_demo.db"

fake = Faker("en_GB")
random.seed(42)
Faker.seed(42)

# --- ICD-10 diagnosis codes with treatments ---
DIAGNOSES = [
    ("J06.9",  "Acute upper respiratory infection",        "Rest, fluids, paracetamol",                 "Monitor for secondary infection."),
    ("I10",    "Essential hypertension",                   "Lifestyle changes, ACE inhibitor prescribed","Follow-up BP check in 4 weeks."),
    ("E11.9",  "Type 2 diabetes mellitus",                 "Metformin 500mg twice daily, diet advice",   "HbA1c recheck in 3 months."),
    ("J45.0",  "Predominantly allergic asthma",            "Salbutamol inhaler, allergen avoidance",     "Spirometry booked."),
    ("M54.5",  "Low back pain",                            "Physiotherapy referral, ibuprofen PRN",      "Reassess in 6 weeks."),
    ("F32.1",  "Moderate depressive episode",              "SSRI prescribed, CBT referral",              "Crisis plan discussed with patient."),
    ("K21.0",  "Gastro-oesophageal reflux with oesophagitis","Omeprazole 20mg daily, dietary advice",   "Avoid NSAIDs."),
    ("I21.0",  "ST elevation myocardial infarction",       "Aspirin, clopidogrel, PCI performed",        "Cardiac rehab referral issued."),
    ("N39.0",  "Urinary tract infection",                  "Trimethoprim 200mg for 7 days",              "Urine culture sent."),
    ("D50.9",  "Iron deficiency anaemia",                  "Ferrous sulfate 200mg three times daily",    "Repeat FBC in 8 weeks."),
    ("G43.9",  "Migraine",                                 "Sumatriptan 50mg at onset, lifestyle review","Headache diary started."),
    ("L20.9",  "Atopic dermatitis",                        "Emollient cream, mild topical steroid",      "Avoid known triggers."),
    ("J18.9",  "Pneumonia",                                "Amoxicillin 500mg three times daily, rest",  "CXR in 6 weeks to confirm resolution."),
    ("I25.1",  "Atherosclerotic heart disease",            "Statin therapy, aspirin, lifestyle changes", "Annual cardiology review."),
    ("F41.1",  "Generalised anxiety disorder",             "CBT referral, low-dose sertraline",          "Safety plan provided."),
]

DEPARTMENTS = ["Cardiology", "General Medicine", "Respiratory", "Mental Health", "Orthopaedics"]

DOCTOR_SEED = [
    (1, "Dr. Amelia Carter", "Cardiology",       "amelia.carter@demo-hospital.org"),
    (2, "Dr. Daniel Shah",   "General Medicine", "daniel.shah@demo-hospital.org"),
    (3, "Dr. Priya Nair",    "Respiratory",      "priya.nair@demo-hospital.org"),
    (4, "Dr. James O'Brien", "Mental Health",    "james.obrien@demo-hospital.org"),
    (5, "Dr. Mei Zhang",     "Orthopaedics",     "mei.zhang@demo-hospital.org"),
]


def random_date(start_year=2024, end_year=2026):
    start = date(start_year, 1, 1)
    end = date(end_year, 3, 20)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def generate(n_patients=100):
    if not DATABASE.exists():
        raise FileNotFoundError(
            f"Database not found at {DATABASE}. Run `python init_db.py` first."
        )

    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")

    # --- Insert doctors + create a user account for each ---
    existing_usernames = set(
        row[0] for row in conn.execute("SELECT username FROM users")
    )
    for doc_id, name, dept, email in DOCTOR_SEED:
        conn.execute(
            "INSERT OR IGNORE INTO doctors (doctor_id, full_name, department, email) VALUES (?, ?, ?, ?)",
            (doc_id, name, dept, email),
        )
        # Generate username from surname + first initial e.g. "cartera"
        parts = name.replace("Dr. ", "").replace("Dr ", "").split()
        username = (parts[-1] + parts[0][0]).lower().replace("'", "")
        if username in existing_usernames:
            username = f"{username}{doc_id}"
        existing_usernames.add(username)
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password, role, linked_id) VALUES (?, ?, 'doctor', ?)",
            (username, generate_password_hash("doctor123"), doc_id),
        )

    # --- Generate patients + users + medical records ---
    patient_ids = []
    existing_emails = set(
        row[0] for row in conn.execute("SELECT email FROM patients WHERE email IS NOT NULL")
    )

    for i in range(n_patients):
        gender = random.choice(["Male", "Female"])
        if gender == "Male":
            full_name = fake.name_male()
        else:
            full_name = fake.name_female()

        dob = fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat()
        phone = fake.phone_number()[:20]

        # Unique email
        email = fake.email()
        attempts = 0
        while email in existing_emails and attempts < 10:
            email = fake.email()
            attempts += 1
        existing_emails.add(email)

        cursor = conn.execute(
            "INSERT INTO patients (full_name, date_of_birth, gender, phone, email) VALUES (?, ?, ?, ?, ?)",
            (full_name, dob, gender, phone, email),
        )
        patient_id = cursor.lastrowid
        patient_ids.append(patient_id)

        # Username from name
        base_user = (full_name.split()[-1] + full_name.split()[0][0]).lower().replace("'", "")
        username = base_user
        suffix = 1
        while username in existing_usernames:
            username = f"{base_user}{suffix}"
            suffix += 1
        existing_usernames.add(username)

        conn.execute(
            "INSERT INTO users (username, password, role, linked_id) VALUES (?, ?, 'patient', ?)",
            (username, generate_password_hash("patient123"), patient_id),
        )

        # 1-3 medical records per patient
        n_records = random.randint(1, 3)
        used_diagnoses = random.sample(DIAGNOSES, min(n_records, len(DIAGNOSES)))
        for icd_code, diagnosis, treatment, notes in used_diagnoses:
            doctor_id = random.randint(1, len(DOCTOR_SEED))
            last_updated = f"{random_date()} {random.randint(8,17):02d}:{random.randint(0,59):02d}:00"
            conn.execute(
                """
                INSERT INTO medical_records
                    (patient_id, doctor_id, diagnosis, treatment, notes, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (patient_id, doctor_id, f"[{icd_code}] {diagnosis}", treatment, notes, last_updated),
            )

    conn.commit()
    conn.close()

    total_patients = 4 + n_patients  # original 4 + generated
    print(f"Generated {n_patients} synthetic patients (total: {total_patients})")
    print(f"Database: {DATABASE}")


if __name__ == "__main__":
    generate(100)
