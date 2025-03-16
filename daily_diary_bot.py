# -*- coding: utf-8 -*-

import pandas as pd
import re
import os
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Год публикации и время
YEAR = 2025
FIVEBOOK_HOUR = 14
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
fivebook["date"] = pd.to_datetime(fivebook["date"], format="%d.%m.%Y")
reflection["date"] = pd.to_datetime(reflection["date"], format="%d.%m.%Y")

# Обновляем год и добавляем время
fivebook["date"] = fivebook["date"].apply(lambda x: x.replace(year=YEAR, hour=FIVEBOOK_HOUR))
reflection["date"] = reflection["date"].apply(lambda x: x.replace(year=YEAR, hour=REFLECTION_HOUR))

def escape_markdown(text):
    """Экранируем специальные символы Markdown V2"""
    escape_chars = r'_*[\]()~`>+=|{}.!'
    text = re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)  
    text = text.replace("#", "\#") 
    return text

def get_today_post(shift_minutes=0):
    """
    Возвращает пост за текущую дату (день и месяц), но с обновленным годом.
    Можно сдвинуть время проверки на shift_minutes вперед.
    """
    now = datetime.now() + timedelta(minutes=shift_minutes)
    today_str = now.strftime("%d.%m")  # Строка в формате ДД.ММ для фильтрации

    # Фильтруем посты только за сегодняшнее число
    today_fivebook = fivebook[fivebook["date"].dt.strftime("%d.%m") == today_str]
    today_reflection = reflection[reflection["date"].dt.strftime("%d.%m") == today_str]

    # Объединяем и выбираем ближайший пост
    today_posts = pd.concat([today_fivebook, today_reflection]).sort_values("date")
    
    if not today_posts.empty:
        selected_post = today_posts.iloc[0]
        logging.info(f"Выбранный пост: {selected_post}")
        return selected_post
    else:
        logging.info(f"На {today_str} пост не найден.")
        return None

async def send_message_async(bot, chat_id, text):
    """Асинхронная отправка сообщения"""
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="MarkdownV2")
        logging.info(f"Успешно отправлено: {text[:50]}...")
        return True
    except TelegramError as e:
        logging.error(f"Ошибка отправки: {e}")
        return False

if __name__ == "__main__":
    bot = Bot(token=TOKEN)
    
    for attempt in range(MAX_ATTEMPTS):
        post = get_today_post(shift_minutes=attempt * 5)

        if post is not None:
            message = f"{escape_markdown(post['hashtag'])}\n\n*{escape_markdown(post['question'])}*"
            asyncio.run(send_message_async(bot, CHAT_ID, message))
            break  # Если пост отправлен, прерываем цикл
        else:
            logging.info(f"Попытка {attempt + 1}: пост не найден.")
    
    logging.info("Бот завершил работу.")
