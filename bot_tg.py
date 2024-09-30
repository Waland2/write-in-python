import json
import re
import telebot
from random import *
from time import *
import sys
import os
from jinja2 import Template
import database as db
from config import *

if TG_TOKEN == '':
    print("Токен для от бота в TG не был найден, TG версия не будет запущена!")
    exit()

bot = telebot.TeleBot(TG_TOKEN)
cnt = -1
problem_answers = []
problem_text = []
problem_photos = []
users = {}
message_counter = 0
ver = []
problem = []
module_names = ["Переменные", "Условия", "Циклы", "Массивы", "Функции"]
mod_names_for_sql = ['P', 'U', 'C', 'M', 'F']
admin_commands = ["Управление ботом", "Save", "Reload", "Добавить задание", "Обнуление статистики", "Таблица пользователей", "Дать права на добавление заданий", "get_user_stats"]
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
                self.send_message(
                    f"В данном модуле требуется выполнение примеров с использованием арифметических операций из языка Python. Количество примеров в модуле не ограничено.\n\nВот твой первый пример: {self.quest}",
                    keyInf2)
                return
            self.send_message(self.quest, keyInf2)
        else:
            if self.ind >= len(problem_text[self.solution_mode]):
                self.ind = 0
                self.problem_indexes[self.solution_mode] = [j for j in range(1, len(problem_answers[self.solution_mode]) + 1)]
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
                self.send_photo(f'№{self.num + 1} ({self.rating} ☆)\n{problem_text[self.solution_mode][self.num]}',
                               problem_photos[self.solution_mode][self.num], keyInf3)
                return
            self.send_photo(f'№{self.num + 1} ({self.rating} ☆)\n{problem_text[self.solution_mode][self.num]}',
                           problem_photos[self.solution_mode][self.num], keyInf2)

    def get_user_answer(self, answer):
        if self.solution_mode == -1:
            if answer == "Пропустить ➡":
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
                if self.num in [5, 10, 20, 30, 40, 50, 100]:
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
            if answer == "Пропустить ➡":
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

        if self.adminMode == -1:
            if self.id in REDACTORS:
                self.send_message("Хорошо", keyMainForRed)
            else:
                self.send_message("Хорошо", keyMainForAdmin)
            self.adminMode = -2
            return
        if self.adminMode == 0:
            if self.id in REDACTORS:
                self.send_message("Хорошо", keyMainForRed)
            else:
                self.send_message("Выберите команду", keyAdmin)
            self.adminMode = -1
            return
        if self.adminMode == 1:
            self.send_message("Выберте модуль, в который хотите добавить новое задание", keyMain1)
            self.adminMode = 0
            return
        if self.adminMode == 2:
            self.adminMode = 1
            os.remove(self.problem[1])
            self.send_message("Пришлите скриншот задания, которое хотите добавить", keyBack)
            return

        if self.adminMode == 4 or self.adminMode == 5:
            self.send_message("У задания будут варианты ответов?", keyVar)
            self.adminMode = 3
            return

        if self.adminMode == 6:
            self.send_message(
                'Пришлите сообщение с вариантами ответов, разделив их двоеточиями. Пример:\nВариант1:Вариант2:Вариант3:Вариант4\nВариант1 - должен быть ПРАВИЛЬНЫМ')
            self.adminMode = 4
            return
        if self.adminMode == 7:
            self.send_message("Пришлите правильный ответ")
            self.adminMode = 5
            return
        if self.adminMode == 100:
            self.send_message("Выберете команду", keyAdmin)
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
                    f"В этот раз решено {self.num} {get_word('пример', self.num)}.\nВ среднем на решение одного примера уходило {srTime} сек.\nНеправильно - {self.mistakes_count} {get_word('пример', self.mistakes_count)}.\nПропущено - {self.skips_count} {get_word('пример', self.skips_count)}.\n\nРейтинг: {all_rating - self.num} --> {all_rating}\nМесто: {self.get_position_in_top()}",
                    keyMain2)
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
            ans = "Привет! Я обучающий чат-бот, созданный для того, чтобы помочь тебе в изучении языка Python!\nНажми кнопку 'Задания', чтобы перейти к решению, или кнопку 'Статистика', чтобы посмотреть сколько уже решено!"
            if self.id in REDACTORS:
                self.send_message(ans, keyMainForRed)
                return

            if self.id not in TG_ADMINS:
                self.send_message(ans, keyMain)
                return
            self.send_message(ans, keyMainForAdmin)

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

    def get_position_in_top(self):
        return db.get_user_place(self.id)

    def get_theory(self):
        text = f"Арифметика - {ARTICLES_WITH_THEORY[0]}\n"
        for i in range(5):
            text += f"{module_names[i]} - {ARTICLES_WITH_THEORY[i + 1]}\n"
        self.send_message(text)

    def send_message(self, text, key=None):
        bot.send_message(self.id, text, reply_markup=key)

    def send_photo(self, text, attachment, key=None):
        bot.send_photo(self.id, open(attachment, 'rb'), caption=text, reply_markup=key)

    def send_document(self, text, ph, key=None):
        if ph.find('.txt') != -1:
            bot.send_document(self.id, open(ph, encoding='UTF-8'), caption=text, reply_markup=key)
            return
        bot.send_document(self.id, open(ph, encoding='UTF-8'), caption=text, reply_markup=key)


def get_username(event):
    first = event.from_user.first_name
    second = event.from_user.last_name
    name = ""
    if not first is None:
        name += first
        if not second is None:
            name += f" {second}"
    else:
        if not second is None:
            name += f"{second}"

    if event.from_user.username is None:
        if first is not None:
            if second is not None:
                return f"{first} {second}"
            return first
        else:
            if second is None:
                return None
            return second
    if name == event.from_user.username:
        return f"{event.from_user.username}"
    return f"{event.from_user.username} ({name})"

def update_problem_indexes():
    for i in users:
        for k in range(cnt):
            users[i].problem_indexes[k] = [j for j in range(1, len(problem_answers[k]) + 1)]

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


def bot_start():
    print("Бот в телеграмме запускается...")
    global module_names, problem_text, problem_answers, problem_photos, cnt

    for i in os.listdir('Problem'):
        os.remove(f"Problem/{i}")

    cnt = len(module_names)
    problem_text = [0] * cnt
    problem_answers = [0] * cnt
    problem_photos = [0] * cnt
    # Собираем задания/ответы
    for i in range(cnt):
        file = open(f"{module_names[i]}/answers.txt", "r", encoding='utf-8')
        content = file.read().split("\n")
        problem_answers[i] = content
        file.close()

        file = open(f"{module_names[i]}/problems.txt", "r", encoding='utf-8')
        content = file.read().split("\n")
        problem_text[i] = content
        file.close()

        mas = []
        for j in range(len(problem_answers[i])):
            mas.append(f"{module_names[i]}/quest{j + 1}.png")
        problem_photos[i] = list(mas)

    # Собираем айди из списка
    all_users = db.get_all_platform_users('TG')
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
    print("Бот в телеграмме запущен")

def add(event):
    id = event.chat.id

    if not id in users:
        db.add_user(id, get_username(event), 'TG')

        users[id] = User(db.get_user_info(id))
        ans = "Привет! Я обучающий чат-бот, созданный для того, чтобы помочь тебе в изучении языка Python! \nНажми кнопку 'Задания', чтобы перейти к решению, или кнопку 'Статистика', чтобы посмотреть сколько уже решено!"
        if id in TG_ADMINS:
            users[id].send_message(ans, keyMainForAdmin)
        elif id in REDACTORS:
            users[id].send_message(ans, keyMainForRed)
        else:
            users[id].send_message(ans, keyMain)
    else:
        if users[id].solution_mode != -2:
            users[id].get_user_answer("ans")
            return
        users[id].send_message(
            "Выбери модуль, по которому хочешь решать задачи.\nЧтобы ознакомиться с теорией, нажми на кнопку 'Теория'",
            keyMain2)


def save_stats():
    users_stats = db.get_all_platform_users('TG')
    user_stats_json = {}
    
    for user in users_stats:
        user_stats_json[user['id']] = user

    with open("Technical/tg_users_stats.json", 'w') as file:
        json.dump(user_stats_json, file)

def delete_stats(id):
    users[id].send_document("Способ обнулить всю статистику, описывается в файле - Инструкция.txt", 'Инструкция.txt')

def add_problem(event, id):
    user = users[id]
    problem = user.problem_info

    if problem['answer_choice']:
        if id in REDACTORS:
            for j in TG_ADMINS:
                message_to_admin = f"Пользователь @{event.from_user.username} добавил новое задание\n\nМодуль: {module_names[problem['module_index']]}\nВопрос: {problem['quest']}\n\nПравильныйВариантОтвета: {problem['answer'][0]}\n"
                for i in range(1, len(problem['answer'])):
                    message_to_admin += f"ВариантОтвета{i + 1}: {problem['answer'][i]}\n"
                users[j].send_photo(message_to_admin, problem['photo'], keyVar2)

        module_name = module_names[problem['module_index']]

        os.rename(problem['photo'], f"{module_name}/quest{len(os.listdir(module_name)) - 1}.png")

        with open(f"{module_name}/answers.txt", 'a', encoding='utf-8') as file_with_answers:
            answer = ""
            for i in problem['answer']:
                answer += f'!{i}'
            answer += " | 2"
            file_with_answers.write(f"\n{answer}")

        with open(f"{module_name}/problems.txt", 'a', encoding='utf-8') as file_with_quests:
            file_with_quests.write(f"\n{problem['quest']}")

        problem_photos[problem['module_index']].append(f"{module_name}/quest{len(os.listdir(module_name)) - 2}.png")
        problem_answers[problem['module_index']].append(answer)
        problem_text[problem['module_index']].append(problem['quest'])
        user.problem_info = {}
        user.adminMode = -1
        if id in REDACTORS:
            users[id].send_message('Задание добавлено!', keyMainForRed)
        else:
            users[id].send_message("Задание добавлено!", keyAdmin)
    else:
        if id in REDACTORS:
            for j in TG_ADMINS:
                message_to_admin = f"Пользователь @{event.from_user.username} добавил новое задание\n\nМодуль: {module_names[problem['module_index']]}\nВопрос: {problem['quest']}\n\nПравильный ответ: {problem['answer']}\n"
                users[j].send_photo(message_to_admin, problem['photo'], keyVar2)

        module_name = module_names[problem['module_index']]

        os.rename(problem['photo'], f"{module_name}/quest{len(os.listdir(module_name)) - 1}.png")

        with open(f"{module_name}/answers.txt", 'a', encoding='utf-8') as file_with_answers:
            answer = problem['answer'] + " | 2"
            file_with_answers.write(f"\n{answer}")

        with open(f"{module_name}/problems.txt", 'a', encoding='utf-8') as file_with_quests:
            file_with_quests.write(f"\n{problem['quest']}")

        problem_photos[problem['module_index']].append(f"{module_name}/quest{len(os.listdir(module_name)) - 2}.png")
        problem_answers[problem['module_index']].append(answer)
        problem_text[problem['module_index']].append(problem['quest'])
        user.problem_info = {}
        user.adminMode = -1
        if id in REDACTORS:
            users[id].send_message('Задание добавлено!', keyMainForRed)
        else:
            users[id].send_message("Задание добавлено!", keyAdmin)
    update_problem_indexes()


def admin_command(text, id, event=None):
    mode = users[id].adminMode
    if mode == 0:
        if text not in module_names:
            users[id].send_message("Введите корректное название модуля", keyMain1)
            return
        users[id].send_message("Пришлите скриншот задания, которое хотите добавить", keyBack)
        users[id].adminMode = 1
        users[id].problem_info['module_index'] = module_names.index(text)

    if mode == 1:
        file_info = bot.get_file(event.photo[-1].file_id)
        download_file = bot.download_file(file_info.file_path)
        src = f"Problem/{event.photo[-1].file_id}.png"
        with open(src, 'wb') as new_file:
            new_file.write(download_file)
        new_file.close()

        users[id].problem_info['photo'] = f"Problem/{event.photo[-1].file_id}.png"
        users[id].adminMode = 2
        users[id].send_message("Пришлите вопрос к заданию", keyBack2)

    if mode == 2:
        users[id].problem_info['quest'] = text
        users[id].adminMode = 3
        users[id].send_message("У задания будут варианты ответов?", keyVar)

    if mode == 3:
        if text == "Да":
            users[id].problem_info['answer_choice'] = True
            users[id].send_message(
                'Пришлите сообщение с вариантами ответов, разделив их двоеточиями. Пример:\nВариант1:Вариант2:Вариант3:Вариант4\nВариант1 - должен быть ПРАВИЛЬНЫМ', keyBack)
            users[id].adminMode = 4
        else:
            users[id].problem_info['answer_choice'] = False
            users[id].adminMode = 5
            users[id].send_message("Пришлите правильный ответ", keyBack)

    if mode == 4:
        try:
            ans = text.split(':')
            if ans[0] == '':
                ans.pop(0)
            if ans[-1] == '':
                ans.pop()
            if len(ans) > 4:
                users[id].send_message("Вариантов ответа может быть не больше четырёх")
            elif len(ans) <= 1:
                users[id].send_message("Вариантов ответа может быть не меньше двух")
            elif text.find('!') != -1:
                users[id].send_message("В вариантах ответа не может быть знака '!'")
            else:
                users[id].problem_info['answer'] = ans
                # users[id].problem.append(ans) # 4
                users[id].adminMode = 6
                textx = f"Модуль: {module_names[users[id].problem_info['module_index']]}\nВопрос: {users[id].problem_info['quest']}\n\nПравильныйВариантОтвета: {users[id].problem_info['answer'][0]}\n"
                for i in range(1, len(users[id].problem_info['answer'])):
                    textx += f"ВариантОтвета{i + 1}: {users[id].problem_info['answer'][i]}\n"
                users[id].send_photo(textx, users[id].problem_info['photo'], keyVar2)
        except:
            users[id].send_message(
                'Пришлите сообщение с вариантами ответов, разделив их двоеточиями. Пример:\nВариант1:Вариант2:Вариант3:Вариант4\nВариант1 - должен быть ПРАВИЛЬНЫМ')

    if mode == 5:
        users[id].problem_info['answer'] = text
        users[id].adminMode = 6
        textx = f"Модуль: {module_names[users[id].problem_info['module_index']]}\nВопрос: {users[id].problem_info['quest']}\n\nПравильный ответ: {users[id].problem_info['answer']}\n"
        users[id].send_photo(textx, users[id].problem_info['photo'], keyVar2)

    if mode == 6:
        if text == 'Добавить✅':
            add_problem(event, id)            
        elif text == 'Отмена❌':
            os.remove(users[id].problem_info['photo'])
            users[id].problem_info = {}
            users[id].adminMode = -1
            if id in REDACTORS:
                users[id].send_message('Выберете команду', keyMainForRed)
                return
            users[id].send_message('Выберете команду', keyAdmin)

    if mode >= 0:
        return

    if id in REDACTORS:
        if text == "Добавить задание":
            users[id].adminMode = 0
            mes = "Выберте модуль, в который хотите добавить новое задание:\n"
            for i in module_names:
                cntX = len(os.listdir(i)) - 2
                mes += f"{i} ({cntX} {get_word('заданий', cntX)})\n"
            users[id].send_message(mes, keyMain1)
            return
        users[id].send_message("Такой команды не существует", keyMainForRed)
        return
    
    if text == "Управление ботом":
        users[id].adminMode = -1
        users[id].send_message("Выберите команду", keyAdmin)

    elif text == "Save":
        save_stats()
        users[id].send_message("Статистика сохранена")

    elif text == "Reload":
        bot_start()
        users[id].send_message("Перезагрузка завершена")

    elif text == "Добавить задание":
        users[id].adminMode = 0
        mes = "Выберте модуль, в который хотите добавить новое задание:\n"
        for i in module_names:
            cntX = len(os.listdir(i)) - 2
            mes += f"{i} ({cntX} {get_word('заданий', cntX)})\n"
        users[id].send_message(mes, keyMain1)
    elif text == "Обнуление статистики":
        delete_stats(id)
    elif text == "Таблица пользователей":
        get_users_table(id)
    elif text == "Дать права на добавление заданий":
        users[id].send_document("Способ сделать человека редактором, описывается в файле - Инструкция.txt", 'Инструкция.txt')
    elif text == "get_user_stats":
        try:
            users[id].send_document("VK", 'Technical/vk_users_stats.json')
        except:
            users[id].send_message("Статистика из ВК не сохранялась")

        try:
            users[id].send_document("TG", 'Technical/tg_users_stats.json')
        except:
            users[id].send_message("Статистика из Телеграмма не сохранялась")

    else:
        if id in REDACTORS:
            users[id].send_message("Такой команды не существует", keyMainForRed)
            return
        users[id].send_message("Такой команды не существует", keyMainForAdmin)

def get_answer_options(vars):
    shuffle(vars)
    if len(vars) == 4:
        keyAns = telebot.types.ReplyKeyboardMarkup()
        keyAns.resize_keyboard = True
        keyAns.row(vars[0], vars[1])
        keyAns.row(vars[2], vars[3])
    elif len(vars) == 3:
        keyAns = telebot.types.ReplyKeyboardMarkup()
        keyAns.resize_keyboard = True
        keyAns.row(vars[0])
        keyAns.row(vars[1])
        keyAns.row(vars[2])
    else:
        keyAns = telebot.types.ReplyKeyboardMarkup()
        keyAns.resize_keyboard = True
        keyAns.row(vars[0])
        keyAns.row(vars[1])

    keyAns.row("⬅ Назад", "Пропустить ➡")
    return keyAns


def get_users_table(id):
    file = open("table.html", 'w', encoding='utf-8')
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

    users[id].send_document("В файле таблица со статистикой пользователей", 'table.html')
    os.remove("table.html")


keyMain = telebot.types.ReplyKeyboardMarkup()
keyMain.resize_keyboard = True
keyMain.row('Задания', 'Статистика', 'Информация')

keyMainForAdmin = telebot.types.ReplyKeyboardMarkup()
keyMainForAdmin.resize_keyboard = True
keyMainForAdmin.row('Задания', 'Статистика', 'Информация')
keyMainForAdmin.row('Управление ботом')

keyMainForRed = telebot.types.ReplyKeyboardMarkup()
keyMainForRed.resize_keyboard = True
keyMainForRed.row('Задания', 'Статистика', 'Информация')
keyMainForRed.row('Добавить задание')

keyMain2 = telebot.types.ReplyKeyboardMarkup()
keyMain2.resize_keyboard = True
keyMain2.row('Арифметика', 'Переменные', 'Условия')
keyMain2.row('Циклы', 'Массивы', 'Функции')
keyMain2.row('⬅ Назад', "Топ 🏆", 'Теория 📖')

keyInf2 = telebot.types.ReplyKeyboardMarkup()
keyInf2.resize_keyboard = True
keyInf2.row('⬅ Назад', 'Пропустить ➡')

keyAdmin = telebot.types.ReplyKeyboardMarkup()
keyAdmin.resize_keyboard = True
keyAdmin.row("Таблица пользователей", "Обнуление статистики")
keyAdmin.row("Добавить задание", "Дать права на добавление заданий")
keyAdmin.row('⬅ Назад')

keyMain1 = telebot.types.ReplyKeyboardMarkup()
keyMain1.resize_keyboard = True
keyMain1.one_time_keyboard = True
keyMain1.row('Переменные', 'Условия', 'Циклы')
keyMain1.row('Массивы', 'Функции', 'Отмена')

keyVar = telebot.types.ReplyKeyboardMarkup()
keyVar.resize_keyboard = True
keyVar.row('Нет', 'Да')

keyVar2 = telebot.types.ReplyKeyboardMarkup()
keyVar2.resize_keyboard = True
keyVar2.row('Отмена❌', 'Добавить✅')
keyVar2.row("⬅ Назад")

keyBack = telebot.types.ReplyKeyboardMarkup()
keyBack.resize_keyboard = True
keyBack.row('⬅ Назад')

keyBack2 = telebot.types.ReplyKeyboardMarkup()
keyBack2.resize_keyboard = True
keyBack2.row('Что программа выведет на экран?', 'Что делает программа?')
keyBack2.row('⬅ Назад')

bot_start()

@bot.message_handler(commands=['start'])
def startMessage(event):
    add(event)

@bot.message_handler(content_types=['text'])
def get_message(event):
    global message_counter
    id = event.from_user.id

    message_counter += 1
    if message_counter >= 100:
        save_stats()
        message_counter = 0

    if id not in users:
        add(event)
    elif event.text in module_names and users[id].adminMode == -2:
        users[id].get_user_answer(event.text)
    elif event.text == "Арифметика" and users[id].solution_mode == -2:
        users[id].solution_mode = -1
        users[id].get_problem()
    elif event.text == "⬅ Назад" or event.text == "Отмена":
        users[id].Stop()
    elif users[id].solution_mode != -2:
        users[id].get_user_answer(event.text)
    elif event.text == "Задания":
        users[id].send_message(
            "Выбери модуль, по которому хочешь решать задачи.\nЧтобы ознакомиться с теорией, нажми на кнопку 'Теория'",
            keyMain2)
    elif event.text == "Статистика":
        users[id].get_self_stats()
    elif event.text == "Теория 📖":
        users[id].get_theory()
    elif event.text == "Топ 🏆":
        users[id].get_users_top()
    elif event.text == "Информация":
        users[id].send_message(INFORMATION)
    else:
        if (id in TG_ADMINS or id in REDACTORS) and (event.text in admin_commands or users[id].adminMode != -1):
            admin_command(event.text, id, event)
        else:
            ans = "Такой команды не существует"
            if id in TG_ADMINS:
                users[id].send_message(ans, keyMainForAdmin)
            elif id in REDACTORS:
                users[id].send_message(ans, keyMainForRed)
            else:
                users[id].send_message(ans, keyMain)

@bot.message_handler(content_types=['photo'])
def get_photo(event):
    id = event.from_user.id
    if (id in TG_ADMINS or id in REDACTORS) and users[id].adminMode == 1:
        admin_command(event.caption, id, event)
        return
    if id not in users:
        add(event)

@bot.message_handler(content_types=['sticker'])
def get_sticker(event):
    id = event.from_user.id
    if id not in users:
        add(event)

bot.infinity_polling()