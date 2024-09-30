from config import *
import pymysql

connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )

def connect_to_db():
    global connection
    while True:
        try:
            with connection.cursor() as cursor:
                create_table_query = f"CREATE TABLE IF NOT EXISTS user (platform varchar(32), id varchar(32), name varchar(100), countArif int, timeArif float, countP int, countU int, countC int, countM int, countF int, ratingP int, ratingU int, ratingC int, ratingM int, ratingF int, allRating int, PRIMARY KEY (id))"
                cursor.execute(create_table_query)
                connection.commit()
            break
        except:
            try:
                connection = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor
            )
            except:
                print('Подключение к бд...')


connect_to_db()

def add_user(id, name, platform):
    connect_to_db()
    with connection.cursor() as cursor:
        sql = "INSERT INTO `user`(`platform`, `id`, `name`, `countArif`, `timeArif`, `countP`, `countU`, `countC`, `countM`, `countF`, `ratingP`, `ratingU`, `ratingC`, `ratingM`, `ratingF`, `allRating`) VALUES (%s, %s, %s, 0, -1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)"
        val = (platform, id, name)
        cursor.execute(sql, val)
        connection.commit()

def get_user_info(id):
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `user` WHERE id='{id}'")
        return cursor.fetchall()[0]
    
def get_user_attribute(id, attr):
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {attr} FROM `user` WHERE id='{id}'")
        return cursor.fetchall()[0][attr]

def get_user_place(id):
    connect_to_db()
    with connection.cursor() as cursor:
        query = """
        SELECT COUNT(*) AS `rank`
        FROM `user`
        WHERE allRating >= (SELECT allRating FROM `user` WHERE id = %s)
        """
        cursor.execute(query, (id,))
        return cursor.fetchall()[0]['rank']



def get_users_top(count):
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT name, allRating FROM user ORDER BY allRating DESC LIMIT {count}")
        return cursor.fetchall()

def get_all_platform_users(platform):
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `user` WHERE platform = '{platform}'")
        return cursor.fetchall()

def get_all_users():
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `user`")
        return cursor.fetchall()

def set_new_value(id, column, value):
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE `user` SET `{column}`= {value} WHERE id='{id}'")
        connection.commit()

def set_new_values(id, val_list):
    connect_to_db()
    with connection.cursor() as cursor:
        for i in val_list:
            cursor.execute(f"UPDATE `user` SET {i[0]} = %s WHERE id=%s", (i[1], id))
        connection.commit()

def update_value(id, column, value):
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE `user` SET `{column}`= `{column}` + {value} WHERE id='{id}'")
        connection.commit()

def update_new_values(id, val_list):
    connect_to_db()
    with connection.cursor() as cursor:
        for i in val_list:
            cursor.execute(f"UPDATE `user` SET {i[0]} = {i[0]} + %s WHERE id=%s", (i[1], id))
        connection.commit()

def custom_command(command):
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()


def delete_all_stats():
    connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM `user`")
        connection.commit()
    