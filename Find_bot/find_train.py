#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
import psycopg2.extras
import psycopg2
import telebot
from telegramcalendar import create_calendar
import requests
from bs4 import BeautifulSoup
from telebot import types
from threadparser import ParserRoute
from threadparser import ParserTrains
from datetime import datetime
import pytz

bot = telebot.TeleBot('1042859480:AAPRPvs-rQhomoAlAvLh2gLSKUyhgwlhuwU')

#print("Hello")
con = psycopg2.connect(user="postgres_user", password="1", host="127.0.0.1", port="5432", database="my_postgres_db")
con.autocommit = True
cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)


#region Variables
my_id = 442618563
my_timezone = 'Europe/Kiev'
warn_schedule = {} #
info_schedule = {} #
menu = {} #
choice = {} #
path = {} #
flag = {} #
selected_date = {} #
route = {} #
station1 = {} #
station2 = {} #
trains = {} #
current_menu = {} #
threads = {} #
info_train = {} #
warn_train = {} #
current_shown_dates = {}
admin_ask = {} #
is_admin = {} #
to_send = {} #
users_to_send = {} #
is_started = {}
is_feedback = {}
locations = ['Днепропетровск-Глав.', '193 Км Остановочный Пункт', 'Нижнеднепровск',
             '196 Км Остановочный Пункт', 'Н.д.узел-парк Л.з', 'Н.д.узел-парк Е.г',
             'Ксеньевка', 'Игрень', '207 Км Остановочный Пункт', '212 Км Остановочный Пункт',
             'Илларионово', '219 Км Остановочный Пункт', '222 Км Остановочный Пункт',
             '225 Км Остановочный Пункт', 'Хорошево,Днепропетровская обл.', '230 Км Остановочный Пункт',
             '235 Км Остановочный Пункт', 'Синельниково-2', 'Синельниково-1']
translit = {'Днепропетровск-Глав.': 'dnepropetrovsk-glav',
            '193 Км Остановочный Пункт': '193-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            'Нижнеднепровск': 'nizhnedneprovsk',
            '196 Км Остановочный Пункт': '196-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            'Н.д.узел-парк Л.з': 'nduzel-park-lz',
            'Н.д.узел-парк Е.г': 'nduzel-park-eg',
            'Ксеньевка': 'ksenevka',
            'Игрень': 'igren',
            '207 Км Остановочный Пункт': '207-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            '212 Км Остановочный Пункт': '212-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            'Илларионово': 'illarionovo',
            '219 Км Остановочный Пункт': '219-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            '222 Км Остановочный Пункт': '222-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            '225 Км Остановочный Пункт': '225-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            'Хорошево,Днепропетровская обл.': 'horoshevo,dnepropetrovskaya-obl',
            '230 Км Остановочный Пункт': '230-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            '235 Км Остановочный Пункт': '235-km-ostanovochnyj-punkt,dnepropetrovskaya-obl',
            'Синельниково-2': 'sinelnikovo-2',
            'Синельниково-1': 'sinelnikovo-1'}
#endregion


def new_menu(chat_id):
    global route
    var = types.ReplyKeyboardMarkup(resize_keyboard=True)
    var.add(types.KeyboardButton(station1[chat_id] + ' - ' + station2[chat_id]))
    var.add(types.KeyboardButton("Пункт отправления"), types.KeyboardButton("Пункт прибытия"))
    # var.add(types.KeyboardButton("Пункт прибытия"))
    var.add(types.KeyboardButton("Выбрать дату"), types.KeyboardButton("Перезапустить"))
    # var.add(types.KeyboardButton("Сброс"))
    route[chat_id] = station1[chat_id] + ' - ' + station2[chat_id]
    current_menu[chat_id] = var
    current_menu_buttons = buttons_keyboard(current_menu[chat_id])
    cur.execute("UPDATE variables SET current_menu = %s WHERE id = %s", (current_menu_buttons, chat_id))
    return var


def insert_variables(chat_id):
    try:
        s = "INSERT INTO variables(id, menu, current_menu, choice, selected_date, route, station1, station2, " + "trains, threads, path, flag, admin_ask, is_admin, to_send, users_to_send, info_schedule, warn_schedule, "+                    "info_train, warn_train) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "+                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        init_menu = ['Пункт отправления', 'Пункт прибытия', 'Выбрать дату', 'Перезапустить']
        init_current_menu = init_menu
        cur.execute(s, (chat_id, init_menu, init_current_menu, [], "", "", "", "", [], [], 0, 1, False, 
                        False, 0, [], "", "", "", ""))
    except psycopg2.errors.UniqueViolation as err:
        #update_variables(message.chat.id)
        global my_id
        with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
            my_id = file.read()
            bot.send_message(my_id, 'insert_variables(chat_id)\n' + 'id = ' + str(message.chat.id) + '\n' + str(ex))
            bot.reply_to(message, u"\U0001F614 " + "Произошел сбой. Информация об ошибке отправлена разработчику, " + 
                         "ошибка будет исправлена в ближайшее время. Извините за неудобства")
    # con.commit()


def check_started(message):
    if message.chat.id not in is_started:
        bot.send_message(message.chat.id, u'\U0001f503 ' + "Бот был перезапущен. Пожалуйста, выполните команду /start " + 
                        "для корректного продолжения работы. Ваши прежние настройки сохранились " + u'\U0001f60a')
        return False
    return True

    
def update_last_time(message):
    cur.execute("UPDATE users SET last_time = TIMESTAMP %s WHERE chat_id = %s", (datetime.now(pytz.timezone(my_timezone)), 
                                                                          message.chat.id))
    
def is_in_variables(chat_id):
    cur.execute("SELECT * FROM variables WHERE id = %s", (chat_id, ))
    if cur.fetchone() is not None:
        return True
    return False


def get_threads(threads_list):
    threads_name = []
    for tmp in threads_list:
        threads_name.append(tmp)
    return threads_name

    
def buttons_keyboard(keys):
    btn_list = []
    for tmp in keys.keyboard:
        for item in tmp:
            btn_list.append(item['text'])
    return btn_list


def get_user(i, user):
    d1 = user['init_date']
    d2 = user['last_time']
    time_format = "%d.%m.%Y в %H:%M:%S"
    s = str(i) + ". " + str(user['chat_id']) + ", " + user['first_name']
    if user['last_name'] is not None:
        s += " " + user['last_name']    
    if user['username'] is not None:
        s += ", @" + user['username']
    
    if d1 is not None:
        s += "\nСтартовал: " + d1.strftime(time_format)
    if d2 is not None:
        s += "\nПоследнее действие: " + d2.strftime(time_format)
    return s

    
def upload_variables(chat_id):
    global menu, current_menu, choice, selected_date, route, station1, station2, trains, threads, path, flag, admin_ask
    global is_admin, to_send, users_to_send, info_schedule, warn_schedule, info_train, warn_train
    
    s = "UPDATE variables " +        "SET menu = %s, current_menu = %s, choice = %s, selected_date = %s, route = %s, station1 = %s, " +        "station2 = %s, trains = %s, path = %s, flag = %s, admin_ask = %s, is_admin = %s, to_send = %s, " +        "users_to_send = %s, info_schedule = %s, warn_schedule = %s, info_train = %s, warn_train = %s " +        "WHERE id = %s;"
    
    menu_buttons = buttons_keyboard(menu[chat_id])
    current_menu_buttons = buttons_keyboard(current_menu[chat_id])
    choice_buttons = buttons_keyboard(choice[chat_id])
    
            
    cur.execute(s, (menu_buttons, current_menu_buttons, choice_buttons, selected_date[chat_id], route[chat_id],
                    station1[chat_id], station2[chat_id], trains[chat_id], path[chat_id], flag[chat_id],
                    admin_ask[chat_id], is_admin[chat_id], to_send[chat_id], users_to_send[chat_id], info_schedule[chat_id],
                    warn_schedule[chat_id], info_train[chat_id], warn_train[chat_id], 
                    chat_id))

def update_variables(chat_id):
    global menu, current_menu, choice, selected_date, route, station1, station2, trains, threads, path, flag, admin_ask
    global is_admin, to_send, users_to_send, info_schedule, warn_schedule, info_train, warn_train
    cur.execute("SELECT * FROM variables WHERE id = %s", (chat_id, ))
    row = cur.fetchone()
    if row is not None:
        menu_buttons = row['menu']
        current_menu_buttons = row['current_menu']
        choice_buttons = row['choice']
        selected_date[chat_id] = row['selected_date']
        route[chat_id] = row['route']
        station1[chat_id] = row['station1']
        station2[chat_id] = row['station2']
        trains[chat_id] = row['trains']
        # threads[chat_id] = row['threads']
        path[chat_id] = row['path']
        flag[chat_id] = row['flag']
        admin_ask[chat_id] = row['admin_ask']
        is_admin[chat_id] = row['is_admin']
        to_send[chat_id] = row['to_send']
        users_to_send[chat_id] = row['users_to_send']
        info_schedule[chat_id] = row['info_schedule']
        warn_schedule[chat_id] = row['warn_schedule']
        info_train[chat_id] = row['info_train']
        warn_train[chat_id] = row['warn_train']
        menu[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if len(menu_buttons) == 4:
            menu[chat_id].add(types.KeyboardButton(menu_buttons[0]), types.KeyboardButton(menu_buttons[1]))
            menu[chat_id].add(types.KeyboardButton(menu_buttons[2]), types.KeyboardButton(menu_buttons[3]))
        elif len(menu_buttons) == 5:
            menu[chat_id].add(types.KeyboardButton(menu_buttons[0]))
            menu[chat_id].add(types.KeyboardButton(menu_buttons[1]), types.KeyboardButton(menu_buttons[2]))
            menu[chat_id].add(types.KeyboardButton(menu_buttons[3]), types.KeyboardButton(menu_buttons[4]))
        choice[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if len(choice_buttons) != 0:
            choice[chat_id].add(types.KeyboardButton(choice_buttons[0]))
            choice_buttons = choice_buttons[1:]
            for i in range(0, len(choice_buttons)):
                if i == len(choice_buttons) - 1:
                    choice[chat_id].add(types.KeyboardButton(choice_buttons[i]))
                    break
                if i % 2 == 0:
                    s1 = choice_buttons[i]
                    if i == len(locations):
                        choice[chat_id].add(types.KeyboardButton(choice_buttons[i]))
                else:
                    choice[chat_id].add(types.KeyboardButton(s1), types.KeyboardButton(choice_buttons[i]))
        current_menu[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if len(current_menu_buttons) == 4:
            current_menu[chat_id].add(types.KeyboardButton(current_menu_buttons[0]), 
                                      types.KeyboardButton(current_menu_buttons[1]))
            current_menu[chat_id].add(types.KeyboardButton(current_menu_buttons[2]), types.KeyboardButton(current_menu_buttons[3]))
        elif len(current_menu_buttons) == 5:
            current_menu[chat_id].add(types.KeyboardButton(current_menu_buttons[0]))
            current_menu[chat_id].add(types.KeyboardButton(current_menu_buttons[1]), 
                                      types.KeyboardButton(current_menu_buttons[2]))
            current_menu[chat_id].add(types.KeyboardButton(current_menu_buttons[3]), 
                                      types.KeyboardButton(current_menu_buttons[4]))
    return True
            

#region Admin
@bot.message_handler(commands=['start', 'help', 'feedback', 'admin', 'exit', 'users', 'send'])
def get_text_messages(message):
    if message.text == '/start':
        global path, flag, menu, choice, current_menu, selected_date, route, station1, station2, trains, con, cur, to_send
        chat_id = message.chat.id
        cur.execute("SELECT * from users WHERE chat_id = %s", (str(chat_id),))
        rows = cur.fetchall()
        if len(rows) == 0:
            cur.execute("INSERT INTO users(chat_id, first_name, last_name, username, init_date, last_time) " + 
                        "VALUES(%s, %s, %s, %s, TIMESTAMP %s, TIMESTAMP %s)", (chat_id, message.chat.first_name, message.chat.last_name, 
                                                                               message.chat.username, 
                                                                               datetime.now(pytz.timezone(my_timezone)),
                                                                               datetime.now(pytz.timezone(my_timezone))))
            # s = "INSERT INTO variables(id, route, path, flag, selected_date, menu, choice, station1, station2, " +\
            #    "admin_ask, is_admin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            insert_variables(chat_id)
            bot.send_message(chat_id, "Приятно познакомиться, " + ("@" + message.chat.username + u" \U0001F609"
                                                                 if (message.chat.username is not None)
                                                                 else (message.chat.first_name +
                                                                 (" " + message.chat.last_name + u" \U0001F609")
                                                                 if (message.chat.last_name is not None) else u" \U0001F609")))
        else:
            cur.execute("UPDATE users SET first_name = %s, last_name = %s, username = %s, init_date = TIMESTAMP %s WHERE chat_id = %s", 
                        (message.chat.first_name, message.chat.last_name, message.chat.username, datetime.now(pytz.timezone(my_timezone)), message.chat.id))
            if not is_in_variables(message.chat.id):
                insert_variables(chat_id)
            update_variables(message.chat.id)
            if admin_ask[message.chat.id]:
                admin_ask[message.chat.id] = False
                cur.execute("UPDATE variables SET admin_ask = %s WHERE id = %s", (admin_ask[message.chat.id],
                                                                                 message.chat.id))
            if is_admin[message.chat.id]:
                bot.reply_to(message, "Вы вышли из режима администратора")
                is_admin[message.chat.id] = False
                cur.execute("UPDATE variables SET is_admin = %s WHERE id = %s", (is_admin[message.chat.id],
                                                                                 message.chat.id))
            if message.chat.id in is_feedback:
                del is_feedback[message.chat.id]
            # con.commit()
            bot.send_message(chat_id, "Снова здравствуйте, " + ("@" + message.chat.username + u" \U0001F609"
                                                                 if (message.chat.username is not None)
                                                                 else (message.chat.first_name +
                                                                 (" " + message.chat.last_name + u" \U0001F609")
                                                                 if (message.chat.last_name is not None) else u" \U0001F609")))
        
        update_last_time(message)
        is_started[message.chat.id] = True
        main_function(message)
    elif message.text == '/help':
        if not check_started(message):
            return
        if admin_ask[message.chat.id]:
            admin_ask[message.chat.id] = False
            cur.execute("UPDATE variables SET admin_ask = %s WHERE id = %s", (admin_ask[message.chat.id],
                                                                              message.chat.id))
            bot.reply_to(message, u"\u26D4 " + "Неверный пароль, запрос отклонен!")
            return
        if message.chat.id in is_feedback:
            del is_feedback[message.chat.id] 
        update_last_time(message)
        bot.send_message(message.chat.id, u'\U0001f4dd ' + 'Бот "Расписание электричек" предназначен для быстрого и удобного ' +
                         'поиска нужного пригородного поезда по заданному маршруту и дате.\n' + u'\U0001f4ca Все данные ' + 
                         'актуальны и обновляются (poezdato.net), но желательно перепроверять информацию ' +
                         'на местных вокзалах, так как изменения могли не успеть занести в систему.' + 
                         '\n' + u'\U0001F4F2 Все взаимодействия с ботом сводятся к нажатию на соответствующие кнопи. ' + 
                         'После того как Вы выберите два крайних пункта вашего маршрута, ' + 
                         'он появится сверху вашего меню и Вы, нажав на него, получите список поездов по вашему запросу. ' + 
                         'Также можно посмотреть детальную информацию о рейсах (по номеру электрички)')
    elif message.text == '/feedback':
        if not check_started(message):
            return
        if admin_ask[message.chat.id]:
            admin_ask[message.chat.id] = False
            bot.reply_to(message, u"\u26D4 " + "Неверный пароль, запрос отклонен!")
            cur.execute("UPDATE variables SET admin_ask = %s WHERE id = %s", (admin_ask[message.chat.id],
                                                                              message.chat.id))
            return
        if is_admin[message.chat.id]:
            bot.reply_to(message, 'Вы в режиме администратора ("/exit" - выйти в обычный режим)')
            return
        bot.send_message(message.chat.id, u"\U0001F4AC " + "Пожалуйста, напишите свой отзыв или пожелание одним сообщением (/q - отменить)")
        is_feedback[message.chat.id] = True
    elif message.text == '/admin':
        if not check_started(message):
            return
        if admin_ask[message.chat.id]:
            admin_ask[message.chat.id] = False
        if message.chat.id in is_feedback:
            del is_feedback[message.chat.id] 
        #update_variables(message.chat.id)
        if is_admin[message.chat.id]:
            bot.reply_to(message, 'Вы уже в режиме администратора ("/exit" - выйти в обычный режим)')
        else:
            bot.reply_to(message, u"\U0001F510" + " Введите пароль")
            admin_ask[message.chat.id] = True
        update_last_time(message)
        cur.execute("UPDATE variables SET admin_ask = %s WHERE id = %s", (admin_ask[message.chat.id], message.chat.id))
    elif message.text == '/exit':
        if not check_started(message):
            return
        if admin_ask[message.chat.id]:
            admin_ask[message.chat.id] = False
            bot.reply_to(message, u"\u26D4 " + "Неверный пароль, запрос отклонен!")
            cur.execute("UPDATE variables SET admin_ask = %s WHERE id = %s", (admin_ask[message.chat.id],
                                                                              message.chat.id))
            return
        if message.chat.id in is_feedback:
            del is_feedback[message.chat.id] 
        
        update_last_time(message)
        admin_ask[message.chat.id] = False
        is_admin[message.chat.id] = False
        bot.reply_to(message, "Режим администратора отключен")
        cur.execute("UPDATE variables SET admin_ask = %s, is_admin = %s WHERE id = %s", 
                    (admin_ask[message.chat.id], is_admin[message.chat.id], message.chat.id))
    elif message.text == '/users':
        if not check_started(message):
            return
        if admin_ask[message.chat.id]:
            admin_ask[message.chat.id] = False
            bot.reply_to(message, u"\u26D4 " + "Неверный пароль, запрос отклонен!")
            cur.execute("UPDATE variables SET admin_ask = %s WHERE id = %s", (admin_ask[message.chat.id],
                                                                              message.chat.id))
            return
        if message.chat.id in is_feedback:
            del is_feedback[message.chat.id] 
        #update_variables(message.chat.id)
        update_last_time(message)
        if is_admin[message.chat.id]:
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()
            s = ""
            i = 1
            for item in users:
                s += get_user(i, item) + "\n\n"
                i += 1
            bot.reply_to(message, s)
    elif message.text.startswith('/send'):
        if not check_started(message):
            return
        if admin_ask[message.chat.id]:
            admin_ask[message.chat.id] = False
            bot.reply_to(message, u"\u26D4 " + "Неверный пароль, запрос отклонен!")
            cur.execute("UPDATE variables SET admin_ask = %s WHERE id = %s", (admin_ask[message.chat.id],
                                                                              message.chat.id))
            return
        if message.chat.id in is_feedback:
            del is_feedback[message.chat.id] 
        try:
            #update_variables(message.chat.id)
            update_last_time(message)
            if is_admin[message.chat.id]:
                to_send[message.chat.id] = 1
                string = message.text.split('/send')
                cur.execute("SELECT * FROM users")
                list_users = cur.fetchall()
                users_to_send[message.chat.id] = []
                if len(string) == 2 and string[1] != "":
                    for item in string[1].strip().split(' '):
                        if int(item.replace(' ', '')) <= len(list_users):
                            users_to_send[message.chat.id].append(list_users[int(item.replace(' ', '')) - 1][0])
                    # print(users_to_send[message.chat.id])
                elif len(string) == 2:
                    for user in list_users:
                        users_to_send[message.chat.id].append(user[0])
                bot.reply_to(message, 'Режим рассылки сообщений включен. Набирайте сообщения ниже (/q - отменить)')
                cur.execute("UPDATE variables SET to_send = %s, users_to_send = %s WHERE id = %s", 
                            (to_send[message.chat.id], users_to_send[message.chat.id], message.chat.id))
        except Exception as ex:
            global my_id
            with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
                my_id = file.read()
                bot.send_message(my_id, '/send\n' + 'id = ' + str(message.chat.id) + '\n' + str(ex))
            bot.reply_to(message, u"\U0001F614 " + "Произошел сбой. Информация об ошибке отправлена разработчику, " + 
                         "ошибка будет исправлена в ближайшее время. Извините за неудобства")
            

def check(chat_id):
    try:
        return chat_id in admin_ask and admin_ask[chat_id]
    except Exception as ex:
        global my_id
        with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
            my_id = file.read()
            bot.send_message(my_id, 'check(message)\n' + 'id = ' + str(chat_id) + '\n' + str(ex))
        bot.send_message(chat_id, u"\U0001F614 " + "Произошел сбой. Я отослал информацию разработчику, " + 
                         "ошибка будет исправлена в ближайшее время. Извините за неудобства")
            
            
@bot.message_handler(func=lambda message: check(message.chat.id))
def get_text_messages(message):
    #update_variables(message.chat.id)
    if not check_started(message):
        return
    chat_id = message.chat.id
    if message.text != "password":
        admin_ask[chat_id] = False
        bot.reply_to(message, u"\u26D4 " + "Неверный пароль!")
    else:
        bot.send_message(chat_id, u"\U0001F513" + " Режим администратора включен")
        is_admin[chat_id] = True
        admin_ask[chat_id] = False
    update_last_time(message)
    cur.execute("UPDATE variables SET admin_ask = %s, is_admin = %s WHERE id = %s", (admin_ask[chat_id], is_admin[chat_id],
                                                                                    chat_id))
    
@bot.message_handler(func=lambda message: message.chat.id in is_feedback)
def get_text_messages(message):
    bot.send_message(message.chat.id, u"\u263A " + "Спасибо за отзыв")
    global my_id
    with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
        my_id = file.read()
        bot.send_message(my_id, "Отзыв от " + str(message.chat.id) + ", " + message.chat.first_name + " " + 
                        (message.chat.last_name if message.chat.last_name is not None else "") +
                        (", @" + message.chat.username if message.chat.username is not None else "") + ":\n\n" + 
                        (message.text))
    del is_feedback[message.chat.id]
    update_last_time(message)
    
    
@bot.message_handler(commands=["q"])
def get_text_messages(message):
    if not check_started(message):
        return
    #update_variables(message.chat.id)
    if to_send[message.chat.id] == 1:
        to_send[message.chat.id] = 0
        cur.execute("UPDATE variables SET to_send = %s WHERE id = %s", (to_send[message.chat.id], message.chat.id))
        bot.reply_to(message, 'Режим рассылки сообщений выключен')
    elif message.chat.id in is_feedback:
        del is_feedback[message.chat.id]
        bot.send_message(message.chat.id, u"\u274C " + "Отменил")
        # TODO
    update_last_time(message)
    

def check_1(message):
    try:
        A = message.chat.id in to_send and to_send[message.chat.id] == 1
        B = message.chat.id in is_admin and is_admin[message.chat.id]
        return A and B
    except Exception as ex:
        global my_id
        with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
            my_id = file.read()
            bot.send_message(my_id, 'check(message)\n' + 'id = ' + str(message.chat.id) + '\n' + str(ex))
        bot.reply_to(message, u"\U0001F614 " + "Произошел сбой. Я отослал информацию разработчику, " + 
                     "ошибка будет исправлена в ближайшее время. Извините за неудобства")
    

@bot.message_handler(func=lambda message: check_1(message))
def get_text_messages(message):
    #update_variables(message.chat.id)
    if not check_started(message):
        return
    cur.execute("SELECT * FROM users")
    all_users = cur.fetchall()
    global my_id
    if len(users_to_send[message.chat.id]) != 0:
        for user in users_to_send[message.chat.id]:
            try:
                bot.send_message(int(user), message.text)
            except telebot.apihelper.ApiException as ex:
                if "bot was blocked by the user" in str(ex):
                    cur.execute("DELETE FROM users WHERE chat_id = %s", (int(user), ))
                    cur.execute("DELETE FROM variables WHERE id = %s", (int(user), ))
                    # con.commit()
                    name = "неизвестный"
                    for row in all_users:
                        if row[0] == int(user):
                            name = row[1] + " " + (row[2] if row[2] is not None else "")
                            name += (" (@" + row[3] + ")" if row[3] is not None else "")
                    users_to_send[message.chat.id].remove(user)
                    cur.execute("UPDATE variables SET users_to_send = %s WHERE id = %s", (users_to_send[message.chat.id], message.chat.id))
                    bot.reply_to(message, "Пользователь " + name + " отключил бота и не смог получить сообщение")
                    if len(users_to_send[message.chat.id]) == 0:
                        bot.reply_to(message, "Список пользователей для отправки сообщений кончился. Передача отменена")
                        to_send[message.chat.id] = 0
                else:
                    with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
                        my_id = file.read()
                        bot.send_message(my_id, 'func=check_1(1)\n' + 'id = ' + str(message.chat.id) + '\n' + str(ex))
                    bot.reply_to(message, u"\U0001F614 " + "Произошел сбой. Я отослал информацию разработчику, " + 
                                 "ошибка будет исправлена в ближайшее время. Извините за неудобства")
    else:
        for item in all_users:
            try:
                bot.send_message(item[0], message.text)
            except telebot.apihelper.ApiException as ex:
                if "bot was blocked by the user" in str(ex):
                    cur.execute("DELETE FROM users WHERE chat_id = %s", (int(item[0]), ))
                    cur.execute("DELETE FROM variables WHERE id = %s", (int(item[0]), ))
                    # con.commit()
                    name = "неизвестный"
                    '''for row in all_users:
                        if row[0] == item[0]:
                            name = row[1] + " " + (row[2] if row[2] is not None else "")
                            name += (" (@" + row[3] + ")" if row[3] is not None else "")'''
                    all_users.remove(item)
                    bot.reply_to(message, "Пользователь " + name + " отключил бота и не смог получить сообщение")
                else:
                    with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
                        my_id = file.read()
                        bot.send_message(my_id, 'func=check_1(2)\n' + 'id = ' + str(message.chat.id) + '\n' + str(ex))
                    bot.reply_to(message, u"\U0001F614 " + "Произошел сбой. Я отослал информацию разработчику, " + 
                                 "ошибка будет исправлена в ближайшее время. Извините за неудобства")
        
    update_last_time(message)
    
#endregion


@bot.message_handler(func=lambda message: message.text in locations)
def get_text_messages(message):
    #update_variables(message.chat.id)
    if not check_started(message):
        return
    try:
        global station1, station2, flag, path, menu
        chat_id = message.chat.id
        if path[chat_id] == 1:
            path[chat_id] = 0
            station1[chat_id] = ''
            station2[chat_id] = ''
        if flag[chat_id] == 1:
            station1[chat_id] = message.text
            if station2[chat_id] != "":
                menu[chat_id] = new_menu(chat_id)
            bot.send_message(chat_id, "Пункт отправления: " + station1[chat_id], reply_markup=menu[chat_id])
        else:
            station2[chat_id] = message.text
            if station1[chat_id] != "":
                menu[chat_id] = new_menu(chat_id)
            bot.send_message(chat_id, "Пункт прибытия: " + station2[chat_id], reply_markup=menu[chat_id])
        query = "UPDATE variables SET path = %s, station1 = %s, station2 = %s, menu = %s WHERE id = %s"
        cur.execute(query, (path[chat_id], station1[chat_id], station2[chat_id], buttons_keyboard(menu[chat_id]), chat_id))
    except Exception as ex:
        global my_id
        with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
            my_id = file.read()
            text = '(func=lambda message: message.text in locations)\nid = ' + str(message.chat.id) + '\n' + str(ex)
            bot.send_message(my_id, str(text))
        bot.reply_to(message, u"\U0001F614 " + "Произошел сбой. Я отослал информацию разработчику, " +                      "ошибка будет исправлена в ближайшее время. Извините за неудобства")    
    update_last_time(message)


@bot.message_handler(func=lambda message: message.text == "Пункт прибытия")
def get_text_messages(message):
    #update_variables(message.chat.id)
    if not check_started(message):
        return
    global choice, flag
    chat_id = message.chat.id
    choice[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
    s1 = locations[0]
    choice[chat_id].add(types.KeyboardButton('В меню'))
    for i in range(0, len(locations)):
        if i == len(locations) - 1:
            choice[chat_id].add(types.KeyboardButton(locations[i]))
            break
        if i % 2 == 0:
            s1 = locations[i]
            if i == len(locations):
                choice[chat_id].add(types.KeyboardButton(locations[i]))
        else:
            choice[chat_id].add(types.KeyboardButton(s1), types.KeyboardButton(locations[i]))
    flag[chat_id] = 2
    query = "UPDATE variables SET choice = %s, flag = %s WHERE id = %s"
    cur.execute(query, (buttons_keyboard(choice[chat_id]), flag[chat_id], chat_id))
    bot.send_message(chat_id, "Выберите станцию", reply_markup=choice[chat_id])
    update_last_time(message)


@bot.message_handler(func=lambda message: message.text == "Пункт отправления")
def get_text_messages(message):
    if not check_started(message):
        return
    global choice, flag
    chat_id = message.chat.id
    choice[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
    s1 = locations[0]
    choice[chat_id].add(types.KeyboardButton('В меню'))
    for i in range(0, len(locations)):
        if i == len(locations) - 1:
            choice[chat_id].add(types.KeyboardButton(locations[i]))
            break
        if i % 2 == 0:
            s1 = locations[i]
        else:
            choice[chat_id].add(types.KeyboardButton(s1), types.KeyboardButton(locations[i]))
    flag[chat_id] = 1
    bot.send_message(chat_id, "Выберите станцию", reply_markup=choice[chat_id])
    query = "UPDATE variables SET choice = %s, flag = %s WHERE id = %s"
    cur.execute(query, (buttons_keyboard(choice[chat_id]), flag[chat_id], chat_id))
    update_last_time(message)


# region Date
@bot.message_handler(func=lambda message: message.text == "Выбрать дату")
def get_text_messages(message):
    #update_variables(message.chat.id)
    if not check_started(message):
        return
    now = datetime.now(pytz.timezone('Europe/Kiev'))
    chat_id = message.chat.id

    date = (now.year, now.month)
    current_shown_dates[chat_id] = date

    markup = create_calendar(now.year, now.month)
    bot.send_message(chat_id, "Выберите дату", reply_markup=markup)
    update_last_time(message)


@bot.callback_query_handler(func=lambda call: 'DAY' in call.data[0:13])
def handle_day_query(call):
    if not check_started(call.message):
        return
    global selected_date
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    last_sep = call.data.rfind(';') + 1
    if saved_date is not None:
        day = call.data[last_sep:]
        date = datetime(int(saved_date[0]), int(saved_date[1]), int(day), 0, 0, 0)
        date_list = str(date).split(' ')[0].split('-')
        selected_date[chat_id] = date_list[2] + '.' + date_list[1] + '.' + date_list[0]
        bot.send_message(chat_id=chat_id, text="Выбранная дата: " + date_list[2] + '.'
                                               + date_list[1] + '.' + date_list[0])
        bot.answer_callback_query(call.id, text="")
        cur.execute("UPDATE variables SET selected_date = %s WHERE id = %s", (selected_date[chat_id], chat_id))
        update_last_time(call.message)
    else:
        pass


@bot.callback_query_handler(func=lambda call: 'MONTH' in call.data)
def handle_month_query(call):
    if not check_started(call.message):
        return
    temp = call.data.split(';')
    month_opt = temp[0].split('-')[0]
    year, month = int(temp[1]), int(temp[2])
    chat_id = call.message.chat.id

    if month_opt == 'PREV':
        month -= 1

    elif month_opt == 'NEXT':
        month += 1

    if month < 1:
        month = 12
        year -= 1

    if month > 12:
        month = 1
        year += 1

    date = (year, month)
    current_shown_dates[chat_id] = date
    markup = create_calendar(year, month)
    bot.edit_message_text("Выберите дату", call.from_user.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: "IGNORE" in call.data)
def ignore(call):
    if not check_started(call.message):
        return
    bot.answer_callback_query(call.id, text="Дата не выбрана")
    update_last_time(call.message)
# endregion


@bot.message_handler(func=lambda message: message.text == 'В меню')
def get_text_messages(message):
    #update_variables(message.chat.id)
    if not check_started(message):
        return
    try:
        bot.send_message(message.chat.id, "Выберите маршрут", reply_markup=current_menu[message.chat.id])
    except Exception as ex:
        global my_id
        with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
            my_id = file.read()
            bot.send_message(my_id, '"В меню"\n' + 'id = ' + str(message.chat.id) + '\n' + str(ex))
        text = u"\U0001F614 " + "Произошел сбой. Я отослал информацию разработчику, " +                 "ошибка будет исправлена в ближайшее время. Извините за неудобства"
        bot.reply_to(message, text)
        
    update_last_time(message)

def is_route(message):  
    s = message.text
    if s is None:
        return False
    try:
        if '-' not in s:
            return False
        temp = s.split(' - ')
        # print(temp[0].strip(), temp[1].strip())
        if temp[0].strip() not in locations:
            return False
        if temp[1].strip() not in locations:
            return False
        return True
    except Exception as ex:
        global my_id
        with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
            my_id = file.read()
            bot.send_message(my_id, 'is_route\n' + 'id = ' + str(message.chat.id) + '\n' + str(ex))
        text = u"\U0001F614 " + "Произошел сбой. Я отослал информацию разработчику, ошибка будет исправлена в ближайшее время. Извините за неудобства"
        bot.reply_to(message, text)

@bot.message_handler(func=lambda message: is_route(message))
def get_text_messages(message):
    if not check_started(message):
        return
    #update_variables(message.chat.id)
    if message.chat.id not in threads:
        bot.send_chat_action(chat_id=message.chat.id, action='typing')
        threads[message.chat.id] = ParserRoute(bot, message, threads, cur, station1, station2,
                                               trains, warn_schedule, info_schedule, selected_date, translit)
        threads[message.chat.id].setName(message.text)
        threads[message.chat.id].start()
        #threads_name = get_threads(threads[message.chat.id])
        # cur.execute("UPDATE variables SET threads = %s WHERE id = %s", (threads[message.chat.id].getName(), message.chat.id))
    else:
        bot.send_message(message.chat.id, u"\u231B " + 'Подождите, запрос обрабатывается')
        
    update_last_time(message)


@bot.message_handler(func=lambda message: message.text == "Перезапустить")
def get_text_messages(message):
    if not check_started(message):
        return
    global menu, current_menu, choice, selected_date, route, station1, station2, trains, threads, path, flag, admin_ask
    global is_admin, to_send, users_to_send, info_schedule, warn_schedule, info_train, warn_train
    chat_id = message.chat.id
    route[chat_id] = ""
    path[chat_id] = 0
    flag[chat_id] = 1
    station1[chat_id] = ""
    station2[chat_id] = ""
    selected_date[chat_id] = ""
    warn_schedule[chat_id] = ""
    info_schedule[chat_id] = ""
    warn_train[chat_id] = ""
    info_train[chat_id] = ""
    admin_ask[chat_id] = False
    is_admin[chat_id] = False
    to_send[chat_id] = 0
    users_to_send[chat_id] = []
    trains[chat_id] = []
    menu[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
    current_menu[chat_id] = menu[chat_id]
    choice[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
    try:
        for temp in threads:
            del threads[temp]
    except RuntimeError:
        threads = {}
        pass
    upload_variables(chat_id)
    update_last_time(message)
    main_function(message)

    
def is_in_trains(text, trains):
    for temp in trains:
        item = temp.split(' ')
        if item[0] == text:
            return True
    return False

    
@bot.message_handler(func=lambda message: message.chat.id in trains and len(trains[message.chat.id]) != 0)
def get_text_messages(message):
    if not check_started(message):
        return
    if not is_in_trains(message.text, trains[message.chat.id]):
        return
    cur.execute("SELECT * FROM variables WHERE id = %s", (message.chat.id, ))
    item = cur.fetchone()
    if item is not None:
        trains[message.chat.id] = item['trains']
        info_train[message.chat.id] = item['info_train']
        warn_train[message.chat.id] = item['warn_train']
        
    if message.chat.id not in threads:
        bot.send_chat_action(chat_id=message.chat.id, action='typing')
        threads[message.chat.id] = ParserTrains(bot, message, cur, threads, trains, info_train, warn_train)
        threads[message.chat.id].setName(message.text)
        threads[message.chat.id].start()
        # threads_name = get_threads(threads[message.chat.id])
        # cur.execute("UPDATE variables SET threads = %s WHERE id = %s", (threads[message.chat.id].getName(), message.chat.id))
    else:
        bot.send_message(message.chat.id, 'Подождите, запрос обрабатывается')
        
    update_last_time(message)


def main_function(message):
    #update_variables(message.chat.id)
    global menu, choice    
    chat_id = message.chat.id
    menu[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
    choice[chat_id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu[chat_id].add(types.KeyboardButton("Пункт отправления"), types.KeyboardButton("Пункт прибытия"))
    # menu[chat_id].add(types.KeyboardButton("Пункт прибытия"))
    menu[chat_id].add(types.KeyboardButton("Выбрать дату"), types.KeyboardButton("Перезапустить"))
    # menu[chat_id].add(types.KeyboardButton("Сброс"))
    bot.send_message(chat_id, "Выберите маршрут", reply_markup=menu[chat_id])
    current_menu[chat_id] = menu[chat_id]
    menu_buttons = []
    current_menu_buttons = menu_buttons
    for tmp in menu[chat_id].keyboard:
        for item in tmp:
            menu_buttons.append(item['text'])
    s = "UPDATE variables SET menu = %s, current_menu = %s WHERE id = %s"
    cur.execute(s, (menu_buttons, current_menu_buttons, chat_id))
    # con.commit()
    

@bot.callback_query_handler(func=lambda call: True) 
def callback_inline(call):
    if not check_started(call.message):
        return
    cur.execute("SELECT * FROM variables WHERE id = %s", (call.message.chat.id, ))
    item = cur.fetchone()
    if item is not None:
        info_schedule[call.message.chat.id] = item['info_schedule']
        warn_schedule[call.message.chat.id] = item['warn_schedule']
        info_train[call.message.chat.id] = item['info_train']
        warn_train[call.message.chat.id] = item['warn_train']
        
    if call.data == '1':
        bot.answer_callback_query(callback_query_id=call.id, text="")
        if warn_schedule[call.message.chat.id].strip() == "":
            text = u"\u2139 " + "Никаких важных уведомлений на данный момент нет.\nИменения могут появится в любое время, " +                    "будьте в курсе и оставайтесь с ботом " + u"\u270C"
            bot.send_message(call.message.chat.id, text)
        else:
            bot.send_message(call.message.chat.id, edit_text(warn_schedule[call.message.chat.id]))

    if call.data == '2':
        bot.answer_callback_query(callback_query_id=call.id, text="")
        if info_schedule[call.message.chat.id].strip() == "":
            text = u"\u2139 " +                     "Никакой дополнительной информации на данный момент не найдено.\n" +                     "Изменения могут появится в любое время, будьте в курсе и оставайтесь " +                     "с ботом " + u"\u270C"
            bot.send_message(call.message.chat.id, text)
        else:
            bot.send_message(call.message.chat.id, edit_text(info_schedule[call.message.chat.id]))

    if call.data == '3':
        bot.answer_callback_query(callback_query_id=call.id, text="")
        if warn_train[call.message.chat.id].strip() == "":
            text = u"\u2139 " + "Никаких важных уведомлений на данный момент нет.\n" +                     "Именения могут появится в любое время, будьте в курсе и оставайтесь " +                     "с ботом " + u"\u270C"
            bot.send_message(call.message.chat.id, text)
        else:
            bot.send_message(call.message.chat.id, edit_text(warn_train[call.message.chat.id]))

    if call.data == '4':
        bot.answer_callback_query(callback_query_id=call.id, text="")
        if info_train[call.message.chat.id].strip() == "":
            text = u"\u2139 " + "Никакой дополнительной информации на данный момент не найдено.\n" +                     "Изменения могут появится в любое время, будьте в курсе и оставайтесь " +                     "с ботом " + u"\u270C"
            bot.send_message(call.message.chat.id, text)
        else:
            bot.send_message(call.message.chat.id, edit_text(info_train[call.message.chat.id]))
            # bot.send_message(call.message.chat.id, info_train[call.message.chat.id], parse_mode='HTML')
            
    update_last_time(call.message)
    

def edit_text(text: str):
    temp = text.split('\n')
    new_text = ""
    for i in temp:
        if i == "":
            continue
        new_text += i.strip() + "\n"
    return new_text


if __name__ == "__main__":
    bot.polling()


# In[ ]:




