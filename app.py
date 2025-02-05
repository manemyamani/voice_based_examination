from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import cv2
import face_recognition
import numpy as np
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Path to the folder where candidate images are stored
KNOWN_FACES_DIR = "known_faces"

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

@app.route('/verify-face', methods=['POST'])
def verify_face():
    data = request.get_json()
    assessment_id = data.get('assessment_id')

    if not assessment_id:
        return jsonify({'error': 'Assessment ID is required!'}), 400

    # Capture live image using webcam
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({'error': 'Could not access webcam!'}), 500

    # Convert frame to RGB for face recognition
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Find faces in the captured image
    face_encodings = face_recognition.face_encodings(frame_rgb)
    
    if not face_encodings:
        return jsonify({'error': 'No face detected!'}), 400

    # Compare with known faces
    match = face_recognition.compare_faces(KNOWN_ENCODINGS, face_encodings[0])
    if True in match:
        matched_index = match.index(True)
        matched_name = KNOWN_NAMES[matched_index]

        session['assessment_id'] = assessment_id  # Store session for authentication
        return jsonify({'success': True, 'message': 'Face verified!', 'redirect_url': url_for('instructions_page')})
    
    return jsonify({'error': 'Face verification failed!'}), 401

if __name__ == '__main__':
    app.run(debug=True)
