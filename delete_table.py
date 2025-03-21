import sqlite3

DATABASE = "auraassist.db"

def delete_questions_table():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS questions;")
        conn.commit()
        conn.close()
        print("✅ Table 'questions' deleted successfully.")
    except Exception as e:
        print("❌ Error:", str(e))

delete_questions_table()
