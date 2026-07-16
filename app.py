import os
import json
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient, events

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # Токен из переменных Render
KEYS_FILE = "api_keys.json"

# ========== СОЗДАЕМ FLASK ДЛЯ RENDER ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Бот-генератор API ключей работает!"

# ========== ЛОГИКА БОТА ==========
async def bot_main():
    """Основная функция бота"""
    client = TelegramClient('bot_session', api_id=0, api_hash='')
    await client.start(bot_token=BOT_TOKEN)
    
    @client.on(events.NewMessage(pattern="/start"))
    async def start_handler(event):
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
    
    @client.on(events.NewMessage(pattern="/get_keys"))
    async def get_keys_handler(event):
        await event.respond(
            "📱 Введи свой номер телефона в международном формате:\n"
            "Пример: `+79123456789`",
            parse_mode="markdown"
        )
        
        # Ждем номер телефона
        @client.on(events.NewMessage(from_users=event.sender_id))
        async def phone_handler(msg):
            phone = msg.text.strip()
            
            if not phone.startswith("+"):
                await msg.respond("❌ Номер должен начинаться с `+`\nПопробуй еще раз.")
                return
            
            await msg.respond(f"⏳ Авторизуюсь под номером {phone}...")
            
            try:
                # Создаем клиент для авторизации пользователя
                user_client = TelegramClient(f"temp_{event.sender_id}", api_id=0, api_hash="")
                await user_client.start(phone=phone)
                
                # Получаем информацию
                me = await user_client.get_me()
                
                # Получаем API ключи
                keys = {
                    "api_id": user_client.api_id,
                    "api_hash": user_client.api_hash,
                    "username": me.username,
                    "first_name": me.first_name,
                    "phone": phone
                }
                
                # Сохраняем в файл
                with open(KEYS_FILE, "w") as f:
                    json.dump(keys, f, indent=2)
                
                await msg.respond(
                    f"✅ **Ключи получены!**\n\n"
                    f"📌 **API ID:** `{user_client.api_id}`\n"
                    f"📌 **API Hash:** `{user_client.api_hash}`\n\n"
                    f"👤 Аккаунт: @{me.username or 'нет'}\n"
                    f"📱 Номер: {phone}\n\n"
                    f"📁 Ключи сохранены в файл: `{KEYS_FILE}`\n\n"
                    f"⚠️ Никому не показывай эти ключи!",
                    parse_mode="markdown"
                )
                
                await user_client.disconnect()
                
            except Exception as e:
                await msg.respond(f"❌ Ошибка: {str(e)}")
            
            # Отключаем обработчик номера
            return
    
    @client.on(events.NewMessage(pattern="/help"))
    async def help_handler(event):
        await event.respond(
            "📖 **Команды:**\n"
            "/start - начать\n"
            "/get_keys - получить API ключи\n"
            "/help - эта справка"
        )
    
    @client.on(events.NewMessage(pattern="/keys"))
    async def show_keys_handler(event):
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
    
    await client.run_until_disconnected()

# ========== ЗАПУСК БОТА В ОТДЕЛЬНОМ ПОТОКЕ ==========
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_main())

if __name__ == "__main__":
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    print("🤖 Бот запущен!")
    
    # Запускаем Flask для Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
