# System Skeleton: Hospital Management System

> **Last Updated**: 2026-08-21  
> **Course**: CSE370 Database Systems  
> **Status**: Database Architecture & Relational Design Finalized  

---

## 1. Architectural Overview & System Modules

The Hospital Management System is a relational database-backed application structured around 3 primary user roles and 4 core clinical/operational domains:

1. **User Identity & Access Control**: Subclass specialization (`Admin`, `Doctor`, `Patient`) inheriting from superclass `User`.
2. **Duty Scheduling & Appointments**: Slot allocation by `Admin` for `Doctor`, and `Patient` appointment reservations against active schedules.
3. **Clinical Records & Diagnostics**: `Medical_History` tracking, `Prescription` authoring, and `Lab_Test` orders.
4. **Pharmacy & Invoicing**: `Medicine` inventory management, $M:N$ `Prescription_Medicine` fulfillment, and `Bill` generation with multi-method `Payment` processing.

---

## 2. Diagram & Design Artifacts

* **EER Diagram (Chen Notation)**: [`Hospital management system EER .drawio`](file:///c:/University/CSE370/Hospital%20management%20system%20EER%20.drawio)
* **Relational Schema Diagram**: [`Hospital Management System - Relational Schema.drawio`](file:///c:/University/CSE370/Hospital%20Management%20System%20-%20Relational%20Schema.drawio)

---

## 3. Relational Database Schema (3NF Specification)

### 3.1. Authentication & Role Inheritance (Class Table Inheritance)

#### `User`
* Base entity for all platform actors.
```sql
CREATE TABLE User (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Phone VARCHAR(20) NOT NULL
);
```

#### `Admin`
* Administrative accounts for managing schedules and viewing revenue reports.
```sql
CREATE TABLE Admin (
    Admin_ID INT PRIMARY KEY,
    FOREIGN KEY (Admin_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);
```

#### `Doctor`
* Healthcare providers conducting appointments and issuing prescriptions/lab tests.
```sql
CREATE TABLE Doctor (
    Doctor_ID INT PRIMARY KEY,
    Specialization VARCHAR(100) NOT NULL,
    FOREIGN KEY (Doctor_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);
```

#### `Patient`
* Patients booking consultations and receiving clinical records.
```sql
CREATE TABLE Patient (
    Patient_ID INT PRIMARY KEY,
    DOB DATE NOT NULL,
    Gender ENUM('Male', 'Female', 'Other') NOT NULL,
    FOREIGN KEY (Patient_ID) REFERENCES User(User_ID) ON DELETE CASCADE
);
```

---

### 3.2. Scheduling & Appointments

#### `Schedule`
* Doctor duty time blocks created and maintained by Admins.
```sql
CREATE TABLE Schedule (
    Schedule_ID INT AUTO_INCREMENT PRIMARY KEY,
    Day VARCHAR(20) NOT NULL,
    Start_Time TIME NOT NULL,
    End_Time TIME NOT NULL,
    Admin_ID INT NOT NULL,
    Doctor_ID INT NOT NULL,
    FOREIGN KEY (Admin_ID) REFERENCES Admin(Admin_ID),
    FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID)
);
```

#### `Appointment`
* Booked patient-doctor consultations linked to active schedules.
```sql
CREATE TABLE Appointment (
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
```

---

### 3.3. Clinical Records & Diagnostics

#### `Medical_History`
* Historical clinical diagnoses and treatments per patient.
```sql
CREATE TABLE Medical_History (
    Record_ID INT AUTO_INCREMENT PRIMARY KEY,
    Diagnosis TEXT NOT NULL,
    Treatment TEXT NOT NULL,
    Date DATE NOT NULL,
    Patient_ID INT NOT NULL,
    Doctor_ID INT NOT NULL,
    FOREIGN KEY (Patient_ID) REFERENCES Patient(Patient_ID),
    FOREIGN KEY (Doctor_ID) REFERENCES Doctor(Doctor_ID)
);
```

#### `Lab_Test`
* Diagnostic tests ordered by doctors and undertaken by patients.
```sql
CREATE TABLE Lab_Test (
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
```

#### `Prescription`
* Medication prescriptions resulting from appointments ($1:1$).
```sql
CREATE TABLE Prescription (
    Prescription_ID INT AUTO_INCREMENT PRIMARY KEY,
    Date DATE NOT NULL,
    Appointment_ID INT UNIQUE NOT NULL,
    FOREIGN KEY (Appointment_ID) REFERENCES Appointment(Appointment_ID) ON DELETE CASCADE
);
```

---

### 3.4. Pharmacy & Medication Inventory

#### `Medicine`
* Hospital pharmacy inventory and catalog.
```sql
CREATE TABLE Medicine (
    Medicine_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Price DECIMAL(10, 2) NOT NULL,
    Stock INT NOT NULL DEFAULT 0
);
```

#### `Prescription_Medicine`
* Bridge table resolving $M:N$ relationship between `Prescription` and `Medicine`.
```sql
CREATE TABLE Prescription_Medicine (
    Prescription_ID INT NOT NULL,
    Medicine_ID INT NOT NULL,
    Dosage VARCHAR(50) NOT NULL,
    Frequency VARCHAR(50) NOT NULL,
    PRIMARY KEY (Prescription_ID, Medicine_ID),
    FOREIGN KEY (Prescription_ID) REFERENCES Prescription(Prescription_ID) ON DELETE CASCADE,
    FOREIGN KEY (Medicine_ID) REFERENCES Medicine(Medicine_ID)
);
```

---

### 3.5. Financials & Billing

#### `Bill`
* Invoice generated per appointment ($1:1$).
```sql
CREATE TABLE Bill (
    Bill_ID INT AUTO_INCREMENT PRIMARY KEY,
    Bill_Date DATE NOT NULL,
    Total_Amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    Appointment_ID INT UNIQUE NOT NULL,
    FOREIGN KEY (Appointment_ID) REFERENCES Appointment(Appointment_ID) ON DELETE CASCADE
);
```

#### `Payment`
* Transaction records against bills ($1:N$).
```sql
CREATE TABLE Payment (
    Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Amount DECIMAL(10, 2) NOT NULL,
    Payment_Date DATE NOT NULL,
    Payment_Method ENUM('Cash', 'Credit Card', 'Debit Card', 'Mobile Banking') NOT NULL,
    Bill_ID INT NOT NULL,
    FOREIGN KEY (Bill_ID) REFERENCES Bill(Bill_ID) ON DELETE CASCADE
);
```

---

## 4. Key Business Rules & Derived Logic

1. **Disjoint Role Constraint `(d)`**: A single `User` record maps to at most one role subclass (`Admin`, `Doctor`, or `Patient`).
2. **Derived Invoicing (`Total_Amount`)**:
   $$\text{Total\_Amount} = \text{Doctor Consultation Fee} + \sum(\text{Prescribed Medicine Prices}) + \sum(\text{Lab Test Costs})$$
3. **Dynamic Revenue Reporting**: Revenue reports for Admins are computed via SQL aggregation (`SUM(Amount)`, `GROUP BY DATE_FORMAT(Payment_Date, '%Y-%m')`) across `Bill` and `Payment` tables and are not stored in a separate table entity.
