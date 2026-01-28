from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from datetime import datetime
import sqlite3

routes = Blueprint("routes", __name__)

DATABASE = "db/medical.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- MEDICAL RECORDS (HOSPITAL) --------------------

@routes.route("/hospital/medical/add", methods=["POST"])
@jwt_required()
def add_medical_record():
    user = get_jwt_identity()
    if user["role"] != "hospital":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO medical_records
    (patient_id, diagnosis, treatment, doctor, hospital, date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["patient_id"],
        data["diagnosis"],
        data["treatment"],
        data["doctor"],
        user["name"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    return jsonify({"message": "Medical record added"})


@routes.route("/hospital/medical/delete/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_medical_record(record_id):
    user = get_jwt_identity()
    if user["role"] != "hospital":
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM medical_records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Medical record deleted"})


# -------------------- INSURANCE RECORDS --------------------

@routes.route("/insurance/update", methods=["POST"])
@jwt_required()
def update_insurance():
    user = get_jwt_identity()
    if user["role"] != "insurance":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO insurance_records
    (patient_id, company, policy_no, claims, target_balance)
    VALUES (?, ?, ?, ?, ?)
    """, (
        data["patient_id"],
        user["company"],
        data["policy_no"],
        data["claims"],
        data["target_balance"]
    ))

    conn.commit()
    conn.close()
    return jsonify({"message": "Insurance data updated"})


# -------------------- PATIENT VIEW (READ ONLY) --------------------

@routes.route("/patient/view/<patient_id>", methods=["GET"])
@jwt_required()
def patient_view(patient_id):
    user = get_jwt_identity()
    if user["role"] not in ["patient", "hospital", "insurance"]:
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM medical_records WHERE patient_id=?", (patient_id,))
    medical = [dict(row) for row in cur.fetchall()]

    cur.execute("SELECT * FROM insurance_records WHERE patient_id=?", (patient_id,))
    insurance = [dict(row) for row in cur.fetchall()]

    conn.close()

    return jsonify({
        "medical_records": medical,
        "insurance_records": insurance
    })
