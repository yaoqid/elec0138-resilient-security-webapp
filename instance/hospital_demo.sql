PRAGMA foreign_keys = ON;

CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    gender TEXT NOT NULL,
    phone TEXT,
    email TEXT UNIQUE
);

CREATE TABLE doctors (
    doctor_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    department TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

CREATE TABLE medical_records (
    record_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment TEXT NOT NULL,
    notes TEXT,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'doctor', 'patient')),
    linked_id INTEGER
);

CREATE TABLE login_logs (
    log_id      INTEGER PRIMARY KEY,
    timestamp   TEXT NOT NULL,
    username    TEXT NOT NULL,
    ip_address  TEXT,
    success     INTEGER NOT NULL CHECK (success IN (0, 1)),
    role        TEXT,
    note        TEXT
);

-- Admin account inserted by init_db.py with hashed password
