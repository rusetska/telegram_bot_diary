# -*- coding: utf-8 -*-

import pandas as pd
import re
import os
import logging
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()])

# Год публикации и время
YEAR = 2025
FIVEBOOK_HOUR = 12
REFLECTION_HOUR = 19
MAX_ATTEMPTS = 4  # 1 основная + 3 попытки со сдвигом

# Получаем токены из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN:
    raise ValueError("Токен отсутствует! Добавь его в секреты репозитория.")

# Загружаем таблицы из Google Sheets
fivebook = pd.read_csv("https://docs.google.com/spreadsheets/d/1bg-5nIYub5Ydo2S6tR9eQgGwKSAszzh9WPF6EEBt6nY/gviz/tq?tqx=out:csv&gid=301691926")
reflection = pd.read_csv("https://docs.google.com/spreadsheets/d/1bg-5nIYub5Ydo2S6tR9eQgGwKSAszzh9WPF6EEBt6nY/gviz/tq?tqx=out:csv&gid=315900274")

# Приводим даты к нужному формату
fivebook["date"] = pd.to_datetime(fivebook["date"], format="%d.%m.%Y").apply(lambda x: x.replace(year=YEAR, hour=FIVEBOOK_HOUR))
reflection["date"] = pd.to_datetime(reflection["date"], format="%d.%m.%Y").apply(lambda x: x.replace(year=YEAR, hour=REFLECTION_HOUR))

def escape_markdown(text):
    """Экранируем специальные символы Markdown V2"""
    escape_chars = r'_*\[\]()~>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

def get_next_post(shift_minutes=0):
    """
    Возвращает ближайший пост, который нужно опубликовать.
    Можно сдвинуть время проверки на shift_minutes вперед.
    """
    now = datetime.now() + timedelta(minutes=shift_minutes)

    # Ищем посты, у которых время публикации <= сейчас
    next_fivebook = fivebook[fivebook["date"] <= now].sort_values("date").head(1)
    next_reflection = reflection[reflection["date"] <= now].sort_values("date").head(1)

    # Объединяем и выбираем самый ранний
    next_post = pd.concat([next_fivebook, next_reflection]).sort_values("date").head(1)

    return next_post.iloc[0] if not next_post.empty else None

def send_message(bot, chat_id, text):
    """Отправляет сообщение в Telegram"""
    try:
        bot.send_message(chat_id=chat_id, text=text, parse_mode="MarkdownV2")
        logging.info(f"Успешно отправлено: {text[:50]}...")
        return True
    except TelegramError as e:
        logging.error(f"Ошибка отправки: {e}")
        return False

if __name__ == "__main__":
    bot = Bot(token=TOKEN)

    for attempt in range(MAX_ATTEMPTS):
        post = get_next_post(shift_minutes=attempt * 5)

        if post is not None:
            message = f"{escape_markdown(post['hashtag'])}\n\n*{escape_markdown(post['question'])}*"
            success = send_message(bot, CHAT_ID, message)

            if success:
                break  # Если пост отправлен, прерываем цикл
        else:
            logging.info(f"Попытка {attempt + 1}: пост не найден.")

    logging.info("Бот завершил работу.")
