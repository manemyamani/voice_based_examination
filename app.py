from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import sqlite3
import cv2
import face_recognition
import numpy as np
import os
import time

app = Flask(__name__)
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for('landing_page'))
        else:
            return jsonify({'error': 'Invalid email or password!'}), 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match!'}), 400

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (first_name, last_name, email, mobile, date_of_birth, gender, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, mobile, date_of_birth, gender, password))
        conn.commit()
        conn.close()

        return jsonify({'success': 'User registered successfully!'}), 200
    return render_template('register.html')

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
