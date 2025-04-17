
import sqlite3

# Connect to SQLite database (or create if not exists)
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Create a table for users
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Commit changes and close the connection
conn.commit()
conn.close()

print("Database setup complete.")


>>>>>>> 361f2722304a379eb268dde65c360b052859e181
