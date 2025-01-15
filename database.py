import sqlite3

# Connect to SQLite database (it will create the database if it doesn't exist)
conn = sqlite3.connect('auraassist.db')
cursor = conn.cursor()

# Create a table named 'users' for user registration
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mobile TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT NOT NULL,
    password TEXT NOT NULL
)
''')

print("Database and 'users' table created successfully.")

# Commit changes and close the connection
conn.commit()
conn.close()
