from validators import *
from yandex_gpt import ask_gpt
from config import LOGS, COUNT_LAST_MSG
from database import create_database, add_message, select_n_last_messages
import telebot
import logging
from speechkit import text_to_speech, speech_to_text
from creds import get_bot_token

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.ERROR, format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")
bot = telebot.TeleBot(get_bot_token())  # создаём объект бота
create_database()


# Проверка на максимальное количество пользователей
def max_users_check(user_id):
    status_check_users, error_message = check_number_of_users(user_id)
    if not status_check_users:
        # Если количество пользователей превышает максимально допустимое,
        # отправляем сообщение с ошибкой пользователю и прекращаем выполнение функции
        bot.send_message(user_id, error_message)
        return True

# ВАЛИДАЦИЯ GPT: подсчет токенов
def count_gpt_tokens(messages, total_spent_tokens, user_id):
    total_gpt_tokens, error_message = is_gpt_token_limit(messages, total_spent_tokens)
    if error_message:
        bot.send_message(user_id, error_message)
        return

# ВАЛИДАЦИЯ_АУДИО: проверка символов для ответа
def check_tts_symbols(answer_gpt, user_id):
    tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)
    if error_message:
        bot.send_message(user_id, error_message)
        return

# ВАЛИДАЦИЯ_АУДИО: проверяем количество аудиоблоков
def check_stt_blocks(message, user_id):
    stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
    if error_message:
        bot.send_message(user_id, error_message)
        return


# /start
@bot.message_handler(commands=['start'])
def start(message):
    max_users_check(message.chat.id)
    bot.send_message(message.chat.id, "Привет! Отправь мне голосовое сообщение или текст, и я тебе отвечу!")


# /help
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "Чтобы приступить к общению, отправь мне голосовое сообщение или текст")


# /debug
@bot.message_handler(commands=['debug'])
def debug(message):
    with open("logs.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


# /tts
@bot.message_handler(commands=['tts'])
def tts_handler(message):
    user_id = message.chat.id
    bot.send_message(user_id, 'Отправь следующим сообщеним текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, text_to_speech)


# обрабатываем голосовые сообщения
@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    user_id = message.from_user.id
    try:
        # Проверка на максимальное количество пользователей
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return
        # Проверка на доступность аудиоблоков
        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(user_id, error_message)
            return
        # Обработка голосового сообщения
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return
        # Запись в БД
        add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])
        # Проверка на доступность GPT-токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return
        # Запрос к GPT и обработка ответа
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer
        # Проверка на лимит символов для SpeechKit
        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)
        # Запись ответа GPT в БД
        add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])
        if error_message:
            bot.send_message(user_id, error_message)
            return
        # Преобразование ответа в аудио и отправка
        status_tts, voice_response = text_to_speech(answer_gpt)
        if status_tts:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)
        bot.send_message(user_id, "Не получилось ответить. Попробуй записать другое сообщение")


# обрабатываем текстовые сообщения
@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        user_id = message.chat.id
        # ВАЛИДАЦИЯ: проверяем, есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)  # мест нет =(
            return
        # БД: добавляем сообщение пользователя и его роль в базу данных
        full_user_message = [message.text, 'user', 0, 0, 0]
        add_message(user_id=user_id, full_message=full_user_message)
        # ВАЛИДАЦИЯ: считаем количество доступных пользователю GPT-токенов
        # получаем последние 4 (COUNT_LAST_MSG) сообщения и количество уже потраченных токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        count_gpt_tokens(last_messages, total_spent_tokens, user_id)
        # получаем сумму уже потраченных токенов + токенов в новом сообщении и оставшиеся лимиты пользователя
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, error_message)
            return
        # GPT: отправляем запрос к GPT
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        # GPT: обрабатываем ответ от GPT
        if not status_gpt:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, answer_gpt)
            return
        # сумма всех потраченных токенов + токены в ответе GPT
        total_gpt_tokens += tokens_in_answer
        # БД: добавляем ответ GPT и потраченные токены в базу данных
        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)
        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)  # отвечаем пользователю текстом
    except Exception as e:
        logging.error(e)  # если ошибка — записываем её в логи
        bot.send_message(message.chat.id, "Не получилось ответить. Попробуй написать другое сообщение")


# обрабатываем все остальные типы сообщений
@bot.message_handler(func=lambda: True)
def handler(message):
    bot.send_message(message.chat.id, "Отправь мне голосовое или текстовое сообщение, и я тебе отвечу")


bot.polling()  # запускаем бота