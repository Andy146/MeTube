import mysql.connector as mariadb
import sys
def db_connect():
    try:
        conn = mariadb.connect(
            user="admin",
            password="Passw0rd",
            host="localhost",
            port=3306,
            db='me_tube')
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    
    return conn