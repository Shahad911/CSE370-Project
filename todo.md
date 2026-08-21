# Project TODO & Technical Debt Tracker

## Active Tasks
- [ ] Implement backend database setup (MySQL / PostgreSQL / Supabase SQL schema)
- [ ] Create seed data for testing (sample Users, Doctors, Patients, Medicines, Schedules)
- [ ] Implement CRUD endpoints / queries:
  - [ ] Doctor: Update Medical History & Search Patient Records (with filtering)
  - [ ] Admin: Doctor Schedule Management
  - [ ] Patient: Appointment Management (Book, Cancel, View)
  - [ ] Billing & Pharmacy: Prescription creation, Bill Generation, Medicine stock view
  - [ ] Payments & Analytics: Payment recording, Admin Revenue Reports (SQL aggregation)
- [ ] Setup Frontend / UI integration

## Technical Debt & Optimization (Dev)
- [ ] Add indexing on high-traffic query columns (`Appointment.Date`, `Payment.Payment_Date`, `User.Email`)
- [ ] Add check constraints for valid financial amounts (`Total_Amount >= 0`, `Amount > 0`, `Test_Cost >= 0`)
