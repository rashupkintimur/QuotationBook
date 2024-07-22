import config
import telebot
from telebot import types
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import time
import uuid

# создаём экземпляр бота
bot = telebot.TeleBot(config.API_TOKEN)

# вспомогательные переменные
url = "https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang="
users = {}
quotes_db = {}

# Обработчик /start команды
@bot.message_handler(commands=["start"])
def welcome(message):
	# создаём клавиатуру
	markup = types.ReplyKeyboardMarkup(row_width=2)
	button_en_lang = types.KeyboardButton("🇬🇧English")
	button_ru_lang = types.KeyboardButton("🇷🇺Русский")
	markup.add(button_en_lang, button_ru_lang)

	# Отправляем сообщение с кнопками
	bot.send_message(message.chat.id, "Выберите язык", reply_markup=markup)

# Обрабатывает команду /favorite_quotes
@bot.message_handler(commands=["favorite_quotes"])
def show_favorites(message):
    user_id = message.from_user.id

    if user_id in users and "favorites" in users[user_id] and users[user_id]["favorites"]:
        favorites = users[user_id]["favorites"]
        if not favorites:
            bot.send_message(message.chat.id, "У вас нет избранных цитат.")
        else:
            response_message = "Ваши избранные цитаты:\n\n"
            for quote in favorites:
                response_message += f"<i>{quote['text']}</i>\n\n<b>{quote['author']}</b>\n\n"
            bot.send_message(message.chat.id, response_message, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "У вас нет избранных цитат.")

# обработчик выбора языка
@bot.message_handler(func=lambda message: message.text in ["🇬🇧English", "🇷🇺Русский"])
def quote_message(message):
	global lang

	user_id = message.from_user.id

	if message.text == "🇬🇧English":
		users[user_id] = { "lang": "en", "favorites": [] }
	elif message.text == "🇷🇺Русский":
		users[user_id] = { "lang": "ru", "favorites": [] }

	# Удаляем клавиатуру выбора языка и добавляем кнопку "Получить цитату"
	markup = types.ReplyKeyboardMarkup(row_width=1)
	button_send = types.KeyboardButton("Получить цитату")
	markup.add(button_send)
	bot.send_message(message.chat.id, "Язык выбран. Нажмите кнопку 'Получить цитату' для получения цитаты!", reply_markup=markup)

# Обрабатывает нажатие на кнопку "Получить цитату"
@bot.message_handler(func=lambda message: message.text == "Получить цитату")
def handle_send(message):
    user_id = message.from_user.id

    if user_id in users:
        send_quote(users[user_id]["lang"], message.chat.id)
    else:
        bot.send_message(message.chat.id, "Сначала выберите язык.")

# Обрабатывает нажатие на кнопку "Сохранить в избранное"
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    data = call.data.split(":")
    action = data[0]

    if action == "save_quote":
        quote_id = data[1]
        user_id = call.message.chat.id

        if user_id in users and quote_id in quotes_db:
            quote = quotes_db[quote_id]
            users[user_id]["favorites"].append({
                "text": quote["text"],
                "author": quote["author"]
            })

            bot.answer_callback_query(call.id, "Цитата сохранена в избранное!")
        else:
            bot.answer_callback_query(call.id, "Ошибка: не удалось сохранить цитату.")

# Отправляет цитату
def send_quote(lang, chat_id):
	response = requests.get(url + lang)

	if response.status_code == 200:
		try:
			quoteObj = response.json()
		except ValueError:
			bot.send_message(chat_id, "Ошибка при обработке ответа от сервера")
		else:
			quoteText = quoteObj["quoteText"]
			quoteAuthor = quoteObj["quoteAuthor"]

			# Генерация уникального идентификатора для цитаты
			quote_id = str(uuid.uuid4())

			# Сохранение цитаты в базе данных
			quotes_db[quote_id] = {
				"text": quoteText,
                "author": quoteAuthor
			}

			markup = types.InlineKeyboardMarkup()
			save = types.InlineKeyboardButton("Сохранить в избранное", callback_data=f"save_quote:{quote_id}")
			markup.add(save)

			bot.send_message(chat_id, f"<i>{quoteText}</i>\n\n<b>{quoteAuthor}</b>", reply_markup=markup, parse_mode="HTML")
	else:
		print(f"Ошибка: {response.status_code}")

# Ежедневная отправка сообщения
def send_daily_message():
	for user_id in users:
		send_quote(users[user_id]["lang"], user_id)

# Запуск планировщика
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_message, "cron", hour=7)
scheduler.start()

# Запуск бота
if __name__ == "__main__":
	bot.polling(none_stop=True)
