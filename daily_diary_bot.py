# -*- coding: utf-8 -*-

import pandas as pd
import re
import asyncio
import os
from datetime import datetime, timedelta
from telegram import Bot

#год публикации, время и количество дней для постинга
YEAR = 2025
FIVEBOOK_HOUR = 22
REFLECTION_HOUR = 22
DAY = 10

#получаем токены из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN:
    raise ValueError("⛔️ Токен не найден! Проверь, добавлен ли он в секреты.")
else:
    print("✅ Токен успешно загружен!")

#загружаем таблицы из Google Sheets
fivebook = pd.read_csv("https://docs.google.com/spreadsheets/d/1bg-5nIYub5Ydo2S6tR9eQgGwKSAszzh9WPF6EEBt6nY/gviz/tq?tqx=out:csv&gid=301691926")
reflection = pd.read_csv("https://docs.google.com/spreadsheets/d/1bg-5nIYub5Ydo2S6tR9eQgGwKSAszzh9WPF6EEBt6nY/gviz/tq?tqx=out:csv&gid=315900274")

#приводим даты к нужному формату
fivebook["date"] = pd.to_datetime(fivebook["date"], format="%d.%m.%Y").apply(lambda x: x.replace(year=YEAR, hour=FIVEBOOK_HOUR))
reflection["date"] = pd.to_datetime(reflection["date"], format="%d.%m.%Y").apply(lambda x: x.replace(year=YEAR, hour=REFLECTION_HOUR))

def escape_markdown(text):
    """экранируем специальные символы Markdown V2"""
    escape_chars = r'_*\[\]()~>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

async def send_scheduled_messages(days):
    """отправляем сообщения по расписанию"""
    bot = Bot(token=TOKEN)
    
    #отбираем посты за указанное количество дней
    now = datetime.now()
    fivebook_posts = fivebook[(fivebook["date"] >= now) & (fivebook["date"] < now + timedelta(days=days))]
    reflection_posts = reflection[(reflection["date"] >= now) & (reflection["date"] < now + timedelta(days=days))]

    #объединяем все посты в один список и сортируем по времени
    all_posts = pd.concat([fivebook_posts, reflection_posts]).sort_values(by="date")

    for _, row in all_posts.iterrows():
        post_time = row["date"]
        delay = (post_time - datetime.now()).total_seconds()

        if delay > 0:
            print(f"Ждём {delay:.2f} секунд до публикации.")
            await asyncio.sleep(delay)

        message = f"{escape_markdown(row['hashtag'])}\n\n*{escape_markdown(row['question'])}*"
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="MarkdownV2")
        print("✅ Пост опубликован!")

#запускаем задачу на публикацию сообщений на N дней вперёд
if __name__ == "__main__":
    asyncio.run(send_scheduled_messages(DAY))
