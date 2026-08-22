from flask import Flask, render_template, request, redirect, url_for, session
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "hospital_management_secret_key"

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    conn = get_db_connection()
    if not conn:
        return render_template("login.html", error="Database connection failed. Ensure MySQL/XAMPP is running.")

    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM User WHERE Email = %s AND Password = %s"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return render_template("login.html", error="Invalid email or password.")

    user_id = user["User_ID"]
    role = None

    cursor.execute("SELECT * FROM Admin WHERE Admin_ID = %s", (user_id,))
    if cursor.fetchone():
        role = "Admin"
    else:
        cursor.execute("SELECT * FROM Doctor WHERE Doctor_ID = %s", (user_id,))
        if cursor.fetchone():
            role = "Doctor"
        else:
            cursor.execute("SELECT * FROM Patient WHERE Patient_ID = %s", (user_id,))
            if cursor.fetchone():
                role = "Patient"

    cursor.close()
    conn.close()

    session["user_id"] = user_id
    session["role"] = role
    session["name"] = user["Name"]

    return redirect(url_for("dashboard"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    phone = request.form.get("phone")
    role = request.form.get("role")

    conn = get_db_connection()
    if not conn:
        return render_template("signup.html", error="Database connection failed.")

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT User_ID FROM User WHERE Email = %s", (email,))
        if cursor.fetchone():
            return render_template("signup.html", error="Email is already registered.")

        insert_user_query = "INSERT INTO User (Name, Email, Password, Phone) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_user_query, (name, email, password, phone))
        user_id = cursor.lastrowid

        if role == "Admin":
            cursor.execute("INSERT INTO Admin (Admin_ID) VALUES (%s)", (user_id,))
        elif role == "Doctor":
            specialization = request.form.get("specialization") or "General Physician"
            cursor.execute("INSERT INTO Doctor (Doctor_ID, Specialization) VALUES (%s, %s)", (user_id, specialization))
        elif role == "Patient":
            dob = request.form.get("dob")
            gender = request.form.get("gender")
            cursor.execute("INSERT INTO Patient (Patient_ID, DOB, Gender) VALUES (%s, %s, %s)", (user_id, dob, gender))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return render_template("signup.html", error=f"Registration failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return render_template("login.html", success="Registration successful! Please log in.")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    role = session.get("role")

    conn = get_db_connection()
    if not conn:
        return "Database connection error.", 500

    cursor = conn.cursor(dictionary=True)

    schedules = []
    doctors = []
    medicines = []
    appointments = []
    patients = []
    medical_histories = []
    prescriptions = []
    lab_tests = []
    bills = []
    patient_search = request.args.get("patient_search", "").strip()
    user_data = None

    if role == "Doctor":
        query = """
            SELECT u.User_ID, u.Name, u.Email, u.Phone, d.Specialization 
            FROM User u 
            JOIN Doctor d ON u.User_ID = d.Doctor_ID 
            WHERE u.User_ID = %s
        """
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()

        cursor.execute("""
            SELECT a.Appointment_ID, a.Date, a.Time, a.Status, a.Patient_ID, u.Name AS Patient_Name, u.Phone AS Patient_Phone,
                   b.Bill_ID, pr.Prescription_ID
            FROM Appointment a 
            JOIN Patient p ON a.Patient_ID = p.Patient_ID 
            JOIN User u ON p.Patient_ID = u.User_ID 
            LEFT JOIN Bill b ON a.Appointment_ID = b.Appointment_ID
            LEFT JOIN Prescription pr ON a.Appointment_ID = pr.Appointment_ID
            WHERE a.Doctor_ID = %s 
            ORDER BY a.Date DESC, a.Time DESC
        """, (user_id,))
        appointments = cursor.fetchall()

        if patient_search:
            search_pattern = f"%{patient_search}%"
            cursor.execute("""
                SELECT p.Patient_ID, u.Name, u.Email, u.Phone, p.DOB, p.Gender 
                FROM Patient p 
                JOIN User u ON p.Patient_ID = u.User_ID 
                WHERE u.Name LIKE %s OR u.Phone LIKE %s 
                ORDER BY u.Name ASC
            """, (search_pattern, search_pattern))
        else:
            cursor.execute("""
                SELECT p.Patient_ID, u.Name, u.Email, u.Phone, p.DOB, p.Gender 
                FROM Patient p 
                JOIN User u ON p.Patient_ID = u.User_ID 
                ORDER BY u.Name ASC
            """)
        patients = cursor.fetchall()

        cursor.execute("""
            SELECT m.Record_ID, m.Diagnosis, m.Treatment, m.Date, u.Name AS Patient_Name, du.Name AS Doctor_Name 
            FROM Medical_History m 
            JOIN Patient p ON m.Patient_ID = p.Patient_ID 
            JOIN User u ON p.Patient_ID = u.User_ID 
            JOIN Doctor d ON m.Doctor_ID = d.Doctor_ID 
            JOIN User du ON d.Doctor_ID = du.User_ID 
            ORDER BY m.Date DESC, m.Record_ID DESC
        """)
        medical_histories = cursor.fetchall()

        cursor.execute("""
            SELECT pr.Prescription_ID, pr.Date, a.Appointment_ID, pu.Name AS Patient_Name, m.Name AS Medicine_Name, pm.Dosage, pm.Frequency, m.Price 
            FROM Prescription pr 
            JOIN Appointment a ON pr.Appointment_ID = a.Appointment_ID 
            JOIN Patient pt ON a.Patient_ID = pt.Patient_ID 
            JOIN User pu ON pt.Patient_ID = pu.User_ID 
            JOIN Prescription_Medicine pm ON pr.Prescription_ID = pm.Prescription_ID 
            JOIN Medicine m ON pm.Medicine_ID = m.Medicine_ID 
            WHERE a.Doctor_ID = %s 
            ORDER BY pr.Date DESC, pr.Prescription_ID DESC
        """, (user_id,))
        prescriptions = cursor.fetchall()

        cursor.execute("""
            SELECT lt.Test_ID, lt.Test_Name, lt.Test_Cost, lt.Status, lt.Result, u.Name AS Patient_Name 
            FROM Lab_Test lt 
            JOIN Patient p ON lt.Patient_ID = p.Patient_ID 
            JOIN User u ON p.Patient_ID = u.User_ID 
            WHERE lt.Doctor_ID = %s 
            ORDER BY lt.Test_ID DESC
        """, (user_id,))
        lab_tests = cursor.fetchall()

        cursor.execute("""
            SELECT b.Bill_ID, b.Bill_Date, b.Total_Amount, b.Appointment_ID, u.Name AS Patient_Name 
            FROM Bill b 
            JOIN Appointment a ON b.Appointment_ID = a.Appointment_ID 
            JOIN Patient p ON a.Patient_ID = p.Patient_ID 
            JOIN User u ON p.Patient_ID = u.User_ID 
            WHERE a.Doctor_ID = %s 
            ORDER BY b.Bill_ID DESC
        """, (user_id,))
        bills = cursor.fetchall()

        cursor.execute("SELECT * FROM Medicine ORDER BY Name ASC")
        medicines = cursor.fetchall()

    elif role == "Patient":
        query = """
            SELECT u.User_ID, u.Name, u.Email, u.Phone, p.DOB, p.Gender 
            FROM User u 
            JOIN Patient p ON u.User_ID = p.Patient_ID 
            WHERE u.User_ID = %s
        """
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()

        cursor.execute("""
            SELECT s.Schedule_ID, s.Day, s.Start_Time, s.End_Time, s.Doctor_ID, u.Name AS Doctor_Name, d.Specialization 
            FROM Schedule s 
            JOIN Doctor d ON s.Doctor_ID = d.Doctor_ID 
            JOIN User u ON d.Doctor_ID = u.User_ID 
            ORDER BY FIELD(s.Day, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
        """)
        schedules = cursor.fetchall()

        cursor.execute("""
            SELECT a.Appointment_ID, a.Date, a.Time, a.Status, u.Name AS Doctor_Name, d.Specialization 
            FROM Appointment a 
            JOIN Doctor d ON a.Doctor_ID = d.Doctor_ID 
            JOIN User u ON d.Doctor_ID = u.User_ID 
            WHERE a.Patient_ID = %s 
            ORDER BY a.Date DESC, a.Time DESC
        """, (user_id,))
        appointments = cursor.fetchall()

        cursor.execute("""
            SELECT pr.Prescription_ID, pr.Date, du.Name AS Doctor_Name, d.Specialization, m.Name AS Medicine_Name, pm.Dosage, pm.Frequency 
            FROM Prescription pr 
            JOIN Appointment a ON pr.Appointment_ID = a.Appointment_ID 
            JOIN Doctor d ON a.Doctor_ID = d.Doctor_ID 
            JOIN User du ON d.Doctor_ID = du.User_ID 
            JOIN Prescription_Medicine pm ON pr.Prescription_ID = pm.Prescription_ID 
            JOIN Medicine m ON pm.Medicine_ID = m.Medicine_ID 
            WHERE a.Patient_ID = %s 
            ORDER BY pr.Date DESC
        """, (user_id,))
        prescriptions = cursor.fetchall()

        cursor.execute("""
            SELECT lt.Test_ID, lt.Test_Name, lt.Test_Cost, lt.Status, lt.Result, du.Name AS Doctor_Name 
            FROM Lab_Test lt 
            JOIN Doctor d ON lt.Doctor_ID = d.Doctor_ID 
            JOIN User du ON d.Doctor_ID = du.User_ID 
            WHERE lt.Patient_ID = %s 
            ORDER BY lt.Test_ID DESC
        """, (user_id,))
        lab_tests = cursor.fetchall()

        cursor.execute("""
            SELECT b.Bill_ID, b.Bill_Date, b.Total_Amount, b.Appointment_ID, COALESCE(SUM(py.Amount), 0) AS Paid_Amount 
            FROM Bill b 
            JOIN Appointment a ON b.Appointment_ID = a.Appointment_ID 
            LEFT JOIN Payment py ON b.Bill_ID = py.Bill_ID 
            WHERE a.Patient_ID = %s 
            GROUP BY b.Bill_ID, b.Bill_Date, b.Total_Amount, b.Appointment_ID 
            ORDER BY b.Bill_ID DESC
        """, (user_id,))
        bills = cursor.fetchall()

    else:  # Admin
        query = "SELECT User_ID, Name, Email, Phone FROM User WHERE User_ID = %s"
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()

        cursor.execute("""
            SELECT s.Schedule_ID, s.Day, s.Start_Time, s.End_Time, u.Name AS Doctor_Name, d.Specialization 
            FROM Schedule s 
            JOIN Doctor d ON s.Doctor_ID = d.Doctor_ID 
            JOIN User u ON d.Doctor_ID = u.User_ID 
            ORDER BY FIELD(s.Day, 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
        """)
        schedules = cursor.fetchall()

        cursor.execute("""
            SELECT d.Doctor_ID, u.Name, d.Specialization 
            FROM Doctor d 
            JOIN User u ON d.Doctor_ID = u.User_ID
        """)
        doctors = cursor.fetchall()

        cursor.execute("SELECT * FROM Medicine ORDER BY Name ASC")
        medicines = cursor.fetchall()

    if user_data:
        user_data["Role"] = role

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        user=user_data,
        schedules=schedules,
        doctors=doctors,
        medicines=medicines,
        appointments=appointments,
        patients=patients,
        medical_histories=medical_histories,
        prescriptions=prescriptions,
        lab_tests=lab_tests,
        bills=bills,
        patient_search=patient_search
    )

@app.route("/admin/schedule/add", methods=["POST"])
def admin_add_schedule():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    admin_id = session.get("user_id")
    doctor_id = request.form.get("doctor_id")
    day = request.form.get("day")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO Schedule (Day, Start_Time, End_Time, Admin_ID, Doctor_ID) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (day, start_time, end_time, admin_id, doctor_id))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/admin/schedule/delete/<int:schedule_id>", methods=["POST"])
def admin_delete_schedule(schedule_id):
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Schedule WHERE Schedule_ID = %s", (schedule_id,))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/admin/medicine/add", methods=["POST"])
def admin_add_medicine():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    name = request.form.get("name")
    price = request.form.get("price")
    stock = request.form.get("stock")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO Medicine (Name, Price, Stock) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, price, stock))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/admin/medicine/update", methods=["POST"])
def admin_update_medicine():
    if session.get("role") != "Admin":
        return redirect(url_for("login"))

    medicine_id = request.form.get("medicine_id")
    price = request.form.get("price")
    stock = request.form.get("stock")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "UPDATE Medicine SET Price = %s, Stock = %s WHERE Medicine_ID = %s"
        cursor.execute(query, (price, stock, medicine_id))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/patient/appointment/book", methods=["POST"])
def patient_book_appointment():
    if session.get("role") != "Patient":
        return redirect(url_for("login"))

    patient_id = session.get("user_id")
    schedule_id = request.form.get("schedule_id")
    date = request.form.get("date")
    time = request.form.get("time")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT Doctor_ID FROM Schedule WHERE Schedule_ID = %s", (schedule_id,))
        sched = cursor.fetchone()

        if sched:
            doctor_id = sched["Doctor_ID"]
            query = """
                INSERT INTO Appointment (Date, Time, Status, Patient_ID, Doctor_ID, Schedule_ID) 
                VALUES (%s, %s, 'Scheduled', %s, %s, %s)
            """
            cursor.execute(query, (date, time, patient_id, doctor_id, schedule_id))
            conn.commit()

        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/patient/appointment/cancel/<int:appointment_id>", methods=["POST"])
def patient_cancel_appointment(appointment_id):
    if session.get("role") != "Patient":
        return redirect(url_for("login"))

    patient_id = session.get("user_id")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "UPDATE Appointment SET Status = 'Cancelled' WHERE Appointment_ID = %s AND Patient_ID = %s"
        cursor.execute(query, (appointment_id, patient_id))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/doctor/medical-history/add", methods=["POST"])
def doctor_add_medical_history():
    if session.get("role") != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session.get("user_id")
    patient_id = request.form.get("patient_id")
    diagnosis = request.form.get("diagnosis")
    treatment = request.form.get("treatment")
    date = request.form.get("date")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
            INSERT INTO Medical_History (Diagnosis, Treatment, Date, Patient_ID, Doctor_ID) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (diagnosis, treatment, date, patient_id, doctor_id))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/doctor/appointment/complete/<int:appointment_id>", methods=["POST"])
def doctor_complete_appointment(appointment_id):
    if session.get("role") != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session.get("user_id")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "UPDATE Appointment SET Status = 'Completed' WHERE Appointment_ID = %s AND Doctor_ID = %s"
        cursor.execute(query, (appointment_id, doctor_id))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/doctor/prescription/create", methods=["POST"])
def doctor_create_prescription():
    if session.get("role") != "Doctor":
        return redirect(url_for("login"))

    appointment_id = request.form.get("appointment_id")
    date = request.form.get("date")
    medicine_id = request.form.get("medicine_id")
    dosage = request.form.get("dosage")
    frequency = request.form.get("frequency")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Prescription (Date, Appointment_ID) VALUES (%s, %s)", (date, appointment_id))
        prescription_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO Prescription_Medicine (Prescription_ID, Medicine_ID, Dosage, Frequency) 
            VALUES (%s, %s, %s, %s)
        """, (prescription_id, medicine_id, dosage, frequency))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/doctor/lab-test/order", methods=["POST"])
def doctor_order_lab_test():
    if session.get("role") != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session.get("user_id")
    patient_id = request.form.get("patient_id")
    test_name = request.form.get("test_name")
    test_cost = request.form.get("test_cost")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = """
            INSERT INTO Lab_Test (Test_Name, Test_Cost, Status, Result, Patient_ID, Doctor_ID, Bill_ID) 
            VALUES (%s, %s, 'Pending', NULL, %s, %s, NULL)
        """
        cursor.execute(query, (test_name, test_cost, patient_id, doctor_id))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/doctor/lab-test/update", methods=["POST"])
def doctor_update_lab_test():
    if session.get("role") != "Doctor":
        return redirect(url_for("login"))

    test_id = request.form.get("test_id")
    result = request.form.get("result")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "UPDATE Lab_Test SET Result = %s, Status = 'Completed' WHERE Test_ID = %s"
        cursor.execute(query, (result, test_id))
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/doctor/bill/generate", methods=["POST"])
def doctor_generate_bill():
    if session.get("role") != "Doctor":
        return redirect(url_for("login"))

    appointment_id = request.form.get("appointment_id")
    bill_date = request.form.get("bill_date")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        total_amount = 500.00  # Base Consultation Fee

        cursor.execute("""
            SELECT SUM(m.Price) AS med_total 
            FROM Prescription pr 
            JOIN Prescription_Medicine pm ON pr.Prescription_ID = pm.Prescription_ID 
            JOIN Medicine m ON pm.Medicine_ID = m.Medicine_ID 
            WHERE pr.Appointment_ID = %s
        """, (appointment_id,))
        med_row = cursor.fetchone()
        if med_row and med_row["med_total"]:
            total_amount += float(med_row["med_total"])

        cursor.execute("SELECT Patient_ID, Doctor_ID FROM Appointment WHERE Appointment_ID = %s", (appointment_id,))
        appt = cursor.fetchone()
        if appt:
            patient_id = appt["Patient_ID"]
            doctor_id = appt["Doctor_ID"]

            cursor.execute("""
                SELECT Test_ID, Test_Cost 
                FROM Lab_Test 
                WHERE Patient_ID = %s AND Doctor_ID = %s AND Bill_ID IS NULL
            """, (patient_id, doctor_id))
            tests = cursor.fetchall()
            for t in tests:
                total_amount += float(t["Test_Cost"])

            cursor.execute("""
                INSERT INTO Bill (Bill_Date, Total_Amount, Appointment_ID) 
                VALUES (%s, %s, %s)
            """, (bill_date, total_amount, appointment_id))
            bill_id = cursor.lastrowid

            for t in tests:
                cursor.execute("UPDATE Lab_Test SET Bill_ID = %s WHERE Test_ID = %s", (bill_id, t["Test_ID"]))

        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
