import database as db

a = input("Вы уверены, что хотите обнулить всю статистику? y/n ")
if a == 'y':
    b = input("Вы ТОЧНО уверены, что хотите обнулить всю статистику? y/n ")
    if b == 'y':
        db.delete_all_stats()
