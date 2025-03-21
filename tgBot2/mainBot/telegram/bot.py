# Компилирующий файл бота и вызывающий обработчики
import asyncio
import telebot
import json
import re
from telebot.async_telebot import AsyncTeleBot, ExceptionHandler
from django.conf import settings
from django.core.cache import cache, caches

from mainBot.models import СategoryChannel

API_TOKEN = settings.BOT_TOKEN
WEBHOOK_URL = f'{settings.WEBHOOK_BASE_URL}/webhook/'  # Укажите полный URL вашего вебхука


# Инициализация асинхронного бота
if settings.DEBUG:
    import logging #дебаг режим
    logger = telebot.logger
    telebot.logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.
    class MyExceptionHandler(ExceptionHandler):
        async def handle(self, exception):
            logger.error(exception)
    bot = AsyncTeleBot(settings.BOT_TOKEN, exception_handler=MyExceptionHandler())
else:
    bot = AsyncTeleBot(settings.BOT_TOKEN)

#! Текст постов
def anketa_text(title, description, count_people, city=None, likes=0, dislikes=0):
    text= f'''
> <b>{title}</b>
{f'\n⊹ <i>{description}</i> ⊹\n' if description else ''}
{f'\n🌆 {city}' if city else ''}
👥 <b>{count_people}</b>   💖 <b>{likes}</b>   👎 <b>{dislikes}</b>

(с) НАш крутой бот 
        '''      
    return text

#! Логика филтрации текста
async def ban_words_cheking(text):

    # Регулярное выражение для поиска ссылок
    link_pattern = r"(?i)(https?://[^\s<>\"']+|www\d{0,3}\.[^\s<>\"']+|t\.me/[^\s<>\"']+|@[\w\d_]+)"
    if re.search(link_pattern, text):
        return await get_message_text("errors", "ban_link")

    ban_words = await cache.aget("ban_words")
    if not ban_words:
        # Выгружаем файл с запретками
        with open("ban_words.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            ban_words = set(data.get("prohibited_words", []))  # Используем set для быстрого поиска
            await cache.aset("ban_words", ban_words, None)       

    # Проверка текста на наличие запрещённых слов
    found_words = [word for word in ban_words if word.lower() in text.lower()]
    if found_words:
        return await get_message_text("errors", "ban_words_text") + f"{', '.join(found_words)}."
        
    return None  
#! Вытаскиваем текст из анкеты   
async def extract_text(post_text, start_token, end_token):
    start = post_text.find(start_token)
    end = post_text.find(end_token, start)

    if start != -1 and end != -1:
        # Извлекаем описание между маркерами
        return post_text[start + len(start_token):end].strip()
    return None   
async def extract_link(text, start_symbols='t.me/'):
    # Для получения ссылки в анкете
    for line in text.splitlines():
        if line.startswith(start_symbols):
            return line[len(start_symbols):].split()[0]
    return None

#! FSM
async def get_user_state(user_id): # Получить статус
    state = await cache.aget(f"user_state:{user_id}")
    if state:
        return state
    return False
async def set_user_state(user_id, state, time=60*25): # Установить
    if state == None:
        cache.delete(f"user_state:{user_id}")
    else:    
        await cache.aset(f"user_state:{user_id}", state, time)

#! метод для messages.json 
async def get_message_text(message_key: str, version: str, language: str='ru') -> str:
    if not settings.DEBUG:
        messages = await caches['redis'].aget('messages')
    else:
        messages=None    
    if not messages:
        # Загрузка сообщений из JSON-файла
        with open('messages.json', 'r', encoding='utf-8') as file:
            messages = json.load(file)
            await caches['redis'].aset('messages', messages, None) # Ставим в кэш навсегда

    return messages.get(language, {}).get(message_key, {}).get(version, "Message not found")    

#! Кэш категорий
async def category_cache() -> list:
    category_cache = await caches['redis'].aget(f'category_Channel_cache')
    if not category_cache:   # Кэшируем базу 
        category_cache = [user async for user in СategoryChannel.objects.all()]
        await caches['redis'].aset(
            f'category_Channel_cache', 
            category_cache, 
            1 if settings.DEBUG else None
            )
    return category_cache


#! Подключаем наш register_handlers.py
from .register_handlers import register_handlers
register_handlers(bot)


#! Проверка и установка вебхука
async def ensure_webhook():
    webhook_info = await bot.get_webhook_info(5)
    # Проверяем, установлен ли вебхук на нужный URL
    if webhook_info.url == WEBHOOK_URL:
        print(f"\nВебхук уже установлен на {WEBHOOK_URL}, ничего не делаем.\n")
    else:
        # Если вебхук отличается или не установлен, удаляем его и создаём новый
        print(f"\n -- Текущий вебхук: {webhook_info.url}. Ожидаемый: {WEBHOOK_URL}. Переустанавливаем...")
        await bot.remove_webhook()
        await asyncio.sleep(1)  # Небольшая пауза для надежности
        await bot.set_webhook(url=WEBHOOK_URL)
        print(f"✅ Новый вебхук установлен на {await bot.get_webhook_info()}\n")
    # Закрытие сессии
    await bot.close_session()    
