import time

import requests
import telebot
from bs4 import BeautifulSoup
from telebot import TeleBot

# Токен телеграм бота
TOKEN = '5682104837:AAEd_LRrlVLlJXGgIyJ0JAM8SqGiWt6C6Go'

# Список валют, для которых нужно получать курсы
currencies = ['USD', 'EUR', 'RUB', 'PLN']
rates = {}
favorite_currencies = []
name_currency = ''
x = 0
for currency in currencies:
    rates.update({
        currency: {'name': currency, 'index_of_currencies': x}
    })
    x += 1
# + '_rate'
# Создание объекта бота
bot: TeleBot = telebot.TeleBot(TOKEN)


# Команда старт
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    # Отправка приветственного сообщения и предложение выбрать любимые валюты
    bot.send_message(chat_id, 'Привет! Я бот для получения курсов валют.')
    for currency in currencies:
        rate = rates.get(currency)
        if rate is not None:
            name = rate.get('name')
            bot.send_message(chat_id, name, reply_markup=keyboard.row(currency))


@bot.message_handler(commands=['help'])
def help(message):
    chat_id = message.chat.id
    help_message = "Список доступных команд:\n\n"
    commands = {
        "/start": "Запуск бота",
        "/help": "Список доступных команд",
        "/favorites": "просмотр списка избранных валют",
        "/del_favorite": "удаление одной валюты из списка избранных валют",
        "/weather": "Получить прогноз погоды"
    }
    for command, description in commands.items():
        help_message += f"{command} - {description}\n"
    bot.send_message(chat_id, text=help_message)


# Функция для получения курсов валют с сайта myfin.by
def get_rates_buy(index_of_currencies):
    response = requests.get('https://myfin.by/currency/minsk')
    soup = BeautifulSoup(response.content, "html.parser")
    data = soup.find("tbody", {"class": ""}).find_all("tr")[index_of_currencies].find_all('td')[1].text
    return data


def get_rates_sell(index_of_currencies):
    response = requests.get('https://myfin.by/currency/minsk')
    soup = BeautifulSoup(response.content, "html.parser")
    data = soup.find("tbody", {"class": ""}).find_all("tr")[index_of_currencies].find_all('td')[2].text
    return data


# Обработчик команды /set_currencies
@bot.message_handler(commands=['get_now'])
def get_now(message):
    global favorite_currencies, rates
    chat_id = message.chat.id
    message_text = 'Курсы валют:\n\n'
    for favorite_currency in favorite_currencies:
        message_text += favorite_currency + ': покупка(' + get_rates_buy(
            rates[favorite_currency]['index_of_currencies']) + '), продажа(' + get_rates_sell(
            rates[favorite_currency]['index_of_currencies']) + ')' + '\n'
    bot.send_message(chat_id, message_text)


@bot.message_handler(commands=['favorites'])
def handle_favorites(message):
    global favorite_currencies
    user_id = message.chat.id

    favorites = favorite_currencies
    if favorites:
        bot.send_message(user_id, f"Ваши любимые валюты: {favorites}")
    else:
        bot.send_message(user_id, "Вы не добавили ни одной валюты в избранное.")


@bot.message_handler(commands=['add_favorite'])
def add_favorite(message):
    global favorite_currencies, currencies

    bot.send_message(message.chat.id, 'Введите валюту, которую хотите добавить в избранные:')
    bot.register_next_step_handler(message, lambda m: process_add_favorite_currency(m, favorite_currencies, currencies))


def process_add_favorite_currency(message, favorite_currencies, currencies):
    currency = message.text
    if currency in currencies and currency not in favorite_currencies:
        favorite_currencies.append(currency)
        bot.reply_to(message, f"{currency} добавлена в избранных.")
    elif currency in favorite_currencies:
        bot.reply_to(message, f"{currency} уже есть в избранных.")
    else:
        bot.reply_to(message, f"{currency} не является доступной валютой.")


@bot.message_handler(commands=['del_favorite'])
def del_favorite(message):
    global favorite_currencies, currencies
    bot.send_message(message.chat.id, 'Введите валюту, которую хотите удалить из избранных:')
    bot.register_next_step_handler(message, lambda m: process_del_favorite_currency(m, favorite_currencies, currencies))


def process_del_favorite_currency(message, favorite_currencies, currencies):
    currency = message.text
    if currency in currencies and currency in favorite_currencies:
        favorite_currencies.remove(currency)
        bot.reply_to(message, f"{currency} удалена из избранных.")
    else:
        bot.reply_to(message, f"{currency} не была найдена в избранных.")


# Обработчик команды /set_time
@bot.message_handler(commands=['set_time'])
def set_time(message):
    bot.reply_to(message, 'Укажи время, в которое я буду присылать курсы валют (в формате ЧЧ:ММ):')
    bot.register_next_step_handler(message, lambda m: process_set_time(m))


def process_set_time(message, ):
    global minutes, hours, favorite_currencies
    chat_id = message.chat.id
    text = message.text

    if ':' in message.text:
        try:
            hours, minutes = message.text.split(':')
            hours = int(hours)
            minutes = int(minutes)

            if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
                raise ValueError()

            bot.send_message(chat_id, 'Курсы валют будут присылаться каждый день в ' + message.text)

            while True:
                now = time.localtime()
                if favorite_currencies != '':
                    if now.tm_hour == hours and now.tm_min == minutes:
                        message_text = 'Курсы валют:\n\n'
                        for favorite_currency in favorite_currencies:
                            message_text += favorite_currency + ': покупка(' + get_rates_buy(
                                rates[favorite_currency]['index_of_currencies']) + '), продажа(' + get_rates_sell(
                                rates[favorite_currency]['index_of_currencies']) + ')' + '\n'
                        bot.send_message(chat_id, message_text)
                        break
                else:
                    bot.send_message(chat_id, 'Вы не выбрали ни одной в избранные\n'
                                              'чтобы получать курсы валют добавьте необходимые в избранные')
                time.sleep(60)

        except ValueError:
            bot.send_message(chat_id, 'Некорректная форма')


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text
    if text in currencies:
        bot.send_message(chat_id, 'Для действия с валютой сначала выберите команду')


bot.polling()
