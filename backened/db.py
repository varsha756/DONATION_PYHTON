import mysql.connector

def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="vasu06",
            database="donation_checker"
        )
        return conn
    except mysql.connector.Error as err:
        print("❌ Error:", err)
        return None