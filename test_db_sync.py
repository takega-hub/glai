import psycopg2

def test_connection():
    try:
        # Try to connect to the database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="eva_ai",
            user="postgres",
            password="password"
        )
        print("✅ Successfully connected to database!")
        
        # Test a simple query
        cur = conn.cursor()
        cur.execute('SELECT 1')
        result = cur.fetchone()
        print(f"Test query result: {result}")
        
        cur.close()
        conn.close()
        print("Connection closed successfully")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()