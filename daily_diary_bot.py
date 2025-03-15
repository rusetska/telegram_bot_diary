# -*- coding: utf-8 -*-
"""daily_diary_bot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1LX_bQZA_8pi9Ivhn7ib8YNFxy1nvZIxU

Лень — лучший двигатель прогресса.

Мне наскучило вручную планировать однотипные посты в личный канал-дневник, так что автоматизируем процесс: Google Sheets, Python и моя любимая помощница — да-да, у меня ChatGPT — девочка 😊
"""

#указываем год и время публикации
YEAR = 2025
FIVEBOOK_HOUR = 9
REFLECTION_HOUR = 18

#импортируем библиотеки
import pandas as pd
import re
import asyncio
import os
from datetime import datetime, timedelta
from telegram import Bot
from telegram.ext import Application, JobQueue

#подключаем токен и id канала
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not TOKEN:
    raise ValueError("⛔️ Токен не найден! Проверь, добавлен ли он в секреты.")
else:
    print("✅ Токен успешно загружен!")

#подгружаем обе страницы с вопросами
fivebook, reflection = (pd.read_csv("https://docs.google.com/spreadsheets/d/1bg-5nIYub5Ydo2S6tR9eQgGwKSAszzh9WPF6EEBt6nY/gviz/tq?tqx=out:csv&gid=301691926"),
                        pd.read_csv("https://docs.google.com/spreadsheets/d/1bg-5nIYub5Ydo2S6tR9eQgGwKSAszzh9WPF6EEBt6nY/gviz/tq?tqx=out:csv&gid=315900274"))
#меняем формат даты
fivebook["date"] = pd.to_datetime(fivebook["date"], format="%d.%m.%Y")
reflection["date"] = pd.to_datetime(reflection["date"], format="%d.%m.%Y")
#подтягиваем год и время публикации
fivebook["date"] = fivebook["date"].apply(lambda x: x.replace(year=YEAR, hour=FIVEBOOK_HOUR))
reflection["date"] = reflection["date"].apply(lambda x: x.replace(year=YEAR, hour=REFLECTION_HOUR))

#функция для экранирования спецсимволов, чтобы в посте можно было выделять текст
def escape_markdown(text):
    escape_chars = r'_*\[\]()~>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

#асинхронная функция отправки сообщений
async def send_scheduled_messages(days):
    #создаём бота для отправки сообщений
    bot = Bot(token=TOKEN)
    #выбираем посты из обеих таблиц для публикации в указанное количество дней от текущего
    fivebook_posts = fivebook[(fivebook["date"] >= datetime.now()) & (fivebook["date"] < datetime.now() + timedelta(days=days))]
    reflection_posts = reflection[(reflection["date"] >= datetime.now()) & (reflection["date"] < datetime.now() + timedelta(days=days))]
    #запускаем цикл для публикации постов
    for _, row in fivebook_posts.iterrows():
        post_time = row["date"]
        delay = (post_time - datetime.now()).total_seconds()
        #ждём нужное время перед публикацией
        if delay > 0:
            print(f"Ждём {delay:.2f} секунд до публикации поста.")
            await asyncio.sleep(delay)
            message = f"{escape_markdown(row['hashtag'])}\n\n*{escape_markdown(row['question'])}*"
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="MarkdownV2")
            print("✅ Вопрос пятибука опубликован!")
            #вкладываем цикл для публикации второго поста
            for _, row in reflection_posts.iterrows():
              post_time = row["date"]
              delay = (post_time - datetime.now()).total_seconds()
              #ждём нужное время перед публикацией
              if delay > 0:
                print(f"Ждём {delay:.2f} секунд до публикации поста.")
                await asyncio.sleep(delay)
                message = f"{escape_markdown(row['hashtag'])}\n\n*{escape_markdown(row['question'])}*"
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="MarkdownV2")
                print("✅ Пост для самоанализа опубликован!")
#публикация отложенных постов
task = asyncio.create_task(send_scheduled_messages(2))
await task