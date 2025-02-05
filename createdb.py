import sqlite3

def create_database():
    conn = sqlite3.connect("auraassist.db")
    cursor = conn.cursor()

    # Create table for storing assessment details
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT UNIQUE NOT NULL,
            candidate_images_folder TEXT NOT NULL,
            instructions_pdf TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("Database and table created successfully.")
