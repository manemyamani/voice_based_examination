from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database connection helper function
def connect_db():
    return sqlite3.connect('auraassist.db')

# Route for landing page
@app.route('/')
def landing_page():
    return render_template('index.html')

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email = request.form['email']
        password = request.form['password']

        # Verify user credentials
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for('landing_page'))  # Redirect to landing page after login
        else:
            return jsonify({'error': 'Invalid email or password!'}), 401

# Route for registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        try:
            # Get form data
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            mobile = request.form['mobile']
            date_of_birth = request.form['date_of_birth']
            gender = request.form['gender']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            # Validate password confirmation
            if password != confirm_password:
                return jsonify({'error': 'Passwords do not match!'}), 400

            # Insert user data into the database
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (first_name, last_name, email, mobile, date_of_birth, gender, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (first_name, last_name, email, mobile, date_of_birth, gender, password))
            conn.commit()
            conn.close()

            return jsonify({'success': 'User registered successfully!'}), 200

        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already exists!'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
