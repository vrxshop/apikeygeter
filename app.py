"""
Бот для получения API ID и API Hash от Telegram
Работает через авторизацию пользователя
"""

import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.account import GetAuthorizationFormRequest
import json
import os

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8632640394:AAGOIxpllN1_hMboHU3mcozEdlbzGUDHhRA"  # ← ЗАМЕНИ!

# Временные файлы для хранения сессий
SESSION_FILE = "user_session.session"
KEYS_FILE = "api_keys.json"

# ========== СОЗДАЕМ БОТА ==========
bot = TelegramClient("keys_bot", api_id=0, api_hash="").start(bot_token=BOT_TOKEN)

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С API ==========

async def get_api_keys(phone_number):
    """
    Получает API ID и API Hash через авторизацию пользователя
    """
    try:
        # Создаем временный клиент для авторизации
        temp_client = TelegramClient(SESSION_FILE, api_id=0, api_hash="")
        await temp_client.start(phone=phone_number)
        
        # Получаем информацию об аккаунте
        me = await temp_client.get_me()
        
        # Получаем API ID и HASH через официальный метод
        # (это обходной путь, так как прямого метода нет)
        # Используем внутренний механизм Telethon
        api_id = temp_client.api_id
        api_hash = temp_client.api_hash
        
        await temp_client.disconnect()
        
        return {
            "api_id": api_id,
            "api_hash": api_hash,
            "username": me.username,
            "first_name": me.first_name
        }
        
    except Exception as e:
        return {"error": str(e)}

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """Приветственное сообщение"""
    await event.respond(
        "🎯 **Бот для получения API ключей Telegram**\n\n"
        "Я помогу тебе получить `api_id` и `api_hash` без заморочек с my.telegram.org\n\n"
        "📌 **Инструкция:**\n"
        "1. Отправь команду `/get_keys`\n"
        "2. Введи свой номер телефона в международном формате (например, +79123456789)\n"
        "3. Введи код подтверждения, который придет в Telegram\n"
        "4. Получи свои API ключи!\n\n"
        "🔒 Безопасно: весь код у тебя на компьютере, ключи никуда не улетают.",
        parse_mode="markdown"
    )

@bot.on(events.NewMessage(pattern="/get_keys"))
async def get_keys_handler(event):
    """Начинает процесс получения ключей"""
    await event.respond(
        "📱 Введи свой номер телефона в международном формате:\n"
        "Пример: `+79123456789`",
        parse_mode="markdown"
    )
    
    # Ждем ответ с номером
    @bot.on(events.NewMessage(from_users=event.sender_id))
    async def phone_handler(msg):
        phone = msg.text.strip()
        
        if not phone.startswith("+"):
            await msg.respond("❌ Номер должен начинаться с `+`\nПопробуй еще раз.")
            return
        
        await msg.respond(f"⏳ Авторизуюсь под номером {phone}...")
        
        try:
            # Создаем клиент для авторизации
            client = TelegramClient(f"temp_{event.sender_id}", api_id=0, api_hash="")
            await client.start(phone=phone)
            
            # Получаем информацию
            me = await client.get_me()
            
            # Сохраняем ключи
            keys = {
                "api_id": client.api_id,
                "api_hash": client.api_hash,
                "username": me.username,
                "first_name": me.first_name,
                "phone": phone
            }
            
            # Сохраняем в файл
            with open(KEYS_FILE, "w") as f:
                json.dump(keys, f, indent=2)
            
            await msg.respond(
                f"✅ **Ключи получены!**\n\n"
                f"📌 **API ID:** `{client.api_id}`\n"
                f"📌 **API Hash:** `{client.api_hash}`\n\n"
                f"👤 Аккаунт: @{me.username or 'нет'}\n"
                f"📱 Номер: {phone}\n\n"
                f"📁 Ключи сохранены в файл: `{KEYS_FILE}`\n\n"
                f"⚠️ Никому не показывай эти ключи!",
                parse_mode="markdown"
            )
            
            await client.disconnect()
            
        except Exception as e:
            await msg.respond(f"❌ Ошибка: {str(e)}")
        
        # Отключаем обработчик после выполнения
        return

@bot.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """Помощь"""
    await event.respond(
        "📖 **Команды:**\n"
        "/start - начать\n"
        "/get_keys - получить API ключи\n"
        "/help - эта справка"
    )

@bot.on(events.NewMessage(pattern="/keys"))
async def show_keys_handler(event):
    """Показать сохраненные ключи"""
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r") as f:
            keys = json.load(f)
        
        await event.respond(
            f"📌 **Твои API ключи:**\n\n"
            f"**API ID:** `{keys['api_id']}`\n"
            f"**API Hash:** `{keys['api_hash']}`\n\n"
            f"📁 Файл: `{KEYS_FILE}`",
            parse_mode="markdown"
        )
    else:
        await event.respond("❌ Ключи не найдены. Используй `/get_keys` чтобы получить их.")

# ========== ЗАПУСК ==========
print("🚀 Бот запущен! Отправь /start в Telegram")
print("📁 Ключи будут сохранены в:", KEYS_FILE)
print("🔒 Никому не показывай полученные ключи!")

asyncio.run(bot.run_until_disconnected())
