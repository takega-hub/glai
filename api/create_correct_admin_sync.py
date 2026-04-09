import psycopg2
import sys
import os
from decouple import config

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.auth.security import get_password_hash
from datetime import datetime

# Connect to localhost since we are running from the host
DATABASE_URL = config("DATABASE_URL", default="postgresql://postgres:password@localhost:5432/eva_ai")

def create_correct_admin_sync():
    conn = None
    try:
        print("Connecting to the database...")
        conn = psycopg2.connect(DATABASE_URL)
        print("Database connection successful.")
        
        cur = conn.cursor()
        
        email = "admin@example.com"
        password = "admin123"
        
        print(f"Hashing password for {email}...")
        hashed_password = get_password_hash(password)
        print("Password hashed successfully.")
        
        query = """
        INSERT INTO users (email, password_hash, role, created_at, status)
        VALUES (%s, %s, 'super_admin', %s, 'active')
        """
        
        print("Executing INSERT query...")
        cur.execute(query, (email, hashed_password, datetime.utcnow()))
        conn.commit()
        print(f"Correct admin user with email '{email}' created successfully.")

    except Exception as e:
        print(f"Error creating correct admin user: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            print("Closing database connection.")
            conn.close()

if __name__ == "__main__":
    print("Starting correct admin creation...")
    create_correct_admin_sync()
    print("Correct admin creation process finished.")
