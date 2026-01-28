from flask import Flask, request, jsonify
import sqlite3, uuid, os
from cryptography.fernet import Fernet
import qrcode
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager
from routes import routes
from flask import Flask, request, jsonify, render_template

# ---------------- BASIC CONFIG ----------------
app = Flask(__name__)
DATABASE = "db/medical.db"
KEY_FILE = "utils/secret.key"
QR_DIR = "static/qr"
app.config["JWT_SECRET_KEY"] = "change-this-secret"
jwt = JWTManager(app)
app.register_blueprint(routes)

os.makedirs(QR_DIR, exist_ok=True)

# ---------------- LOAD ENCRYPTION KEY ----------------
with open(KEY_FILE, "rb") as f:
    cipher = Fernet(f.read())

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        name TEXT,
        phone TEXT,
        blood_group TEXT,
        emergency_contact TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_name TEXT,
        council_id TEXT UNIQUE,
        email TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS insurance_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS otp_codes (
        phone TEXT,
        otp TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def create_default_admin():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM admins")
    if cur.fetchone() is None:
        cur.execute("""
        INSERT INTO admins (username, password)
        VALUES (?, ?)
        """, (
            "admin",
            generate_password_hash("admin123")
        ))
        conn.commit()
        print("✅ Default admin created (admin / admin123)")

    conn.close()

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return jsonify({"status": "NFC Health ID System Running"})

@app.route("/login/admin", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admins WHERE username=?", (username,))
    admin = cur.fetchone()
    conn.close()

    if admin and check_password_hash(admin["password"], password):
        return jsonify({"message": "Admin login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/register/hospital", methods=["POST"])
def register_hospital():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
        INSERT INTO hospitals (hospital_name, council_id, email, password)
        VALUES (?, ?, ?, ?)
        """, (
            data["hospital_name"],
            data["council_id"],
            data["email"],
            generate_password_hash(data["password"])
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Hospital already registered"}), 400

    conn.close()
    return jsonify({"message": "Hospital registered successfully"})

@app.route("/login/hospital", methods=["POST"])
def hospital_login():
    data = request.json
    council_id = data.get("council_id")
    password = data.get("password")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitals WHERE council_id=?", (council_id,))
    hospital = cur.fetchone()
    conn.close()

    if hospital and check_password_hash(hospital["password"], password):
        return jsonify({
            "message": "Hospital login successful",
            "hospital_name": hospital["hospital_name"]
        })

    return jsonify({"error": "Invalid hospital credentials"}), 401
@app.route("/register/insurance", methods=["POST"])
def register_insurance():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
        INSERT INTO insurance_users (company_name, email, password)
        VALUES (?, ?, ?)
        """, (
            data["company_name"],
            data["email"],
            generate_password_hash(data["password"])
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Insurance company already registered"}), 400

    conn.close()
    return jsonify({"message": "Insurance company registered successfully"})
@app.route("/login/insurance", methods=["POST"])
def insurance_login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM insurance_users WHERE email=?", (email,))
    insurance = cur.fetchone()
    conn.close()

    if insurance and check_password_hash(insurance["password"], password):
        return jsonify({
            "message": "Insurance login successful",
            "company_name": insurance["company_name"]
        })

    return jsonify({"error": "Invalid insurance credentials"}), 401

@app.route("/admin/create_patient", methods=["POST"])
def create_patient():
    data = request.json

    patient_id = str(uuid.uuid4())
    encrypted_id = cipher.encrypt(patient_id.encode()).decode()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        data["name"],
        data["phone"],
        data["blood_group"],
        data["emergency_contact"],
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    url = f"http://127.0.0.1:5000/card/{encrypted_id}"

    qr_img = qrcode.make(url)
    qr_path = f"{QR_DIR}/{patient_id}.png"
    qr_img.save(qr_path)

    return jsonify({
        "message": "Patient created",
        "nfc_url": url,
        "qr": qr_path
    })

@app.route("/card/<encrypted_id>")
def card_entry(encrypted_id):
    try:
        patient_id = cipher.decrypt(encrypted_id.encode()).decode()
        return jsonify({"patient_id": patient_id})
    except:
        return jsonify({"error": "Invalid card"}), 403
from flask_jwt_extended import create_access_token

@app.route("/login/patient", methods=["POST"])
def patient_login():
    data = request.json
    phone = data.get("phone")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE phone=?", (phone,))
    patient = cur.fetchone()
    conn.close()

    if not patient:
        return jsonify({"error": "Patient not found"}), 401

    token = create_access_token(identity={
        "role": "patient",
        "patient_id": patient["patient_id"]
    })

    return jsonify({"token": token})


@app.route("/login/hospital", methods=["POST"])
def hospital_login_jwt():
    data = request.json

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitals WHERE council_id=?", (data["council_id"],))
    hospital = cur.fetchone()
    conn.close()

    if not hospital or not check_password_hash(hospital["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity={
        "role": "hospital",
        "name": hospital["hospital_name"]
    })

    return jsonify({"token": token})


@app.route("/login/insurance_jwt", methods=["POST"])
def insurance_login_jwt():
    data = request.json

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM insurance_users WHERE email=?", (data["email"],))
    ins = cur.fetchone()
    conn.close()

    if not ins or not check_password_hash(ins["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity={
        "role": "insurance",
        "company": ins["company_name"]
    })

    return jsonify({"token": token})
import random
from datetime import timedelta

# -------- SEND OTP --------
@app.route("/login/patient/send_otp", methods=["POST"])
def send_patient_otp():
    data = request.json
    phone = data.get("phone")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM patients WHERE phone=?", (phone,))
    patient = cur.fetchone()

    if not patient:
        conn.close()
        return jsonify({"error": "Patient not found"}), 404

    otp = str(random.randint(100000, 999999))

    cur.execute("DELETE FROM otp_codes WHERE phone=?", (phone,))
    cur.execute("""
        INSERT INTO otp_codes VALUES (?, ?, ?)
    """, (phone, otp, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    # DEV MODE: show OTP in terminal
    print(f"🔐 OTP for {phone}: {otp}")

    return jsonify({"message": "OTP sent"})


# -------- VERIFY OTP --------
@app.route("/login/patient/verify_otp", methods=["POST"])
def verify_patient_otp():
    data = request.json
    phone = data.get("phone")
    otp = data.get("otp")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM otp_codes WHERE phone=? AND otp=?
    """, (phone, otp))
    record = cur.fetchone()

    if not record:
        conn.close()
        return jsonify({"error": "Invalid OTP"}), 401

    cur.execute("SELECT * FROM patients WHERE phone=?", (phone,))
    patient = cur.fetchone()

    cur.execute("DELETE FROM otp_codes WHERE phone=?", (phone,))
    conn.commit()
    conn.close()

    token = create_access_token(
        identity={
            "role": "patient",
            "patient_id": patient["patient_id"]
        },
        expires_delta=timedelta(hours=12)
    )

    return jsonify({"token": token})

# ---------------- CARD CREATION (QR + NFC PAYLOAD) ----------------

@app.route("/admin/register_patient_and_card", methods=["POST"])
def register_patient_and_card():
    data = request.json

    # 1. Create patient ID
    patient_id = str(uuid.uuid4())

    # 2. Encrypt patient ID
    encrypted_id = cipher.encrypt(patient_id.encode()).decode()

    # 3. Store patient in DB
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO patients
        (patient_id, name, phone, blood_group, emergency_contact, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        data["name"],
        data["phone"],
        data["blood_group"],
        data["emergency_contact"],
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    # 4. Create CARD PAYLOAD (single source of truth)
    card_payload = f"http://127.0.0.1:5000/card/{encrypted_id}"

    # 5. Generate QR code
    qr_img = qrcode.make(card_payload)
    qr_path = f"static/qr/{patient_id}.png"
    qr_img.save(qr_path)

    # 6. Return everything frontend / NFC writer needs
    return jsonify({
        "message": "Patient + Card created successfully",
        "patient_id": patient_id,
        "encrypted_id": encrypted_id,
        "card_payload": card_payload,   # THIS goes to NFC
        "qr_image_path": qr_path        # THIS is shown / printed
    })
@app.route("/health")
def health_login():
    return render_template("health_login.html")

@app.route("/management")
def management_login():
    return render_template("management_login.html")
@app.route("/patient/dashboard")
def patient_dashboard():
    return render_template("patient_dashboard.html")
@app.route("/hospital/dashboard")
def hospital_dashboard():
    return render_template("hospital_dashboard.html")
@app.route("/patient/profile")
def patient_profile():
    return render_template("patient_profile.html")
@app.route("/insurance/dashboard")
def insurance_dashboard():
    return render_template("insurance_dashboard.html")
@app.route("/")
def landing():
    return render_template("index.html")

@app.route("/hospital/login")
def hospital_login_page():
    return render_template("hospital_login.html")

@app.route("/insurance/login")
def insurance_login_page():
    return render_template("insurance_login.html")

@app.route("/patient/register")
def patient_register():
    return render_template("health_login.html")
@app.route("/favicon.ico")
def favicon():
    return "", 204

# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    create_default_admin()
    app.run(debug=True)
