import re
import vk_api
import json
from vk_api.longpoll import VkLongPoll, VkEventType
from random import *
from time import *
import sys
import os
import requests
from jinja2 import Template
import zipfile
import database as db
from config import *


if VK_TOKEN == '':
    print("Токен для от бота в ВК не был найден, ВК версия не будет запущена!")
    exit()
    
vk = vk_api.VkApi(token=VK_TOKEN)

session = vk.get_api()
longpoll = VkLongPoll(vk)
cnt = -1
problem_answers = []
problem_text = []
problem_photos = []
users = {}
message_counter = 0
ver = []
problem = []
admin_commands = ["Управление ботом", "Save", "Перезагрузка", "Добавить задание", "Обнуление статистики",
                 "Таблица пользователей", "Дать права на добавление заданий"]
module_names = ["Переменные", "Условия", "Циклы", "Массивы", "Функции"]
mod_names_for_sql = ['P', 'U', 'C', 'M', 'F']
prims = [2, 1, 4, 2, 2, 2]
template = Template("""
  <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Таблица пользователей</title>
</head>
<body>
    <style>
        table {
          border-collapse: collapse;
          width: 75%;
          margin-left: auto;
          margin-right: auto;
        }
        th, td {
          text-align: center;
          padding: 8px;
          border: 1px solid black;
        }
        th {
          background-color: white;
          font-weight: bold;
        }
        p {
          text-align: center;
          font-size: 20;
        }
      </style>
          <p> Рейтинг пользователей </p>
          <table>
             <tr>
              <th scope="col", style="background-color: lightgray;">Пользователь</th>
              <th scope="col", style="background-color: lightgray;">Арифметика</th>
              <th scope="col", style="background-color: lightgray;">Переменные</th>
              <th scope="col", style="background-color: lightgray;">Условия</th>
              <th scope="col", style="background-color: lightgray;">Циклы</th>
              <th scope="col", style="background-color: lightgray;">Массивы</th>
              <th scope="col", style="background-color: lightgray;">Фукнции</th>
              <th scope="col", style="background-color: lightgray;">Всего балов</th>
              <th scope="col", style="background-color: lightgray;">Место</th>
            </tr>
            {% for item in my_array %}
            <tr>
              <th scope="col"><span style="color: {{item[9]}};">{{item[0]}}</span></th>
              <th scope="col">{{item[1]}}</th>
              <th scope="col">{{item[2]}}</th>
              <th scope="col">{{item[3]}}</th>
              <th scope="col">{{item[4]}}</th>
              <th scope="col">{{item[5]}}</th>
              <th scope="col">{{item[6]}}</th>
              <th scope="col">{{item[7]}}</th>
              <th scope="col">{{item[8]}}</th>
            </tr>
            {% endfor %}  
        </table>
</body>
</html>

""")

class User:
    def __init__(self, info):
        self.id = int(info['id'])
        self.num = 0
        self.quest = 0
        self.ans = 0
        self.solution_mode = -2
        self.tr = 0
        self.last_time = -1
        self.all_time = -1
        self.skips_count = 0
        self.mistakes_count = 0
        self.answer_choice = False
        self.ind = 0
        self.problem_indexes = [[], [], [], [], []]
        self.rating = 0
        self.old_rating = 0
        self.adminMode = -2
        self.name = info['name']
        self.problem_info = {}
        for i in range(cnt):
            self.problem_indexes[i] = [j for j in range(1, len(problem_answers[i]) + 1)]
            shuffle(self.problem_indexes[i])

    def get_problem(self):
        if self.solution_mode == -1:
            self.quest, self.ans = get_arif_problem(self.num)
            self.ans = str(self.ans)
            if self.num == 0 and self.skips_count + self.mistakes_count == 0:
                self.send_message(f"В данном модуле требуется выполнение примеров с использованием арифметических операций из языка Python. Количество примеров в модуле не ограничено.\n\nВот твой первый пример: {self.quest}", keyInf2)
                return
            self.send_message(self.quest, keyInf2)
        else:
            if self.ind >= len(problem_text[self.solution_mode]):
                self.ind = 0
                shuffle(self.problem_indexes[self.solution_mode])

            self.num = self.problem_indexes[self.solution_mode][self.ind] - 1
            self.ans, self.rating = problem_answers[self.solution_mode][self.num].split(" | ")
            self.rating = int(self.rating)
            if self.ans[0] == '!':
                self.answer_choice = True
                masAns = self.ans.split('!')
                masAns.pop(0)
                self.ans = masAns[0]
                keyInf3 = get_answer_options(masAns)
                self.send_photo(f'№{self.num + 1} ({self.rating} ☆)\n{problem_text[self.solution_mode][self.num]}', problem_photos[self.solution_mode][self.num], keyInf3)
                return
            self.send_photo(f'№{self.num + 1} ({self.rating} ☆)\n{problem_text[self.solution_mode][self.num]}', problem_photos[self.solution_mode][self.num], keyInf2)

    def get_user_answer(self, answer):
        if self.solution_mode == -1:
            if answer == "Пропустить":
                self.send_message("Хорошо, пример пропущен")
                self.skips_count += 1
                self.tr = 0
                self.get_problem()
                self.last_time = time()
                return
            answer = answer.replace(',', '.')
            if answer == self.ans:
                self.tr = 0
                self.num += 1
                if self.num in [5, 10, 20, 30, 40, 50]:
                    self.send_message(f"{choice(CORRECTLY)} ✅, Решено уже {self.num} примеров, {choice(CONGRATULATIONS)}")
                else:
                    self.send_message(f"{choice(CORRECTLY)} ✅")
                db.update_value(self.id, 'allRating', 1)
                times = time()
                if self.last_time != -1 and times - self.last_time < 120:
                    self.all_time += times - self.last_time
                self.last_time = times
                self.get_problem()
            else:
                if self.tr == 1:
                    ans = f"Снова неправильно, 😿\nПравильным ответом было: {self.ans}"
                    if self.quest.find("** 0.5") != -1:
                        ans += f"\n'**' обозначает возведение числа в степень. Если воозвести число в 0.5 степень, то это равносильно извлечению квадратного корня из числа."
                    elif self.quest.find("**") != -1:
                        a, b = self.quest.split(" ** ")
                        b, c = b.split(" = ")
                        ans += f"\n'**' обозначает возведение числа в степень. В данном случаем мы возводим число {a} в {b} степень"
                    elif self.quest.find("//") != -1:
                        ans += f"\n'//' обозначает целочисленное деление, то есть отбрасываем дробную часть"
                    elif self.quest.find("%") != -1:
                        ans += f"\n'%' обозначает остаток деления, то есть получает остаток деления первого числа на второе"
                    elif self.quest.find("abs") != -1:
                        ans += f"\n'abs' обозначает модуль числа, то есть изменяет знак минуса на плюс"
                    elif self.quest.find("round") != -1 and self.quest.find(",") != -1:
                        ans += f"\n'round' обозначает фукнцию округления числа, второе число показывает до какого знака надо округлять"
                    elif self.quest.find("round") != -1:
                        ans += f"\n'round' обозначает фукнцию округления числа, в данном случае округление до целого"
                    self.send_message(ans)
                    self.tr = 0
                    self.mistakes_count += 1
                    self.get_problem()
                    return
                self.send_message("Неправильно, 😿\nПопробуй ещё раз!")
                self.tr += 1
        else:
            if self.solution_mode == -2:
                if answer in module_names:
                    self.old_rating = db.get_user_attribute(self.id, 'allRating')
                    self.solution_mode = module_names.index(answer)
                    self.ind = 0
                    shuffle(self.problem_indexes[self.solution_mode])
                    self.get_problem()
                else:
                    self.send_message("Такого модуля не существует")
                    return
                return
            if answer == "Пропустить":
                self.tr = 0
                self.send_message("Хорошо, это задание пропущено")
                self.ind += 1
                self.answer_choice = False
                self.get_problem()
                return
            answer = answer.replace('&gt;', '>')
            if answer == self.ans and not self.answer_choice:
                db.update_new_values(self.id, [
                    [f'count{mod_names_for_sql[self.solution_mode]}', 1],
                    [f'rating{mod_names_for_sql[self.solution_mode]}', self.rating],
                    ['allRating', self.rating]
                ])
                self.tr = 0

                all_rating = db.get_user_attribute(self.id, 'allRating')
                self.ind += 1
                self.send_message(f"{choice(CORRECTLY)} ✅\nРейтинг: {all_rating - self.rating} --> {all_rating}")
                self.get_problem()
                return
            elif self.answer_choice:
                self.answer_choice = False
                if answer == self.ans:
                    db.update_new_values(self.id, [
                        [f'count{mod_names_for_sql[self.solution_mode]}', 1],
                        [f'rating{mod_names_for_sql[self.solution_mode]}', self.rating],
                        ['allRating', self.rating]
                    ])
                    
                    all_rating = db.get_user_attribute(self.id, "allRating")
                    self.ind += 1
                    self.send_message(f"{choice(CORRECTLY)} ✅\nРейтинг: {all_rating - self.rating} --> {all_rating}")
                    self.get_problem()
                    return
                self.send_message(f"Неправильно ❌, ты сможешь вернуться к этому заданию позже")
                self.tr = 0
                self.ind += 1
                self.get_problem()
            else:
                self.tr += 1
                if self.tr == 1:
                    self.send_message(f"Неправильно ❌, попробуй ещё раз")
                else:
                    self.send_message(f"Снова неправильно ❌, ты сможешь вернуться к этому заданию позже")
                    self.tr = 0
                    self.ind += 1
                    self.get_problem()

    def Stop(self):
        if self.adminMode == 100:
            self.send_message("Выберете команду", keyAdmin)
            self.adminMode = -1
            return
        if self.adminMode == -1:
            self.send_message("Хорошо", keyMainForAdmin)
            self.adminMode = -2
            return
        if self.adminMode == 0:
            self.send_message("Выберите команду", keyMainForAdmin)
            self.adminMode = -1
            return
        if self.solution_mode == -1:
            db.update_value(self.id, 'countArif', self.num)
            if self.num == 0:
                self.send_message("Увы, не решено ни одного примера :(", keyMain2)
            elif self.num == 1:
                all_rating = db.get_user_attribute(self.id, 'allRating')
                self.send_message(f"В этот раз решено {self.num} {get_word('пример', self.num)}.\nНеправильно - {self.mistakes_count} {get_word('пример', self.mistakes_count)}.\nПропущено - {self.skips_count} {get_word('пример', self.skips_count)}.\n\nРейтинг: {all_rating - self.num} --> {all_rating}\nМесто: {self.get_position_in_top()}", keyMain2)
            else:
                srTime = abs(round(self.all_time / self.num, 2))
                if srTime != -1:
                    info = db.get_user_info(self.id)
                    srTime = round((info['timeArif'] * (info['countArif'] - self.num) + srTime * self.num) / info['countArif'], 2)
                
                db.set_new_value(self.id, 'timeArif', srTime)
                all_rating = db.get_user_attribute(self.id, 'allRating')
                self.send_message(
                    f"В этот раз решено {self.num} {get_word('пример', self.num)}.\nВ среднем на решение одного примера уходило {srTime} сек.\nНеправильно - {self.mistakes_count} {get_word('пример', self.mistakes_count)}.\nПропущено - {self.skips_count} {get_word('пример', self.skips_count)}.\n\nРейтинг: {all_rating - self.num} --> {all_rating}\nМесто: {self.get_position_in_top()}", keyMain2)
            self.solution_mode = -2
            self.num = 0
            self.last_time = -1
            self.all_time = -1
            self.skips_count = 0
            self.mistakes_count = 0
            self.tr = 0
        # INF
        elif self.solution_mode >= 0:
            all_rating = db.get_user_attribute(self.id, 'allRating')
            if self.old_rating == all_rating:
                self.send_message("Увы, не решено ни одной задачи :(", keyMain2)
            else:
                self.send_message(f"Рейтинг: {self.old_rating} --> {all_rating}\nМесто: {self.get_position_in_top()}", keyMain2)
            self.solution_mode = -2
            self.ind = 0
            self.num = 0
            self.tr = 0
            self.answer_choice = False
        else:
            if self.id not in VK_ADMINS:
                self.send_message(
                    "Привет! Я обучающий чат-бот, созданный для того, чтобы помочь тебе в изучении языка Python!\nНажми кнопку 'Задания', чтобы перейти к решению, или кнопку 'Статистика', чтобы посмотреть сколько уже решено!",
                    keyMain)
                return
            self.send_message("Привет! Я обучающий чат-бот, созданный для того, чтобы помочь тебе в изучении языка Python!\nНажми кнопку 'Задания', чтобы перейти к решению, или кнопку 'Статистика', чтобы посмотреть сколько уже решено!", keyMainForAdmin)

    def get_self_stats(self):
        user_stats = db.get_user_info(self.id)

        stat = "Арифметика:\n"
        count_arif = user_stats['countArif']
        if count_arif != 0:
            stat += f"За всё время решено {count_arif} {get_word('пример', count_arif)} ({count_arif} ☆).\nВ среднем на решение одного примера уходило {user_stats['timeArif']} cек.\n\nОстальные модули:\n"
            if count_arif == 1:
                stat = stat[0:30] + stat[31::]
        else:
            stat += "Модуль арифметики ещё не решался :(\n\nОстальные модули:\n"

        all_count = 0
        all_rating = 0
        for i in mod_names_for_sql:
            if user_stats[f'count{i}'] == 0:
                stat += f"{module_names[mod_names_for_sql.index(i)]} - 0 заданий (0 ☆)\n"
            else:
                stats_count = user_stats[f'count{i}']
                rating_count = user_stats[f'rating{i}']
                all_count +=  user_stats[f'count{i}']
                all_rating += user_stats[f'rating{i}']
                stat += f"{module_names[mod_names_for_sql.index(i)]} - {stats_count} {get_word('заданий', stats_count)} ({rating_count} ☆)\n"

        stat += f"Итого: {all_count} {get_word('заданий', all_count)} ({all_rating} ☆)\n\nВсего: {user_stats['allRating']} ☆\nМесто: {self.get_position_in_top()}"
        self.send_message(stat)

    def get_position_in_top(self):
        return db.get_user_place(self.id)

    def get_users_top(self):
        top = db.get_users_top(10)
        text = ""
        for i in range(len(top)):
            if i == 0:
                text += f"🥇) {top[i]['name']} - {top[i]['allRating']} ☆\n"
            elif i == 1:
                text += f"🥈) {top[i]['name']} - {top[i]['allRating']} ☆\n"
            elif i == 2:
                text += f"🥉) {top[i]['name']} - {top[i]['allRating']} ☆\n"
            else:
                text += f" {i + 1} ) {top[i]['name']} - {top[i]['allRating']} ☆\n"
        self.send_message(text)

    def get_theory(self):
        text = f"Арифметика - {ARTICLES_WITH_THEORY[0]}\n"
        for i in range(5):
            text += f"{module_names[i]} - {ARTICLES_WITH_THEORY[i + 1]}\n"
        self.send_message(text)

    def send_message(self, text, key=0):
        if key == 0:
            vk.method('messages.send', {'user_id': self.id, 'message': text, 'random_id': 0})
            return
        vk.method('messages.send', {'user_id': self.id, 'message': text, 'random_id': 0, 'keyboard': key})

    def send_photo(self, text, attachment, key=0):
        vk.method('messages.send', {'user_id': self.id, 'message': text, 'random_id': 0, 'attachment': attachment, 'keyboard': key})

    def send_document(self, text, ph, key=0):
        upload_url = session.docs.getMessagesUploadServer(type='doc', peer_id=self.id)['upload_url']
        files = {'file': open(ph, 'rb')}
        response = requests.post(upload_url, files=files)
        file_data = response.json()['file']
        saved_file = session.docs.save(file=file_data, title=ph)

        session.messages.send(
            user_id=self.id,
            attachment=f"doc{saved_file['doc']['owner_id']}_{saved_file['doc']['id']}",
            message=text,
            random_id=0
        )
    
def get_username(id):
    data = vk.method("users.get", {"user_ids": id})[0]
    return "{} {}".format(data["first_name"], data["last_name"])


def get_arif_problem(num):
    mode = choice(ver)
    num += 1
    if num == 1:
        x = randint(1, 10)
        y = randint(1, 10)
        z = x + y
        return [f"{x} + {y} = ?", abs(z)]
    if num == 2:
        x = randint(1, 10)
        y = randint(1, 10)
        z = x * y
        return [f"{x} * {y} = ?", abs(z)]
    if num == 3:
        x = randint(1, 20)
        if x % 2 == 0:
            x += 1
        y = 2
        z = x / y
        return [f"{x} / {y} = ?", abs(z)]
    if mode == 1:
        sign = choice([1, 1, 2])
        if sign == 1:
            x = randint(1, min(num * 10, 100))
            y = randint(1, min(num * 10, 100))
            if x > y:
                x, y = y, x
            z = x - y
            return [f"abs({x} - {y}) = ?", abs(z)]
        else:
            x = randint(1, min(num * 10, 100))
            y = randint(1, min(num * 10, 100))
            z = x + y
            return [f"{x} + {y} = ?", abs(z)]
    elif mode == 2:
        x = randint(1, min(20, num * 4))
        y = randint(1, max(x // 7, 10))
        if randint(0, 1):
            x, y = y, x
        z = x * y
        return [f"{x} * {y} = ?", z]
    elif mode == 3:
        sign = choice([0, 1, 1, 2, 2])
        if sign == 0:
            x = randint(1, 100)
            y = choice([2, 4, 5, 8, 10])
            if y == 8 and x % 2:
                x += 1
            elif x % y == 0:
                x += 1
            z = x / y
            return [f"{x} / {y} = ?", z]
        elif sign == 1:
            x = randint(1, 100)
            y = randint(1, x // 2 + 1)
            z = x // y
            return [f"{x} // {y} = ?", z]
        elif sign == 2:
            x = randint(1, 100)
            y = randint(1, x // 2 + 10)
            z = x % y
            return [f"{x} % {y} = ?", z]
    elif mode == 4:
        x = randint(2, 15)
        y = randint(2, 4)
        if x ** y > 200 and x != 0:
            y -= 1
        if x > 10:
            x = 2
        if x == 2:
            y = randint(2, 10)
        z = x ** y
        return [f"{x} ** {y} = ?", z]
    elif mode == 5:
        x = choice([1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256, 361, 400])
        y = 0.5
        z = round(x ** y)
        return [f"{x} ** {y} = ?", z]
    elif mode == 6:
        x = randint(0, 20)
        y = randint(1, 9999)
        if y > 5000:
            y //= 10
        else:
            y = randint(1, 9999)
        z = float(f"{x}.{y}")
        modeRound = randint(0, 1)
        digit = randint(0, len(str(z).split(".")[1]) - 1)
        if modeRound == 0:
            return [f"round({z}) = ?", round(z)]
        if digit == 0:
            digit += 1
        return [f"round({z}, {digit}) = ?", round(z, digit)]


def get_word(word, number):
    if word == 'пример':
        if 10 <= number <= 20:
            return word + "ов"
        if number % 10 == 1:
            return word
        if 2 <= (number % 10) <= 4:
            return word + "a"
        return word + "ов"

    if number % 10 == 0:
        return "заданий"
    if number % 10 == 1 and not 10 <= number <= 20:
        return "задание"
    if number % 10 <= 4 and not 10 <= number <= 20:
        return "задания"
    return "заданий"

def update_problem_indexes():
    for i in users:
        for k in range(cnt):
            users[i].problem_indexes[k] = [j for j in range(1, len(problem_answers[k]) + 1)]

def bot_start():
    print("Бот в ВК запускается...")
    global module_names, problem_text, problem_answers, problem_photos, cnt
    cnt = len(module_names)
    problem_text = [0] * cnt
    problem_answers = [0] * cnt
    problem_photos = [0] * cnt

    # Собираем задания/ответы

    with open('Problems/vk_uploaded_problems.json', 'r') as file:
        uploaded = json.load(file)
    
    is_new_problems = False

    for i in range(cnt):
        file = open(f"{module_names[i]}/answers.txt", "r", encoding='utf-8')
        content = file.read().split("\n")
        problem_answers[i] = content
        file.close()

        file = open(f"{module_names[i]}/problems.txt", "r", encoding='utf-8')
        content = file.read().split("\n")
        problem_text[i] = content
        file.close()
    
        if not uploaded.get(module_names[i]):
            uploaded[module_names[i]] = []
        differences = len(problem_answers[i]) - len(uploaded[module_names[i]])
        if differences > 0:
            is_new_problems = True
            for j in range(len(uploaded[module_names[i]]) + 1, len(problem_answers[i]) + 1):
                print("Новое задание добавлено.")
                try:
                    photo = vk_api.VkUpload(vk).photo_messages(f"{module_names[i]}/quest{j}.png")
                except:
                    sleep(3)
                    photo = vk_api.VkUpload(vk).photo_messages(f"{module_names[i]}/quest{j}.png")
                    
                owner_id = photo[0]['owner_id']
                photo_id = photo[0]['id']
                access_key = photo[0]['access_key']
                uploaded[module_names[i]].append(f'photo{owner_id}_{photo_id}_{access_key}')
        problem_photos[i] = uploaded[module_names[i]]

    if is_new_problems:
        with open('Problems/vk_uploaded_problems.json', 'w') as file:
            json.dump(uploaded, file)

    # Собираем айди из списка
    all_users = db.get_all_platform_users('VK')
    for i in all_users:
        users[int(i['id'])] = User(i)
        
    # Вероятности примеров
    s = 1
    global ver
    ver = []
    for i in prims:
        for j in range(i):
            ver.append(s)
        s += 1

    print("Бот в ВК запущен")

def add(event):
    id = event.user_id

    if not id in users:
        db.add_user(id, get_username(id), 'VK')
        users[id] = User(db.get_user_info(id))
        if id in VK_ADMINS:
            users[id].send_message(
                "Привет! Я обучающий чат-бот, созданный для того, чтобы помочь тебе в изучении языка Python! \nНажми кнопку 'Задания', чтобы перейти к решению, или кнопку 'Статистика', чтобы посмотреть сколько уже решено!",
                keyMainForAdmin)
        else:
            users[id].send_message("Привет! Я обучающий чат-бот, созданный для того, чтобы помочь тебе в изучении языка Python!\nНажми кнопку 'Задания', чтобы перейти к решению, или кнопку 'Статистика', чтобы посмотреть сколько уже решено!", keyMain)

    else:
        if users[id].solution_mode != -2:
            users[id].get_user_answer("ans")
            return
        users[id].send_message("Выбери модуль, по которому хочешь решать задачи.\nЧтобы ознакомиться с теорией, нажми на кнопку 'Теория'", keyMain2)

def save_stats():
    users_stats = db.get_all_platform_users('VK')
    user_stats_json = {}
    
    for user in users_stats:
        user_stats_json[user['id']] = user

    with open("Technical/vk_users_stats.json", 'w') as file:
        json.dump(user_stats_json, file)

def delete_stats(id):
    users[id].send_document("Способ обнулить всю статистику, описывается в файле - Инструкция.txt", 'Инструкция.txt')

def admin_command(text, id):
    global problem

    if text == "Управление ботом":
        users[id].adminMode = -1
        users[id].send_message("Выберите команду", keyAdmin)

    elif text == "Save":
        save_stats()

    elif text == "Reload":
        bot_start()
        users[id].send_message("Перезагрузка завершена")

    elif text == "Добавить задание":
        users[id].send_message("Добавлять новые задания можно только в телеграмм версии: https://t.me/pythonlearners_bot")

    elif text == "Обнуление статистики":
        delete_stats(id)

    elif text == "Таблица пользователей":
        get_users_table(id)
    elif text == "Дать права на добавление заданий":
        users[id].send_document("Способ сделать человека редактором, описывается в файле - Инструкция.txt", 'Инструкция.txt')
    else:
        users[id].send_message(
            "Привет! Я обучающий чат-бот, созданный для того, чтобы помочь тебе в изучении языка Python!\nНажми кнопку 'Задания', чтобы перейти к решению, или кнопку 'Статистика', чтобы посмотреть сколько уже решено!",
            keyMainForAdmin)

def get_button(text, color):
    return {
        "action" : {
            "type" : "text",
            "payload" : "{\"button\" : \"" + "1" + "\"}",
            "label" : f"{text}"
        },
        "color" : f"{color}"
    }


def get_answer_options(vars):
    shuffle(vars)
    if len(vars) == 4:
        keyAns = {
            "one_time": False,
            "buttons": [
                [get_button(vars[0], "primary"), get_button(vars[1], "primary")],
                [get_button(vars[2], "primary"), get_button(vars[3], "primary")],
                [get_button("Назад", 'secondary'), get_button("Пропустить", 'secondary')]
            ]
        }
    elif len(vars) == 3:
        keyAns = {
            "one_time": False,
            "buttons": [
                [get_button(vars[0], "primary")],
                [get_button(vars[1], "primary")],
                [get_button(vars[2], "primary")],
                [get_button("Назад", 'secondary'), get_button("Пропустить", 'secondary')]
            ]
        }
    else:
        keyAns = {
            "one_time": False,
            "buttons": [
                [get_button(vars[0], "primary")],
                [get_button(vars[1], "primary")],
                [get_button("Назад", 'secondary'), get_button("Пропустить", 'secondary')]
            ]
        }
    keyAns = json.dumps(keyAns, ensure_ascii=False).encode('utf-8')
    return str(keyAns.decode("utf-8"))

def adding_check():
    with open('Problems/vk_uploaded_problems.json', 'r') as file:
        uploaded = json.load(file)
    
    is_new_problems = False
    for i in range(cnt):
        file = open(f"{module_names[i]}/answers.txt", "r", encoding='utf-8')
        content = file.read().split("\n")
        problem_answers[i] = content
        file.close()
    
        if not uploaded.get(module_names[i]):
            uploaded[module_names[i]] = []
        differences = len(problem_answers[i]) - len(uploaded[module_names[i]])
        if differences > 0:
            is_new_problems = True
            for j in range(len(uploaded[module_names[i]]) + 1, len(problem_answers[i]) + 1):
                try:
                    photo = vk_api.VkUpload(vk).photo_messages(f"{module_names[i]}/quest{j}.png")
                except:
                    photo = vk_api.VkUpload(vk).photo_messages(f"{module_names[i]}/quest{j}.png")
                    
                owner_id = photo[0]['owner_id']
                photo_id = photo[0]['id']
                access_key = photo[0]['access_key']
                uploaded[module_names[i]].append(f'photo{owner_id}_{photo_id}_{access_key}')
        problem_photos[i] = uploaded[module_names[i]]

    if is_new_problems:
        with open('Problems/vk_uploaded_problems.json', 'w') as file:
            json.dump(uploaded, file)
        update_problem_indexes()
        print("Новые задания добавлены.")

def get_users_table(id):
    file = open("table.html", 'w')
    masForHTML = []
    ratings = []

    all_users = db.get_all_users()
    all_users.sort(key=lambda x: x['allRating'], reverse=True)


    for i in all_users:
        ratings.append(i['allRating'])
    
    for user in all_users:

        rank = ratings.index(user['allRating']) + 1
        count = ratings.count(user['allRating'])
        rang1, rang2 = rank, rank + count - 1
        color = 'black'

        if user['platform'] == 'TG':
            color = 'rgb(35, 0, 149)'

        if rang1 == rang2:
            rang = str(rang1)
        else:
            rang = f"{rang1}-{rang2}"

        user_name = re.sub(r'[^А-яA-z0-9() ]', '', user['name'])

        masForHTML.append([user_name, user['countArif'], user['ratingP'], user['ratingU'],
                            user['ratingC'], user['ratingM'], user['ratingF'],
                            user['allRating'], rang, color])

    file.write(template.render(my_array=masForHTML))
    file.close()


    myZip = zipfile.ZipFile("table.zip", 'w')
    myZip.write('table.html')
    myZip.close()
    
    users[id].send_document("В архиве содержится файл со статистикой пользователей. (Если в таблице проблемы с отображением русских букв, рекомендуется получать таблицу через телеграмм версию)", 'table.zip')
    os.remove("table.zip")
    os.remove("table.html")

keyMain = {
        "one_time": False,
        "buttons": [
            [get_button("Задания", 'primary'), get_button("Статистика", 'primary'), get_button("Информация", 'primary')]
        ]
    }
keyMain = json.dumps(keyMain, ensure_ascii=False).encode('utf-8')
keyMain = str(keyMain.decode("utf-8"))

keyMainForAdmin = {
        "one_time": False,
        "buttons": [
            [get_button("Задания", 'primary'), get_button("Статистика", 'primary'), get_button("Информация", 'primary')],
            [get_button("Управление ботом", 'secondary')]
        ]
    }
keyMainForAdmin = json.dumps(keyMainForAdmin, ensure_ascii=False).encode('utf-8')
keyMainForAdmin = str(keyMainForAdmin.decode("utf-8"))

keyMain2 = {
        "one_time": False,
        "buttons": [
            [get_button('Арифметика', 'primary'), get_button('Переменные', 'primary'), get_button('Условия', 'primary')],
            [get_button('Циклы', 'primary'), get_button('Массивы', 'primary'), get_button('Функции', 'primary')],
            [get_button('Назад', 'secondary'), get_button("Топ 🏆", "secondary"), get_button("Теория", "secondary")]
        ]
    }
keyMain2 = json.dumps(keyMain2, ensure_ascii=False).encode('utf-8')
keyMain2 = str(keyMain2.decode("utf-8"))


keyInf2 = {
        "one_time": False,
        "buttons": [
            [get_button("Назад", 'primary'), get_button("Пропустить", 'primary')],
        ]
    }
keyInf2 = json.dumps(keyInf2, ensure_ascii=False).encode('utf-8')
keyInf2 = str(keyInf2.decode("utf-8"))

keyAdmin = {
        "one_time": False,
        "buttons": [
            [get_button("Таблица пользователей", 'primary'), get_button("Обнуление статистики", 'negative')],
            [get_button("Добавить задание", 'primary'), get_button("Дать права на добавление заданий", 'primary')],
            [get_button("Назад", 'secondary')]
        ]
    }
keyAdmin = json.dumps(keyAdmin, ensure_ascii=False).encode('utf-8')
keyAdmin = str(keyAdmin.decode("utf-8"))

keyVar = {
        "one_time": False,
        "buttons": [
            [get_button('Нет', 'primary'), get_button('Да', 'negative')]
        ]
    }
keyVar = json.dumps(keyVar, ensure_ascii=False).encode('utf-8')
keyVar = str(keyVar.decode("utf-8"))

bot_start()

while True:
    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    message_counter += 1
                    if message_counter >= 3:
                        adding_check()
                        save_stats()
                        message_counter = 0

                    id = event.user_id
                    if id not in users:
                        add(event)
                    if event.text == "":
                        continue
                    elif event.text in module_names and users[id].adminMode == -2:
                        users[id].get_user_answer(event.text)
                    elif event.text == "Арифметика" and users[id].solution_mode == -2:
                        users[id].solution_mode = -1
                        users[id].get_problem()
                    elif event.message == "Назад" or event.message == "Отмена":
                        users[id].Stop()
                    elif users[id].solution_mode != -2:
                        users[id].get_user_answer(event.text)
                    elif event.text == "Задания":
                        users[id].send_message(
                            "Выбери модуль, по которому хочешь решать задачи.\nЧтобы ознакомиться с теорией, нажми на кнопку 'Теория'",
                            keyMain2)
                    elif event.text == "Статистика":
                        users[id].get_self_stats()
                    elif event.text == "Теория":
                        users[id].get_theory()
                    elif event.text == "Топ 🏆":
                        users[id].get_users_top()
                    elif event.text == "Информация":
                        users[id].send_message(INFORMATION)
                    else:
                        if id in VK_ADMINS and (event.text in admin_commands or users[id].adminMode != -1):
                            admin_command(event.message, id)
                        else:
                            if id in VK_ADMINS:
                                users[id].send_message("Такой команды не существует", keyMainForAdmin)
                            else:
                                users[id].send_message("Такой команды не существует", keyMain)
                except:
                    log = f"Ошибка у пользователя: https://vk.com/id{event.user_id}\nВремя: {strftime('%H:%M')}\nСообщение: {event.message}"
                    print(sys.exc_info())
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    log += f"\nОшибка {exc_type.__name__} в строке {exc_traceback.tb_lineno}: {exc_value}"
                    users[VK_ADMINS[0]].send_message(log)
    except:
        save_stats()
        print(f"Ошибка соединения в {strftime('%H:%M')}")
        sleep(30)