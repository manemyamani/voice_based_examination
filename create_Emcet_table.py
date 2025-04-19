import sqlite3

def create_database():
    conn = sqlite3.connect("auraassist.db")
    cursor = conn.cursor()

    # Create table for storing assessment details

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EMCET (
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
def insert_data(assessment_id, question, option1, option2, option3, option4, answer, subject):
    conn = sqlite3.connect("auraassist.db")
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO EMCET (assessment_id, question, option1, option2, option3, option4, answer, subject)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (assessment_id, question, option1, option2, option3, option4, answer, subject))

    conn.commit()
    conn.close()
    print("Data inserted successfully!")
insert_data(9491,"√50+√18","8√2","7√2","9√2","10√2","7√2","Mathematics")
insert_data(9491,"In a cyclic quadrilateral, one angle is 100°,another is  90° and the third is 85°. Find the fourth angle","75°","85°","65°","95°","75°","Mathematics")
insert_data(9491,"∫(x ^2+3x+5)dx where x=2?","18.66","19","19.33","15.9","18.66","Mathematics")
insert_data(9491,"Which of the following is an example of a covalent compound?","Nacl","H2O","KBr","CaCl","H2O","Chemistry")
insert_data(9491,"What is the pH of a solution with H + = 1×10 ^−3 Molecules?","3","1","5","7","3","Chemistry")
insert_data(9491,"What is the molar mass of sodium chloride ?","23 gram per mol","58.5 gram per mol","44 gram per mol","33.4 gram per mol","58.5 gram per mol","Chemistry")
insert_data(9491,"The work done in moving a charge of 5 Columb across a potential difference of 12 Volts is?","50 Joules","60 Joules","70 Joules","80 Joules","60 Joules","Physics")
insert_data(9491,"Which of the following lenses had the highest power?","+2D","-5D","+4D","-2D","+2D","Physics")
if __name__ == "__main__":
    create_database()
    print("Database and table created successfully.")
