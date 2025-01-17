import sqlite3
from werkzeug.security import generate_password_hash

# Connect to the SQLite database
conn = sqlite3.connect('parking_tickets.db')
cursor = conn.cursor()

# Create the users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

conn.commit()
conn.close()
