USE hospital_db;

-- 1. Insert Base Users
INSERT INTO User (User_ID, Name, Email, Password, Phone) VALUES
(1, 'System Administrator', 'admin@hospital.com', 'admin123', '01711000001'),
(2, 'Dr. Rafiqul Islam', 'rafiqul@hospital.com', 'doctor123', '01711000002'),
(3, 'Dr. Nusrat Jahan', 'nusrat@hospital.com', 'doctor123', '01711000003'),
(4, 'Dr. Tanvir Ahmed', 'tanvir@hospital.com', 'doctor123', '01711000004'),
(5, 'Abdul Karim', 'abdul@gmail.com', 'patient123', '01811000001'),
(6, 'Farhana Yasmin', 'farhana@gmail.com', 'patient123', '01811000002'),
(7, 'Shakib Al Hasan', 'shakib@gmail.com', 'patient123', '01811000003');

-- 2. Insert Roles
INSERT INTO Admin (Admin_ID) VALUES (1);

INSERT INTO Doctor (Doctor_ID, Specialization) VALUES
(2, 'Cardiology'),
(3, 'Dermatology'),
(4, 'Pediatrics');

INSERT INTO Patient (Patient_ID, DOB, Gender) VALUES
(5, '1988-04-15', 'Male'),
(6, '1995-09-22', 'Female'),
(7, '1992-01-10', 'Male');

-- 3. Insert Doctor Schedules
INSERT INTO Schedule (Schedule_ID, Day, Start_Time, End_Time, Admin_ID, Doctor_ID) VALUES
(1, 'Sunday', '09:00:00', '13:00:00', 1, 2),
(2, 'Monday', '10:00:00', '14:00:00', 1, 3),
(3, 'Tuesday', '14:00:00', '18:00:00', 1, 4),
(4, 'Wednesday', '09:00:00', '13:00:00', 1, 2),
(5, 'Thursday', '11:00:00', '15:00:00', 1, 3);

-- 4. Insert Medicines Inventory
INSERT INTO Medicine (Medicine_ID, Name, Price, Stock) VALUES
(1, 'Napa 500mg', 1.20, 500),
(2, 'Seclo 20mg', 6.00, 300),
(3, 'Ace Plus', 2.50, 400),
(4, 'Histacin', 0.50, 250),
(5, 'Antacid Plus', 2.00, 350),
(6, 'Flexi 50mg', 5.00, 200);
