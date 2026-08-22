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

    elif role == "Patient":
        query = """
            SELECT u.User_ID, u.Name, u.Email, u.Phone, p.DOB, p.Gender 
            FROM User u 
            JOIN Patient p ON u.User_ID = p.Patient_ID 
            WHERE u.User_ID = %s
        """
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()

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

    return render_template("dashboard.html", user=user_data, schedules=schedules, doctors=doctors, medicines=medicines)

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
