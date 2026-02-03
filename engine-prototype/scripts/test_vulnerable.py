# engine-prototype/scripts/test_vulnerable.py
#!/usr/bin/env python3
"""
Archivo con vulnerabilidades intencionales para pruebas SAST.
"""

import os
import subprocess
import pickle
import sqlite3
from flask import Flask

app = Flask(__name__)

# 1. Command Injection
def insecure_command():
    user_input = input("Enter filename: ")
    # Vulnerabilidad: command injection
    os.system(f"ls -la {user_input}")

# 2. Hardcoded password
DB_PASSWORD = "supersecret123"  # Vulnerabilidad: hardcoded secret

# 3. SQL Injection
def get_user(username):
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    # Vulnerabilidad: SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchall()

# 4. Pickle deserialization
def load_data(data):
    # Vulnerabilidad: pickle deserialization
    return pickle.loads(data)

# 5. Shell injection
def run_command(command):
    # Vulnerabilidad: shell injection
    subprocess.call(command, shell=True)

# 6. Flask debug mode
if __name__ == '__main__':
    app.run(debug=True)  # Vulnerabilidad: debug mode enabled in production

# 7. Assert used in production
def check_admin(user):
    assert user.is_admin, "User is not admin"  # Vulnerabilidad: assert in production
    return True

# 8. Insecure hashing (MD5)
import hashlib
def hash_password(password):
    # Vulnerabilidad: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()

# 9. Insecure randomness
import random
def generate_token():
    # Vulnerabilidad: predictable random
    return random.randint(1, 1000)

# 10. Bandit test case: try-except-pass
def silent_fail():
    try:
        risky_operation()
    except:
        pass  # Vulnerabilidad: silent exception