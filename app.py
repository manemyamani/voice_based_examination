from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response, jsonify
import sqlite3
import cv2
import face_recognition
import numpy as np
import os
import time
import hashlib
import sqlite3

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
            assessment_id INTEGER NOT NULL,  -- Added assessment_id column
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

def create_responses_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            response1 TEXT,
            response2 TEXT,
            response3 TEXT,
            response4 TEXT,
            response5 TEXT,
            response6 TEXT,
            response7 TEXT,
            response8 TEXT,
            response9 TEXT,
            response10 TEXT,
            response11 TEXT,
            response12 TEXT,
            response13 TEXT,
            response14 TEXT,
            response15 TEXT,
            response16 TEXT,
            response17 TEXT,
            response18 TEXT,
            response19 TEXT,
            response20 TEXT,
            response21 TEXT,
            response22 TEXT,
            response23 TEXT,
            response24 TEXT,
            response25 TEXT,
            response26 TEXT,
            response27 TEXT,
            response28 TEXT,
            response29 TEXT,
            response30 TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_responses_table()


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



@app.route('/submit_question/', methods=['POST'])
def submit_question():
    try:
        data = request.json

        # Extract values from request
        assessment_id = data.get('assessment_id')  # Get assessment_id
        question = data.get('question')
        option1 = data.get('option1')
        option2 = data.get('option2')
        option3 = data.get('option3')
        option4 = data.get('option4')
        answer = data.get('answer')
        subject = data.get('subject')

        # Insert into the database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO questions (assessment_id, question, option1, option2, option3, option4, answer, subject)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (assessment_id, question, option1, option2, option3, option4, answer, subject))
        conn.commit()
        conn.close()

        return jsonify({"message": "Question submitted successfully!"}), 200

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
    
@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    try:
        data = request.json
        assessment_id = data.get("assessment_id")
        user_id = data.get("user_id")

        if not assessment_id or not user_id:
            return jsonify({"error": "Missing assessment_id or user_id"}), 400

        # Get the number of responses dynamically
        responses = {key: value for key, value in data.items() if key.startswith("response")}

        # Construct the SQL query dynamically
        columns = ", ".join(responses.keys())
        placeholders = ", ".join(["?"] * len(responses))

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                {columns}
            )
        ''')

        cursor.execute(f'''
            INSERT INTO responses (assessment_id, user_id, {columns})
            VALUES (?, ?, {placeholders})
        ''', (assessment_id, user_id, *responses.values()))

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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
                return redirect(url_for("assessment"))  # Regular form submission

        return jsonify({"error": "Invalid email or password!"}), 401

    return render_template("login.html")
@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    if request.method == "POST":
        # Handle assessment submission logic
        assessment_id = request.form["assessmentId"]
        question_count = request.form["questionCount"]

        # Redirect to host.html after setting assessment
        return redirect(url_for("host_page", assessmentId=assessment_id, questionCount=question_count))

    return render_template("assessment.html")

# Function to get the next assessment ID
def get_next_assessment_id():
    try:
        conn = sqlite3.connect(DATABASE)  # Use the correct database
        cursor = conn.cursor()

        # Query to get the max assessment_id from the questions table
        cursor.execute("SELECT MAX(assessment_id) FROM questions")
        max_id = cursor.fetchone()[0]

        conn.close()

        # If no records exist, start from 1, otherwise increment max_id
        return (max_id + 1) if max_id else 1

    except Exception as e:
        print("Error fetching next assessment ID:", e)
        return None

@app.route("/get_next_assessment_id", methods=["GET"])
def get_next_assessment():
    next_id = get_next_assessment_id()
    if next_id is None:
        return jsonify({"error": "Failed to retrieve next assessment ID"}), 500

    return jsonify({"next_assessment_id": next_id})

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route("/host")
def host_page():
    assessment_id = request.args.get("assessmentId")
    question_count = request.args.get("questionCount")
    return render_template("host.html", assessment_id=assessment_id, question_count=question_count)


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
