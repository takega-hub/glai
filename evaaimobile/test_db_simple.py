import psycopg2

def test_connection():
    try:
        # Try to connect to the database with explicit connection parameters
        print("Attempting to connect to PostgreSQL...")
        conn = psycopg2.connect(
            host="172.19.0.2",
            port=5432,
            database="eva_ai",
            user="postgres",
            password="password",
            connect_timeout=10
        )
        print("✅ Successfully connected to database!")
        
        # Test a simple query
        cur = conn.cursor()
        cur.execute('SELECT version()')
        result = cur.fetchone()
        print(f"PostgreSQL version: {result[0]}")
        
        cur.close()
        conn.close()
        print("Connection closed successfully")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Operational error: {e}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()