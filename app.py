from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response, jsonify
import sqlite3
import cv2
import face_recognition
import numpy as np
import os
import time
import hashlib

app = Flask(__name__)
#---------------------------
DATABASE = "auraassist.db"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)


def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            answer TEXT NOT NULL,
            subject TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()

# Ensure users table exists
def create_users_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mobile TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            gender TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_users_table()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            email = request.form["email"]
            mobile = request.form["mobile"]
            date_of_birth = request.form["date_of_birth"]
            gender = request.form["gender"]
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]

            if password != confirm_password:
                return jsonify({"error": "Passwords do not match!"}), 400

            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                conn.close()
                return jsonify({"error": "Email already registered!"}), 400

            hashed_password = hash_password(password)

            cursor.execute('''
                INSERT INTO users (first_name, last_name, email, mobile, date_of_birth, gender, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (first_name, last_name, email, mobile, date_of_birth, gender, hashed_password))

            conn.commit()
            conn.close()

            return jsonify({"success": "User registered successfully!"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template("register.html")



@app.route("/submit_question/", methods=["POST"])
def submit_question():
    try:
        data = request.get_json()  # Read JSON data

        # Debugging: Print incoming data
        print("Incoming JSON:", data)

        question = data.get("question")
        option1 = data.get("option1")
        option2 = data.get("option2")
        option3 = data.get("option3")
        option4 = data.get("option4")
        answer = data.get("answer")
        subject = data.get("subject")

        if not all([question, option1, option2, option3, option4, answer, subject]):
            return jsonify({"error": "All fields are required!"}), 400

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO questions (question, option1, option2, option3, option4, answer, subject)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (question, option1, option2, option3, option4, answer, subject))

        conn.commit()
        conn.close()

        return jsonify({"message": "Question added successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/exam")
def home():
    return render_template("exam.html") 
@app.route("/get_questions", methods=["GET"])
def get_questions():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions")
        questions = cursor.fetchall()
        conn.close()

        # Convert data into a list of dictionaries
        question_list = [
            {
                "id": row[0],
                "question": row[1],
                "option1": row[2],
                "option2": row[3],
                "option3": row[4],
                "option4": row[5],
                "answer": row[6],
                "subject": row[7],
            }
            for row in questions
        ]

        return jsonify(question_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 400



import sqlite3

def create_response_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            selected_option TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    conn.commit()
    conn.close()

# Call the function to create the table
create_response_table()

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    try:
        data = request.json
        question_id = data.get("question_id")
        selected_option = data.get("selected_option")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO responses (question_id, selected_option)
            VALUES (?, ?)
        ''', (question_id, selected_option))

        conn.commit()
        conn.close()

        return jsonify({"message": "Answer submitted successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

#---------------------------
app.secret_key = 'your_secret_key'  # Required for session management

KNOWN_FACES_DIR = "known_faces"

# Global variables for webcam and latest frame
cap = None
latest_frame = None

# Load known faces from storage
def load_known_faces():
    known_encodings = []
    known_names = []
    
    for filename in os.listdir(KNOWN_FACES_DIR):
        img_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(image)

        if encoding:
            known_encodings.append(encoding[0])
            known_names.append(filename.split(".")[0])  # Use filename as candidate ID

    return known_encodings, known_names

KNOWN_ENCODINGS, KNOWN_NAMES = load_known_faces()

# Database connection
def connect_db():
    return sqlite3.connect('auraassist.db')

@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/instructions')
def instructions_page():
    if 'assessment_id' in session:
        return render_template('instructions.html')
    else:
        return redirect(url_for('landing_page'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and verify_password(user[1], password):
            session['user_id'] = user[0]  # Store user session
            print(f"User {user[0]} logged in")  # Debugging log

            # Check if the request is AJAX (fetch)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"redirect_url": url_for("host_page")})
            else:
                return redirect(url_for("host_page"))  # Regular form submission

        return jsonify({"error": "Invalid email or password!"}), 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route("/host")
def host_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("host.html")

def start_camera():
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
        time.sleep(2)  # Delay for camera to warm up
        if not cap.isOpened():
            print("⚠️ Could not access webcam.")
            return False
    return True

def stop_camera():
    global cap
    if cap and cap.isOpened():
        cap.release()
    cap = None

@app.route('/face-verification')
def face_verification_page():
    return render_template('face_verification.html')

@app.route('/verify-face', methods=['POST'])
def verify_face():
    global latest_frame
    data = request.get_json()
    assessment_id = data.get('assessment_id')

    if not assessment_id:
        return jsonify({'error': 'Assessment ID is required!'}), 400

    if not start_camera():
        return jsonify({'error': 'Could not access webcam!'}), 500

    success, frame = cap.read()
    if not success:
        stop_camera()  # Stop camera if frame is not captured
        return jsonify({'error': 'Could not capture image!'}), 500

    latest_frame = frame  # Store latest frame

    # Convert frame to RGB for face recognition
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Find faces in the captured image
    face_encodings = face_recognition.face_encodings(frame_rgb)
    
    if not face_encodings:
        stop_camera()  # Stop camera if no face detected
        return jsonify({'error': 'No face detected!'}), 400

    # Compare with known faces
    match = face_recognition.compare_faces(KNOWN_ENCODINGS, face_encodings[0])
    if True in match:
        matched_index = match.index(True)
        matched_name = KNOWN_NAMES[matched_index]

        session['assessment_id'] = assessment_id  # Store session for authentication
        stop_camera()  # Stop camera after successful verification
        return jsonify({'success': True, 'message': 'Face verified!', 'redirect_url': url_for('instructions_page')})
    
    stop_camera()  # Stop camera if face verification fails
    return jsonify({'error': 'Face verification failed!'}), 401

# Webcam streaming function
def generate_frames():
    global latest_frame
    if not start_camera():
        return None

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            latest_frame = frame
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')  
def video_feed():  
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')  


if __name__ == '__main__':
    app.run(debug=True)
