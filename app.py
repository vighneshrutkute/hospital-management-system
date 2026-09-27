from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import psycopg2.extras
import os
from datetime import date
from decimal import Decimal, InvalidOperation

app = Flask(__name__)
app.secret_key = 'hospital_secret_key'

# ─── DB CONNECTION ───────────────────────────────────────────http://127.0.0.1:5000/
def get_db():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        host="localhost",
        port=5432,
        user="vighneshashokrutkute",
        password="sql@123",
        dbname="hospital"
    )

def get_cursor(db, dict_cursor=False):
    if dict_cursor:
        return db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return db.cursor()

def form_value(name, default=None):
    value = request.form.get(name)
    if value is None:
        return default
    value = value.strip()
    return value if value != "" else default

def money_value(name):
    raw = form_value(name, "0")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid amount for {name}: {raw}")

# ─── HOME ────────────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COUNT(*) AS cnt FROM PATIENT")
    patients = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM DOCTOR")
    doctors = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM APPOINTMENT")
    appointments = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM ROOM WHERE status='Available'")
    rooms = cur.fetchone()['cnt']
    db.close()
    return render_template('index.html', patients=patients, doctors=doctors,
                           appointments=appointments, rooms=rooms)

# ══════════════════════════════════════════════════════════════
#  PATIENTS
# ══════════════════════════════════════════════════════════════
@app.route('/patients')
def patients():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM PATIENT ORDER BY patient_id DESC")
    data = cur.fetchall()
    db.close()
    return render_template('patients.html', patients=data)

@app.route('/patients/add', methods=['GET','POST'])
def add_patient():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""INSERT INTO PATIENT
            (first_name,middle_name,last_name,dob,gender,blood_group,phone_no,address,reg_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (request.form['first_name'], form_value('middle_name'),
             request.form['last_name'],  request.form['dob'],
             request.form['gender'],     form_value('blood_group'),
             form_value('phone_no'),   form_value('address'),
             date.today()))
            db.commit()
            flash('Patient added successfully!', 'success')
        except (psycopg2.Error, ValueError) as e:
            db.rollback()
            flash(f'Could not add patient: {getattr(e, "pgerror", None) or e}', 'danger')
        finally:
            cur.close(); db.close()
        return redirect(url_for('patients'))
    return render_template('add_patient.html')

@app.route('/patients/edit/<int:pid>', methods=['GET','POST'])
def edit_patient(pid):
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        cur.execute("""UPDATE PATIENT SET first_name=%s,middle_name=%s,last_name=%s,
            dob=%s,gender=%s,blood_group=%s,phone_no=%s,address=%s WHERE patient_id=%s""",
            (request.form['first_name'], form_value('middle_name'),
             request.form['last_name'],  request.form['dob'],
             request.form['gender'],     form_value('blood_group'),
             form_value('phone_no'),   form_value('address'), pid))
        db.commit(); db.close()
        flash('Patient updated!', 'success')
        return redirect(url_for('patients'))
    cur.execute("SELECT * FROM PATIENT WHERE patient_id=%s", (pid,))
    patient = cur.fetchone(); db.close()
    return render_template('edit_patient.html', patient=patient)

@app.route('/patients/delete/<int:pid>')
def delete_patient(pid):
    db = get_db()
    cur = db.cursor()
    try:
        # Remove records that depend on the patient first.
        cur.execute("""DELETE FROM PRESCRIPTION_MEDICINE
                       WHERE prescription_id IN (
                           SELECT pr.prescription_id
                           FROM PRESCRIPTION pr
                           JOIN TREATMENT t ON pr.treatment_id=t.treatment_id
                           WHERE t.patient_id=%s
                       )""", (pid,))
        cur.execute("""DELETE FROM PRESCRIPTION
                       WHERE treatment_id IN (SELECT treatment_id FROM TREATMENT WHERE patient_id=%s)""", (pid,))
        cur.execute("DELETE FROM TREATMENT WHERE patient_id=%s", (pid,))
        cur.execute("DELETE FROM APPOINTMENT WHERE patient_id=%s", (pid,))

        # Free rooms before removing their allocation records.
        cur.execute("SELECT room_no FROM ROOM_ALLOCATED WHERE patient_id=%s", (pid,))
        allocated_rooms = [row[0] for row in cur.fetchall()]
        cur.execute("DELETE FROM ROOM_ALLOCATED WHERE patient_id=%s", (pid,))
        for room_no in allocated_rooms:
            cur.execute("UPDATE ROOM SET status='Available' WHERE room_no=%s", (room_no,))

        cur.execute("DELETE FROM BILL WHERE patient_id=%s", (pid,))
        cur.execute("DELETE FROM PATIENT WHERE patient_id=%s", (pid,))
        db.commit()
        flash('Patient and related records deleted.', 'info')
    except psycopg2.Error as e:
        db.rollback()
        flash(f'Could not delete patient: {e.pgerror or e}', 'danger')
    finally:
        cur.close(); db.close()
    return redirect(url_for('patients'))

# ══════════════════════════════════════════════════════════════
#  DOCTORS
# ══════════════════════════════════════════════════════════════
@app.route('/doctors')
def doctors():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT D.*, DEP.dept_name FROM DOCTOR D
                   LEFT JOIN DEPARTMENT DEP ON D.dept_id=DEP.dept_id
                   ORDER BY D.doctor_id DESC""")
    data = cur.fetchall(); db.close()
    return render_template('doctors.html', doctors=data)

@app.route('/doctors/add', methods=['GET','POST'])
def add_doctor():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        cur.execute("""INSERT INTO DOCTOR
            (dname,specialization,qualification,phone_no,consultation_fee,joining_date,dept_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (request.form['dname'],          form_value('specialization'),
             form_value('qualification'),  form_value('phone_no'),
             money_value('consultation_fee'),form_value('joining_date'),
             form_value('dept_id')))
        db.commit(); db.close()
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('doctors'))
    cur.execute("SELECT * FROM DEPARTMENT")
    depts = cur.fetchall(); db.close()
    return render_template('add_doctor.html', depts=depts)

@app.route('/doctors/edit/<int:did>', methods=['GET','POST'])
def edit_doctor(did):
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        cur.execute("""UPDATE DOCTOR SET dname=%s,specialization=%s,qualification=%s,
            phone_no=%s,consultation_fee=%s,joining_date=%s,dept_id=%s WHERE doctor_id=%s""",
            (request.form['dname'],          form_value('specialization'),
             form_value('qualification'),  form_value('phone_no'),
             money_value('consultation_fee'),form_value('joining_date'),
             form_value('dept_id'), did))
        db.commit(); db.close()
        flash('Doctor updated!', 'success')
        return redirect(url_for('doctors'))
    cur.execute("SELECT * FROM DOCTOR WHERE doctor_id=%s", (did,))
    doctor = cur.fetchone()
    cur.execute("SELECT * FROM DEPARTMENT")
    depts = cur.fetchall(); db.close()
    return render_template('edit_doctor.html', doctor=doctor, depts=depts)

@app.route('/doctors/delete/<int:did>')
def delete_doctor(did):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""DELETE FROM PRESCRIPTION_MEDICINE
                       WHERE prescription_id IN (
                           SELECT pr.prescription_id
                           FROM PRESCRIPTION pr
                           JOIN TREATMENT t ON pr.treatment_id=t.treatment_id
                           WHERE t.doctor_id=%s
                       )""", (did,))
        cur.execute("""DELETE FROM PRESCRIPTION
                       WHERE treatment_id IN (SELECT treatment_id FROM TREATMENT WHERE doctor_id=%s)""", (did,))
        cur.execute("DELETE FROM TREATMENT WHERE doctor_id=%s", (did,))
        cur.execute("DELETE FROM APPOINTMENT WHERE doctor_id=%s", (did,))
        cur.execute("DELETE FROM DOCTOR WHERE doctor_id=%s", (did,))
        db.commit()
        flash('Doctor and related records deleted.', 'info')
    except psycopg2.Error as e:
        db.rollback()
        flash(f'Could not delete doctor: {e.pgerror or e}', 'danger')
    finally:
        cur.close(); db.close()
    return redirect(url_for('doctors'))

# ══════════════════════════════════════════════════════════════
#  DEPARTMENTS
# ══════════════════════════════════════════════════════════════
@app.route('/departments')
def departments():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM DEPARTMENT ORDER BY dept_id")
    data = cur.fetchall(); db.close()
    return render_template('departments.html', departments=data)

@app.route('/departments/add', methods=['GET','POST'])
def add_department():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO DEPARTMENT (dept_name,dept_location) VALUES (%s,%s)",
                    (request.form['dept_name'], request.form['dept_location']))
        db.commit(); db.close()
        flash('Department added!', 'success')
        return redirect(url_for('departments'))
    return render_template('add_departments.html')

@app.route('/departments/delete/<int:did>')
def delete_department(did):
    db = get_db()
    cur = db.cursor()
    try:
        # Do not silently delete doctors. A department can be deleted only
        # after its doctors have been reassigned or deleted.
        cur.execute("SELECT COUNT(*) FROM DOCTOR WHERE dept_id=%s", (did,))
        doctor_count = cur.fetchone()[0]
        if doctor_count:
            flash(f'Cannot delete department: {doctor_count} doctor(s) still belong to it. Reassign or delete them first.', 'danger')
        else:
            cur.execute("DELETE FROM DEPARTMENT WHERE dept_id=%s", (did,))
            db.commit()
            flash('Department deleted.', 'info')
    except psycopg2.Error as e:
        db.rollback()
        flash(f'Could not delete department: {e.pgerror or e}', 'danger')
    finally:
        cur.close(); db.close()
    return redirect(url_for('departments'))

# ══════════════════════════════════════════════════════════════
#  APPOINTMENTS
# ══════════════════════════════════════════════════════════════
@app.route('/appointments')
def appointments():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT A.*,
        CONCAT(P.first_name,' ',P.last_name) AS patient_name,
        D.dname AS doctor_name
        FROM APPOINTMENT A
        JOIN PATIENT P ON A.patient_id=P.patient_id
        JOIN DOCTOR D ON A.doctor_id=D.doctor_id
        ORDER BY A.appointment_date DESC""")
    data = cur.fetchall(); db.close()
    return render_template('appointments.html', appointments=data)

@app.route('/appointments/add', methods=['GET','POST'])
def add_appointment():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        cur.execute("""INSERT INTO APPOINTMENT
            (patient_id,doctor_id,appointment_date,appointment_time,
             consultation_mode,reason,booking_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (request.form['patient_id'],      request.form['doctor_id'],
             request.form['appointment_date'],form_value('appointment_time'),
             form_value('consultation_mode'),form_value('reason'),
             date.today()))
        db.commit(); db.close()
        flash('Appointment booked!', 'success')
        return redirect(url_for('appointments'))
    cur.execute("SELECT patient_id, CONCAT(first_name,' ',last_name) AS name FROM PATIENT")
    patients = cur.fetchall()
    cur.execute("SELECT doctor_id, dname FROM DOCTOR")
    docs = cur.fetchall(); db.close()
    return render_template('add_appointment.html', patients=patients, doctors=docs)

@app.route('/appointments/delete/<int:aid>')
def delete_appointment(aid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM APPOINTMENT WHERE appointment_id=%s", (aid,))
    db.commit(); db.close()
    flash('Appointment deleted.', 'info')
    return redirect(url_for('appointments'))

# ══════════════════════════════════════════════════════════════
#  TREATMENTS
# ══════════════════════════════════════════════════════════════
@app.route('/treatments')
def treatments():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT T.*,
        CONCAT(P.first_name,' ',P.last_name) AS patient_name,
        D.dname AS doctor_name
        FROM TREATMENT T
        JOIN PATIENT P ON T.patient_id=P.patient_id
        JOIN DOCTOR D ON T.doctor_id=D.doctor_id
        ORDER BY T.treatment_date DESC""")
    data = cur.fetchall(); db.close()
    return render_template('treatments.html', treatments=data)

@app.route('/treatments/add', methods=['GET','POST'])
def add_treatment():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        cur.execute("""INSERT INTO TREATMENT
            (patient_id,doctor_id,diagnosis,status,treatment_date,treatment_desc)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (request.form['patient_id'],    request.form['doctor_id'],
             form_value('diagnosis'),     form_value('status'),
             request.form['treatment_date'],form_value('treatment_desc')))
        db.commit(); db.close()
        flash('Treatment recorded!', 'success')
        return redirect(url_for('treatments'))
    cur.execute("SELECT patient_id, CONCAT(first_name,' ',last_name) AS name FROM PATIENT")
    patients = cur.fetchall()
    cur.execute("SELECT doctor_id, dname FROM DOCTOR")
    docs = cur.fetchall(); db.close()
    return render_template('add_treatment.html', patients=patients, doctors=docs)

@app.route('/treatments/delete/<int:tid>')
def delete_treatment(tid):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""DELETE FROM PRESCRIPTION_MEDICINE
                       WHERE prescription_id IN (SELECT prescription_id FROM PRESCRIPTION WHERE treatment_id=%s)""", (tid,))
        cur.execute("DELETE FROM PRESCRIPTION WHERE treatment_id=%s", (tid,))
        cur.execute("DELETE FROM TREATMENT WHERE treatment_id=%s", (tid,))
        db.commit()
        flash('Treatment and related prescription records deleted.', 'info')
    except psycopg2.Error as e:
        db.rollback()
        flash(f'Could not delete treatment: {e.pgerror or e}', 'danger')
    finally:
        cur.close(); db.close()
    return redirect(url_for('treatments'))

# ══════════════════════════════════════════════════════════════
#  PRESCRIPTIONS
# ══════════════════════════════════════════════════════════════
@app.route('/prescriptions')
def prescriptions():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT PR.*,
        CONCAT(P.first_name,' ',P.last_name) AS patient_name,
        D.dname AS doctor_name,
        T.diagnosis
        FROM PRESCRIPTION PR
        JOIN TREATMENT T ON PR.treatment_id=T.treatment_id
        JOIN PATIENT P ON T.patient_id=P.patient_id
        JOIN DOCTOR D ON T.doctor_id=D.doctor_id
        ORDER BY PR.prescription_id DESC""")
    prescriptions = cur.fetchall()
    for rx in prescriptions:
        cur.execute("""SELECT M.medicine_name FROM PRESCRIPTION_MEDICINE PM
                       JOIN MEDICINE M ON PM.medicine_id=M.medicine_id
                       WHERE PM.prescription_id=%s""", (rx['prescription_id'],))
        rx['medicines'] = [r['medicine_name'] for r in cur.fetchall()]
    db.close()
    return render_template('prescriptions.html', prescriptions=prescriptions)

@app.route('/prescriptions/add', methods=['GET','POST'])
def add_prescription():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        cur.execute("""INSERT INTO PRESCRIPTION (treatment_id,dosage,instructions,duration)
                       VALUES (%s,%s,%s,%s) RETURNING prescription_id""",
                    (request.form['treatment_id'], form_value('dosage'),
                     form_value('instructions'),  form_value('duration')))
        pid = cur.fetchone()['prescription_id']
        for mid in request.form.getlist('medicines'):
            cur.execute("INSERT INTO PRESCRIPTION_MEDICINE VALUES (%s,%s)", (pid, mid))
        db.commit(); cur.close(); db.close()
        flash('Prescription added!', 'success')
        return redirect(url_for('prescriptions'))
    cur.execute("SELECT T.treatment_id, CONCAT(P.first_name,' ',P.last_name,' - ',T.diagnosis) AS label FROM TREATMENT T JOIN PATIENT P ON T.patient_id=P.patient_id")
    treatments = cur.fetchall()
    cur.execute("SELECT * FROM MEDICINE")
    meds = cur.fetchall(); db.close()
    return render_template('add_prescription.html', treatments=treatments, medicines=meds)

# ══════════════════════════════════════════════════════════════
#  ROOMS
# ══════════════════════════════════════════════════════════════
@app.route('/rooms')
def rooms():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM ROOM ORDER BY room_no")
    data = cur.fetchall(); db.close()
    return render_template('rooms.html', rooms=data)

@app.route('/rooms/add', methods=['GET','POST'])
def add_room():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO ROOM (room_no,room_type,status) VALUES (%s,%s,%s)",
                    (request.form['room_no'], form_value('room_type'), form_value('status')))
        db.commit(); db.close()
        flash('Room added!', 'success')
        return redirect(url_for('rooms'))
    return render_template('add_room.html')

@app.route('/rooms/delete/<int:rno>')
def delete_room(rno):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM ROOM_ALLOCATED WHERE room_no=%s", (rno,))
        cur.execute("DELETE FROM ROOM WHERE room_no=%s", (rno,))
        db.commit()
        flash('Room and its allocation records deleted.', 'info')
    except psycopg2.Error as e:
        db.rollback()
        flash(f'Could not delete room: {e.pgerror or e}', 'danger')
    finally:
        cur.close(); db.close()
    return redirect(url_for('rooms'))

# ══════════════════════════════════════════════════════════════
#  ROOM ALLOCATION
# ══════════════════════════════════════════════════════════════
@app.route('/allocations')
def allocations():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT RA.*,
        CONCAT(P.first_name,' ',P.last_name) AS patient_name,
        R.room_type
        FROM ROOM_ALLOCATED RA
        JOIN PATIENT P ON RA.patient_id=P.patient_id
        JOIN ROOM R ON RA.room_no=R.room_no
        ORDER BY RA.admission_date DESC""")
    data = cur.fetchall(); db.close()
    return render_template('allocations.html', allocations=data)

@app.route('/allocations/add', methods=['GET','POST'])
def add_allocation():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        cur.execute("""INSERT INTO ROOM_ALLOCATED
            (patient_id,room_no,bed_no,admission_reason,admission_date,discharge_date)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (request.form['patient_id'],      request.form['room_no'],
             form_value('bed_no'),          form_value('admission_reason'),
             request.form['admission_date'],  request.form.get('discharge_date') or None))
        cur.execute("UPDATE ROOM SET status='Occupied' WHERE room_no=%s", (request.form['room_no'],))
        db.commit(); db.close()
        flash('Room allocated!', 'success')
        return redirect(url_for('allocations'))
    cur.execute("SELECT patient_id, CONCAT(first_name,' ',last_name) AS name FROM PATIENT")
    patients = cur.fetchall()
    cur.execute("SELECT room_no, room_type FROM ROOM WHERE status='Available'")
    rooms = cur.fetchall(); db.close()
    return render_template('add_allocation.html', patients=patients, rooms=rooms)

@app.route('/allocations/delete/<int:aid>')
def delete_allocation(aid):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT room_no FROM ROOM_ALLOCATED WHERE allocation_id=%s", (aid,))
        allocation = cur.fetchone()
        if allocation:
            room_no = allocation[0]
            cur.execute("DELETE FROM ROOM_ALLOCATED WHERE allocation_id=%s", (aid,))
            cur.execute("UPDATE ROOM SET status='Available' WHERE room_no=%s", (room_no,))
            db.commit()
            flash('Room allocation deleted and room marked available.', 'info')
        else:
            flash('Room allocation not found.', 'warning')
    except psycopg2.Error as e:
        db.rollback()
        flash(f'Could not delete room allocation: {e.pgerror or e}', 'danger')
    finally:
        cur.close(); db.close()
    return redirect(url_for('allocations'))

# ══════════════════════════════════════════════════════════════
#  MEDICINES
# ══════════════════════════════════════════════════════════════
@app.route('/medicines')
def medicines():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM MEDICINE ORDER BY medicine_id DESC")
    data = cur.fetchall(); db.close()
    return render_template('medicines.html', medicines=data)

@app.route('/medicines/add', methods=['GET','POST'])
def add_medicine():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO MEDICINE (medicine_name,price,expiry_date) VALUES (%s,%s,%s)",
                    (request.form['medicine_name'], money_value('price'), form_value('expiry_date')))
        db.commit(); db.close()
        flash('Medicine added!', 'success')
        return redirect(url_for('medicines'))
    return render_template('add_medicine.html')

@app.route('/medicines/delete/<int:mid>')
def delete_medicine(mid):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM PRESCRIPTION_MEDICINE WHERE medicine_id=%s", (mid,))
        cur.execute("DELETE FROM MEDICINE WHERE medicine_id=%s", (mid,))
        db.commit()
        flash('Medicine deleted.', 'info')
    except psycopg2.Error as e:
        db.rollback()
        flash(f'Could not delete medicine: {e.pgerror or e}', 'danger')
    finally:
        cur.close(); db.close()
    return redirect(url_for('medicines'))

# ══════════════════════════════════════════════════════════════
#  BILLING
# ══════════════════════════════════════════════════════════════
@app.route('/billing')
def billing():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT B.*,
        CONCAT(P.first_name,' ',P.last_name) AS patient_name
        FROM BILL B
        JOIN PATIENT P ON B.patient_id=P.patient_id
        ORDER BY B.bill_id DESC""")
    data = cur.fetchall(); db.close()
    return render_template('billing.html', bills=data)

@app.route('/billing/add', methods=['GET','POST'])
def add_bill():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        doc_fee  = money_value('doctor_fee')
        med_fee  = money_value('medicine_fee')
        room_chg = money_value('room_charge')
        total    = doc_fee + med_fee + room_chg
        cur.execute("""INSERT INTO BILL
            (patient_id,payment_date,payment_method,payment_status,
             doctor_fee,medicine_fee,room_charge,total_amount)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (request.form['patient_id'],    request.form['payment_date'],
             form_value('payment_method'),form_value('payment_status'),
             doc_fee, med_fee, room_chg, total))
        db.commit(); db.close()
        flash('Bill generated!', 'success')
        return redirect(url_for('billing'))
    cur.execute("SELECT patient_id, CONCAT(first_name,' ',last_name) AS name FROM PATIENT")
    patients = cur.fetchall(); db.close()
    return render_template('add_bill.html', patients=patients)

@app.route('/billing/delete/<int:bid>')
def delete_bill(bid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM BILL WHERE bill_id=%s", (bid,))
    db.commit(); db.close()
    flash('Bill deleted.', 'info')
    return redirect(url_for('billing'))

@app.errorhandler(psycopg2.Error)
def handle_database_error(error):
    # Keep database errors visible in the UI instead of leaving a broken 500 page.
    app.logger.exception("Database error")
    flash(f"Database error: {error}", "danger")
    return redirect(request.referrer or url_for('index'))

@app.errorhandler(400)
def handle_bad_request(error):
    flash(f"Invalid form request: {error}", "danger")
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
