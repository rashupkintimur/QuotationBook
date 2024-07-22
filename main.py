import config
import telebot
from telebot import types
import requests

# создаём экземпляр бота
bot = telebot.TeleBot(config.API_TOKEN)

# вспомогательные переменные
lang = None
url = "https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang="

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

# Обработчик сообщений
@bot.message_handler(func=lambda message: True)
def quote_message(message):
	global lang

	if message.text == "🇬🇧English":
		lang = "en"
	elif message.text == "🇷🇺Русский":
		lang = "ru"

	send_quote(message)

# Отправляет цитату
def send_quote(message):
	response = requests.get(url + lang)

	if response.status_code == 200:
		try:
			quoteObj = response.json()

			bot.send_message(message.chat.id, f"<i>{quoteObj["quoteText"]}</i>\n\n<b>{quoteObj["quoteAuthor"]}</b>", parse_mode="HTML")
		except ValueError:
			bot.send_message(message.chat.id, "Ошибка при обработке ответа от сервера")
	else:
		print(f"Ошибка: {response.status_code}")

# Запуск бота
if __name__ == "__main__":
	bot.polling()
