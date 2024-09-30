from config import *
import pymysql


connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, cursorclass=pymysql.cursors.DictCursor)

with connection.cursor() as cursor:
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()

    if (DB_NAME,) not in databases:
        cursor.execute(f"CREATE DATABASE {DB_NAME}")

connection.close()