import datetime
from threading import Thread

import requests
from bs4 import BeautifulSoup
from telebot import types
import pytz


class ParserRoute(Thread):

    def __init__(self, bot, message, threads, cur, station1, station2, trains, warn_schedule, info_schedule,
                 selected_date, translit):
        Thread.__init__(self)
        self.bot = bot
        self.message = message
        self.threads = threads
        self.cur = cur
        self.station1 = station1
        self.station2 = station2
        self.trains = trains
        self.warn_schedule = warn_schedule
        self.info_schedule = info_schedule
        self.selected_date = selected_date
        self.translit = translit

    def run(self):
        # print('In run', self.getName())
        chat_id = self.message.chat.id
        threads = self.threads
        station1 = self.station1
        station2 = self.station2
        trains = self.trains
        warn_schedule = self.warn_schedule
        info_schedule = self.info_schedule
        selected_date = self.selected_date
        translit = self.translit
        bot = self.bot
        cur = self.cur
        url = {}

        try:
            trains[chat_id] = []
            st1 = self.get_station(translit[station1[chat_id]])
            st2 = self.get_station(translit[station2[chat_id]])
            for_link = self.str_for_link(st1, st2)
            now = datetime.datetime.now(pytz.timezone('Europe/Kiev'))
            now_list = str(now).split(' ')[0].split('-')
            user_date = now_list[2] + '.' + now_list[1] + '.' + now_list[0]
            if selected_date[chat_id] != "":  # Если этот пользователь устанавливал дату
                user_date = selected_date[chat_id]
            url[chat_id] = "http://poezdato.net/raspisanie-poezdov/" + for_link + '/' + user_date + '/'
            # print(url[chat_id])
            page = requests.get(url[chat_id])
            soup = BeautifulSoup(page.text, 'html.parser')
            row = soup.findAll('tr')[1:]
            train = {}
            answer = ""
            for data in row:
                elements = data.findAll('td')
                if elements[0].find('img').get('title') == 'Пригородный':
                    number = elements[1].find('a').text
                    url_number = elements[1].find('a').get('href')
                    _from = elements[2].findAll('a')[0].text.replace('\n', ' ').strip()
                    _to = elements[2].findAll('a')[1].text.replace('\n', ' ').strip()
                    time1 = elements[3].find('span').text
                    time2 = elements[4].find('span').text
                    time_in_go = elements[5].text
                    train['number'] = number
                    train['from'] = _from
                    train['to'] = _to
                    train['time1'] = time1
                    train['time2'] = time2
                    train['travel_time'] = time_in_go
                    if '-' in number:
                        tmp = number.split('-')
                        number = tmp[0] + ' (' + tmp[1] + ')'

                    text = "🚆 /" + number + " " + _from + u"\u2014" + _to + '\n*' + time1.replace('.', ':') + "* (ст " + \
                           station1[chat_id] + ")\n*" + time2.replace('.', ':') + '* (ст ' + \
                           station2[chat_id] + ')\n' + 'В пути: ' + time_in_go + '\n\n'
                    answer += text
                    trains[chat_id].append('/' + number.split(' ')[0] + ' ' + url_number)
                    #trains[chat_id]['/' + number.split(' ')[0]] = url_number
            if answer == "":
                answer = u"\U0001F614 Поездов по данному запросу не найдено"

            warnings = soup.find_all('div', class_='warning')
            warn_schedule[chat_id] = ""
            info_schedule[chat_id] = ""
            for temp in warnings:
                if len(temp.get('class')) != 1:
                    continue
                warn_schedule[chat_id] += u"\u26A1 " + temp.text.strip() + "\n"

            try:
                info_text = soup.find('div', class_='info_bottom').find_next('p')
                info_schedule[chat_id] = u"\u2139 " + info_text.text
            except AttributeError:
                info_schedule[chat_id] = ""

            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton('Важные уведомления', callback_data='1'))
            keyboard.add(types.InlineKeyboardButton('Дополнительная информация', callback_data='2'))
            bot.send_message(chat_id, '🗓 *' + user_date + '*' + '\n\n' + answer, parse_mode='Markdown', reply_markup=keyboard)
            del threads[chat_id]
            cur.execute("UPDATE variables SET trains = %s, info_schedule = %s, warn_schedule = %s WHERE id = %s", 
                        (trains[chat_id], info_schedule[chat_id], warn_schedule[chat_id], chat_id))
        except (KeyError, IndexError) as err:
            with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
                my_id = file.read()
                bot.send_message(my_id, 'Parse_Route\n' + 'id = ' + str(chat_id) + '\n' + str(err))
            bot.reply_to(chat_id, u"\U0001F614 " + "Произошел сбой. Информация об ошибке отправлена разработчику, " + 
                         "ошибка будет исправлена в ближайшее время. Извините за неудобства")
            pass
	
			
    @staticmethod
    def str_for_link(st1: str, st2: str):
        st1 = st1.replace(' ', '-')
        st2 = st2.replace(' ', '-')
        s = st1 + '--' + st2
        return s

    @staticmethod
    def get_station(s: str):
        s = s.replace("'", '')
        s = s.replace(".", '')
        s = s.lower()
        return s


class ParserTrains(Thread):
    def __init__(self, bot, message, cur, threads, trains, info_train, warn_train):
        Thread.__init__(self)
        self.bot = bot
        self.message = message
        self.threads = threads
        self.trains = trains
        self.info_train = info_train
        self.warn_train = warn_train
        self.cur = cur

    
    def run(self):
        trains = self.trains
        message = self.message
        chat_id = message.chat.id
        bot = self.bot
        threads = self.threads
        info_train = self.info_train
        warn_train = self.warn_train
        cur = self.cur
        try:
            if len(trains[chat_id]) != 0:
                # print("http://poezdato.net" + str(trains[chat_id].get(message.text)))
                s = ""
                begin = ""
                end = ""
                trains_dict = self.get_trains(trains[chat_id])
                page = requests.get("http://poezdato.net/" + str(trains_dict[message.text]))
                soup = BeautifulSoup(page.text, 'html.parser')
                rows = soup.find('tbody').find_all_next('tr')
                rows = [tmp for tmp in rows if len(tmp.findAll('td')) == 5]  # 5 столбцов таблицы
                i = 0
                for temp in rows:
                    row = temp.findAll('td')
                    name_st = row[0].text.strip()
                    time1 = row[1].text.strip()
                    time_stop = row[2].text.strip()
                    time2 = row[3].text.strip()
                    time_in_go = row[4].text.strip()
                    if name_st != "":
                        s += u'\U0001f689 ' + name_st + '\n'
                    if time1 != "":
                        s += time1.replace('.', ":") + (' - ' if i != len(rows) - 1 else '\n')
                    if time2 != "":
                        s += time2.replace('.', ":") + ('\n\n' if i == 0 else ' (')
                    if time_stop != "":
                        s += 'стоянка ' + time_stop + ')\n'
                    if time_in_go != "":
                        s += 'В пути: ' + " ".join(time_in_go.split()) + '\n\n'
                    if i == 0:
                        begin = row[0].text.strip()
                    if i == len(rows) - 1:
                        end = row[0].text.strip()
                    i += 1

                answer = "🚆 *" + message.text.replace('/', '') + ' ' + begin + ' - ' + end + '*\n\n'
                answer = answer + s

                warnings = soup.find_all('div', class_='warning')
                warn_train[chat_id] = ""
                for temp in warnings:
                    if len(temp.get('class')) != 1:
                        continue
                    warn_train[chat_id] += u"\u26A1 " + temp.text.strip() + "\n"

                try:
                    info_text = soup.find('div', class_='info_bottom').find_next('p')
                    info_train[chat_id] = u"\u2139 " + info_text.text
                except AttributeError:
                    info_train[chat_id] = ""

                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton('Важные уведомления', callback_data='3'))
                keyboard.add(types.InlineKeyboardButton('Дополнительная информация', callback_data='4'))
                if len(s) > 4096:
                    bot.send_message(chat_id, answer[:int(len(answer) / 2)], parse_mode='Markdown')
                    bot.send_message(chat_id, answer[int(len(answer) / 2):], parse_mode='Markdown', reply_markup=keyboard)
                else:
                    bot.send_message(chat_id, answer, parse_mode='Markdown', reply_markup=keyboard)

                del threads[chat_id]

                cur.execute("UPDATE variables SET info_train = %s, warn_train = %s WHERE id = %s", 
                            (info_train[chat_id], warn_train[chat_id], chat_id))

        except (KeyError, IndexError) as err:
            with open('/home/ubuntu/Daniil/Find_train/admin_id.txt', mode='r') as file:
                my_id = file.read()
                bot.send_message(my_id, 'Parse_Trains\n' + 'id = ' + str(chat_id) + '\n' + str(err))
            bot.reply_to(chat_id, u"\U0001F614 " + "Произошел сбой. Информация об ошибке отправлена разработчику, " + 
                         "ошибка будет исправлена в ближайшее время. Извините за неудобства")
            pass


    @staticmethod
    def get_trains(trains_list):
        trains_dict = {}
        for temp in trains_list:
            item = temp.split(' ')
            trains_dict[item[0]] = item[1]
        return trains_dict