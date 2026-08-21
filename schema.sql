-- Database Creation
CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- 1. Base User Table
CREATE TABLE IF NOT EXISTS User (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Phone VARCHAR(20) NOT NULL
);

-- 2. Role Subclasses (Specialization)
CREATE TABLE IF NOT EXISTS Admin (
    Admin_ID INT PRIMARY KEY,
    FOREIGN KEY (Admin_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Doctor (
    Doctor_ID INT PRIMARY KEY,
    Specialization VARCHAR(100) NOT NULL,
    FOREIGN KEY (Doctor_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Patient (
    Patient_ID INT PRIMARY KEY,
    DOB DATE NOT NULL,
    Gender ENUM('Male', 'Female', 'Other') NOT NULL,
    FOREIGN KEY (Patient_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);

-- 3. Duty Schedules
CREATE TABLE IF NOT EXISTS Schedule (
    Schedule_ID INT AUTO_INCREMENT PRIMARY KEY,
    Day VARCHAR(20) NOT NULL,
    Start_Time TIME NOT NULL,
    End_Time TIME NOT NULL,
    Admin_ID INT NOT NULL,
    Doctor_ID INT NOT NULL,
    FOREIGN KEY (Admin_ID) REFERENCES Admin(Admin_ID),
    FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID)
);

-- 4. Appointments
CREATE TABLE IF NOT EXISTS Appointment (
    Appointment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Date DATE NOT NULL,
    Time TIME NOT NULL,
    Status ENUM('Scheduled', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Scheduled',
    Patient_ID INT NOT NULL,
    Doctor_ID INT NOT NULL,
    Schedule_ID INT NOT NULL,
    FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID),
    FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID),
    FOREIGN KEY (Schedule_ID) REFERENCES Schedule(Schedule_ID)
);

-- 5. Medical History
CREATE TABLE IF NOT EXISTS Medical_History (
    Record_ID INT AUTO_INCREMENT PRIMARY KEY,
    Diagnosis TEXT NOT NULL,
    Treatment TEXT NOT NULL,
    Date DATE NOT NULL,
    Patient_ID INT NOT NULL,
    Doctor_ID INT NOT NULL,
    FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID),
    FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID)
);

-- 6. Invoices & Billing
CREATE TABLE IF NOT EXISTS Bill (
    Bill_ID INT AUTO_INCREMENT PRIMARY KEY,
    Bill_Date DATE NOT NULL,
    Total_Amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    Appointment_ID INT UNIQUE NOT NULL,
    FOREIGN KEY (Appointment_ID) REFERENCES Appointment(Appointment_ID) ON DELETE CASCADE
);

-- 7. Lab Tests
CREATE TABLE IF NOT EXISTS Lab_Test (
    Test_ID INT AUTO_INCREMENT PRIMARY KEY,
    Test_Name VARCHAR(100) NOT NULL,
    Test_Cost DECIMAL(10, 2) NOT NULL,
    Status ENUM('Pending', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Pending',
    Result TEXT,
    Patient_ID INT NOT NULL,
    Doctor_ID INT NOT NULL,
    Bill_ID INT,
    FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID),
    FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID),
    FOREIGN KEY (Bill_ID) REFERENCES Bill(Bill_ID) ON DELETE SET NULL
);

-- 8. Prescriptions
CREATE TABLE IF NOT EXISTS Prescription (
    Prescription_ID INT AUTO_INCREMENT PRIMARY KEY,
    Date DATE NOT NULL,
    Appointment_ID INT UNIQUE NOT NULL,
    FOREIGN KEY (Appointment_ID) REFERENCES Appointment(Appointment_ID) ON DELETE CASCADE
);

-- 9. Medicines Inventory
CREATE TABLE IF NOT EXISTS Medicine (
    Medicine_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Price DECIMAL(10, 2) NOT NULL,
    Stock INT NOT NULL DEFAULT 0
);

-- 10. Prescription-Medicine Bridge Table (M:N)
CREATE TABLE IF NOT EXISTS Prescription_Medicine (
    Prescription_ID INT NOT NULL,
    Medicine_ID INT NOT NULL,
    Dosage VARCHAR(50) NOT NULL,
    Frequency VARCHAR(50) NOT NULL,
    PRIMARY KEY (Prescription_ID, Medicine_ID),
    FOREIGN KEY (Prescription_ID) REFERENCES Prescription(Prescription_ID) ON DELETE CASCADE,
    FOREIGN KEY (Medicine_ID) REFERENCES Medicine(Medicine_ID)
);

-- 11. Payments
CREATE TABLE IF NOT EXISTS Payment (
    Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Amount DECIMAL(10, 2) NOT NULL,
    Payment_Date DATE NOT NULL,
    Payment_Method ENUM('Cash', 'Credit Card', 'Debit Card', 'Mobile Banking') NOT NULL,
    Bill_ID INT NOT NULL,
    FOREIGN KEY (Bill_ID) REFERENCES Bill(Bill_ID) ON DELETE CASCADE
);