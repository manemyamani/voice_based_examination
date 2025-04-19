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
DATABASE = "auraassist.db"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)
def is_valid_assessment_id(assessment_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM questions WHERE assessment_id = ?", (assessment_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None  

@app.route('/validate-assessment-id', methods=['POST'])
def validate_assessment_id():
    data = request.get_json()
    assessment_id = data.get('assessment_id')
    if not assessment_id:
        return jsonify({"valid": False})     
    valid = is_valid_assessment_id(assessment_id)    
    return jsonify({"valid": valid})

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
        assessment_id = data.get('assessment_id') 
        question = data.get('question')
        option1 = data.get('option1')
        option2 = data.get('option2')
        option3 = data.get('option3')
        option4 = data.get('option4')
        answer = data.get('answer')
        subject = data.get('subject')
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
        assessment_id = request.args.get('assessment_id')
        candidate_id = request.args.get("candidate_id")
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        if assessment_id:
            cursor.execute("""
                SELECT 
                    id, 
                    assessment_id, 
                    question, 
                    option1, 
                    option2, 
                    option3, 
                    option4, 
                    answer, 
                    subject 
                FROM questions 
                WHERE assessment_id = ?
            """, (assessment_id,))
        else:
            
            conn.close()
            return jsonify({"error": "Assessment ID is required"}), 400
        
        questions = cursor.fetchall()
        conn.close()

        if not questions:
            return jsonify({"error": "No questions found for this assessment ID"}), 404

        # Convert data into a list of dictionaries
        question_list = [
            {
                "id": row[0],
                "assessment_id": row[1],
                "question": row[2],
                "option1": row[3],
                "option2": row[4],
                "option3": row[5],
                "option4": row[6],
                "answer": row[7],
                "subject": row[8]
            }
            for row in questions
        ]

        # return jsonify(question_list)
        return jsonify({"candidate_name": candi_name, "questions": question_list})


    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 400


@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    try:
        data = request.json
        assessment_id = data.get("assessment_id")
        user_id = data.get("user_id")

        if not assessment_id or not user_id:
            return jsonify({"error": "Missing assessment_id or user_id"}), 400

        # Get dynamic responses
        responses = {key: value for key, value in data.items() if key.startswith("response")}
        
        if not responses:
            return jsonify({"error": "No responses received"}), 400

        # Construct the SQL query dynamically
        columns = ", ".join(responses.keys())
        placeholders = ", ".join(["?"] * len(responses))

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Ensure the table exists (but avoid creating it dynamically every time)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                user_id TEXT NOT NULL
            )
        ''')

        # Check if columns already exist; if not, add them dynamically
        existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(responses)")}
        new_columns = set(responses.keys()) - existing_columns

        for col in new_columns:
            cursor.execute(f"ALTER TABLE responses ADD COLUMN {col} TEXT")

        # Insert data dynamically
        sql = f'''
            INSERT INTO responses (assessment_id, user_id, {columns})
            VALUES (?, ?, {placeholders})
        '''
        cursor.execute(sql, (assessment_id, candi_name, *responses.values()))

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

app.secret_key = 'your_secret_key'  
KNOWN_FACES_DIR = "known_faces"

cap = None
latest_frame = None

def load_known_faces():
    known_encodings = []
    known_names = []
    
    for filename in os.listdir(KNOWN_FACES_DIR):
        img_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(image)

        if encoding:
            known_encodings.append(encoding[0])
            known_names.append(filename.split(".")[0])  

    return known_encodings, known_names

KNOWN_ENCODINGS, KNOWN_NAMES = load_known_faces()

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
# @app.route("/transfer_questions", methods=["POST"])
# def transfer_questions():
#     try:
#         data = request.get_json()
#         assessment_id = data.get("assessmentId")
        
#         # Connect to database
#         conn = sqlite3.connect("auraassist.db")
#         cursor = conn.cursor()
        
#         # First clear existing questions with this assessment ID (optional)
#         cursor.execute("DELETE FROM questions WHERE assessment_id = ?", (assessment_id,))
        
#         # Fetch questions from EMCET table with the specified assessment ID
#         cursor.execute("SELECT * FROM EMCET WHERE assessment_id = ?", (assessment_id,))
#         emcet_questions = cursor.fetchall()
        
#         if not emcet_questions:
#             return jsonify({"error": "No questions found with the specified assessment ID"}), 404
        
#         # Insert questions into questions table
#         for question in emcet_questions:
#             # Skip the ID column from EMCET when inserting into questions
#             # The order should match your table schema: assessment_id, question, option1, option2, option3, option4, answer, subject
#             cursor.execute("""
#                 INSERT INTO questions
#                 (assessment_id, question, option1, option2, option3, option4, answer, subject)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#             """, (
#                 question[1],  # assessment_id
#                 question[2],  # question
#                 question[3],  # option1
#                 question[4],  # option2
#                 question[5],  # option3
#                 question[6],  # option4
#                 question[7],  # answer
#                 question[8]   # subject
#             ))
        
#         conn.commit()
#         conn.close()
        
#         return jsonify({"success": True, "message": f"Transferred {len(emcet_questions)} questions to questions table"}), 200
    
#     except Exception as e:
#         conn.rollback()  # Roll back in case of error
#         conn.close()
#         return jsonify({"error": str(e)}), 500
@app.route("/transfer_questions", methods=["POST"])
def transfer_questions():
    try:
        data = request.get_json()
        assessment_id = data.get("assessmentId")
        
        # Connect to database
        conn = sqlite3.connect("auraassist.db")
        cursor = conn.cursor()
        
        # Check if questions already exist for this assessment ID
        cursor.execute("SELECT COUNT(*) FROM questions WHERE assessment_id = ?", (assessment_id,))
        existing_questions_count = cursor.fetchone()[0]
        
        if existing_questions_count > 0:
            conn.close()
            return jsonify({
                "success": False, 
                "message": "Questions for this assessment ID already exist", 
                "exists": True
            }), 200
        
        # Fetch questions from EMCET table with the specified assessment ID
        cursor.execute("SELECT * FROM EMCET WHERE assessment_id = ?", (assessment_id,))
        emcet_questions = cursor.fetchall()
        
        if not emcet_questions:
            conn.close()
            return jsonify({"error": "No questions found with the specified assessment ID"}), 404
        
        # Insert questions into questions table
        for question in emcet_questions:
            # Skip the ID column from EMCET when inserting into questions
            # The order should match your table schema: assessment_id, question, option1, option2, option3, option4, answer, subject
            cursor.execute("""
                INSERT INTO questions
                (assessment_id, question, option1, option2, option3, option4, answer, subject)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question[1],  # assessment_id
                question[2],  # question
                question[3],  # option1
                question[4],  # option2
                question[5],  # option3
                question[6],  # option4
                question[7],  # answer
                question[8]   # subject
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Transferred {len(emcet_questions)} questions to questions table",
            "exists": False
        }), 200
    
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()  # Roll back in case of error
            conn.close()
        return jsonify({"error": str(e)}), 500
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
            session['user_id'] = user[0] 
            print(f"User {user[0]} logged in")  

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"redirect_url": url_for("host_page")})
            else:
                return redirect(url_for("assessment"))  

        return jsonify({"error": "Invalid email or password!"}), 401

    return render_template("login.html")
@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    if request.method == "POST":
       
        assessment_id = request.form["assessmentId"]
        question_count = request.form["questionCount"]

        return redirect(url_for("host_page", assessmentId=assessment_id, questionCount=question_count))

    return render_template("assessment.html")

def get_next_assessment_id():
    try:
        conn = sqlite3.connect(DATABASE) 
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(assessment_id) FROM questions")
        max_id = cursor.fetchone()[0]

        conn.close()

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
            print("⚠ Could not access webcam.")
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
    global latest_frame, candi_name
    data = request.get_json()
    assessment_id = data.get('assessment_id')

    if not assessment_id:
        return jsonify({
            'error': 'Assessment ID is required!',
            'voice_alert': 'Assessment ID is required. Please provide a valid assessment ID.'
        }), 400

    if not start_camera():
        return jsonify({
            'error': 'Could not access webcam!',
            'voice_alert': 'Camera error. Could not access webcam. Please check your camera settings.'
        }), 500

    success, frame = cap.read()
    if not success:
        stop_camera()  # Stop camera if frame is not captured
        return jsonify({
            'error': 'Could not capture image!',
            'voice_alert': 'Failed to capture image. Please try again.'
        }), 500

    latest_frame = frame  # Store latest frame

    # Convert frame to RGB for face recognition
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(frame_rgb)
    
    if len(face_locations) == 0:
        stop_camera()
        return jsonify({
            'error': 'No face detected!',
            'voice_alert': 'No face detected. Please position yourself in front of the camera.'
        }), 400
        
    if len(face_locations) > 1:
        stop_camera()
        return jsonify({
            'error': 'Multiple faces detected! Only one person is allowed.',
            'voice_alert': 'Multiple faces detected. Only one person is allowed during the exam.',
            'multiple_faces': True
        }), 400

    # Compare with known faces
    known_face_encodings = []
    known_face_names = []
    
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(KNOWN_FACES_DIR, filename)
            try:
                known_image = face_recognition.load_image_file(img_path)
                encoding = face_recognition.face_encodings(known_image)
                
                if encoding:
                    known_face_encodings.append(encoding[0])
                    known_face_names.append(os.path.splitext(filename)[0])
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Verification parameters
    MATCH_THRESHOLD = 0.5  # Adjust for stricter matching
    current_face_encoding = face_recognition.face_encodings(frame_rgb, face_locations)[0]

    # Compare with known faces
    matches = face_recognition.compare_faces(known_face_encodings, current_face_encoding)
    face_distances = face_recognition.face_distance(known_face_encodings, current_face_encoding)

    # Find best match
    best_match_index = None
    if True in matches:
        best_match_index = matches.index(True)
        
        # Additional confidence check
        if face_distances[best_match_index] > MATCH_THRESHOLD:
            best_match_index = None

    # Stop camera
    stop_camera()

    # Verification result
    if best_match_index is not None:
        matched_name = known_face_names[best_match_index]
        
        # Log verification
        print(f"✅ Verified User: {matched_name}")
        candi_name = str(matched_name)
      
        # Set session variables for security
        session['candidate_id'] = matched_name
        session['assessment_id'] = assessment_id
        
        return jsonify({
            'success': True,
            'message': f'Face verified for {matched_name}',
            'voice_alert': f'Verification successful.',
            'username': matched_name,
            'redirect_url': url_for('instructions_page')
        }), 200
    else:
        return jsonify({
            'error': 'Unauthorized user! Only registered candidates can take the exam.', 
            'voice_alert': 'Unauthorized user detected. Only registered candidates can take this exam.',
            'unauthorized': True
        }), 401



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
    app.run(host='0.0.0.0', port=5000)