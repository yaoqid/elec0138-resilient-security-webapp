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

INSERT INTO doctors (doctor_id, full_name, department, email) VALUES
(1, 'Dr. Amelia Carter', 'Cardiology', 'amelia.carter@demo-hospital.org'),
(2, 'Dr. Daniel Shah', 'General Medicine', 'daniel.shah@demo-hospital.org');

INSERT INTO patients (patient_id, full_name, date_of_birth, gender, phone, email) VALUES
(1, 'Olivia Bennett', '1992-04-18', 'Female', '07123 456781', 'olivia.bennett@example.com'),
(2, 'Ethan Collins', '1985-09-02', 'Male', '07123 456782', 'ethan.collins@example.com'),
(3, 'Sophia Turner', '2001-01-27', 'Female', '07123 456783', 'sophia.turner@example.com'),
(4, 'Liam Foster', '1978-12-11', 'Male', '07123 456784', 'liam.foster@example.com');

INSERT INTO medical_records (record_id, patient_id, doctor_id, diagnosis, treatment, notes, last_updated) VALUES
(1, 1, 2, 'Seasonal influenza', 'Rest, fluids, and paracetamol for fever management', 'Patient advised to return if symptoms worsen after 5 days.', '2026-03-10 09:30:00'),
(2, 2, 1, 'Mild hypertension', 'Lifestyle changes and blood pressure monitoring', 'Follow-up review scheduled in 6 weeks.', '2026-03-11 14:15:00'),
(3, 3, 2, 'Iron deficiency anaemia', 'Oral iron supplements for 8 weeks', 'Discussed diet improvement and repeat blood test.', '2026-03-12 11:00:00'),
(4, 4, 1, 'Stable angina', 'Prescribed nitrate therapy and exercise guidance', 'Patient instructed on symptom tracking and emergency warning signs.', '2026-03-13 16:20:00');

INSERT INTO users (user_id, username, password, role, linked_id) VALUES
(1, 'admin1', 'admin123', 'admin', NULL),
(2, 'acarter', 'doctor123', 'doctor', 1),
(3, 'dshah', 'doctor123', 'doctor', 2),
(4, 'obennett', 'patient123', 'patient', 1),
(5, 'ecollins', 'patient123', 'patient', 2),
(6, 'sturner', 'patient123', 'patient', 3),
(7, 'lfoster', 'patient123', 'patient', 4);
