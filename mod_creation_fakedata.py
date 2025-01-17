import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('parking_tickets.db')
cursor = conn.cursor()

# Create the tickets table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_plate TEXT NOT NULL,
        amount REAL NOT NULL,
        paid INTEGER NOT NULL DEFAULT 0
    )
''')

# Insert some sample data
sample_data = [
    ('ABC123', 50.0, 0),
    ('XYZ789', 75.0, 0),
    ('ABC123', 25.0, 1)  # Already paid ticket
]

cursor.executemany("INSERT INTO tickets (license_plate, amount, paid) VALUES (?, ?, ?)", sample_data)
conn.commit()
conn.close()
