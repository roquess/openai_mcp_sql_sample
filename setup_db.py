# setup_db.py
import sqlite3

conn = sqlite3.connect("company.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    role TEXT,
    team TEXT,
    age INTEGER
)
""")

employees = [
    ("Alice", "dev", "frontend", 30),
    ("Bob", "dev", "backend", 28),
    ("Charlie", "dev", "backend", 35),
    ("Diana", "designer", "frontend", 26),
    ("Eve", "dev", "frontend", 24),
]

c.executemany("INSERT INTO employees (name, role, team, age) VALUES (?, ?, ?, ?)", employees)

conn.commit()
conn.close()
print("SQLite 'company.db' created !")

