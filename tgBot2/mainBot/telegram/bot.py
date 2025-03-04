# Компилирующий файл бота и вызывающий обработчики
import asyncio
import telebot
import json
from telebot.async_telebot import AsyncTeleBot, ExceptionHandler
from django.conf import settings
from django.core.cache import cache


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
        messages = cache.get('messages')
    else:
        messages=None    
    if not messages:
        # Загрузка сообщений из JSON-файла
        with open('messages.json', 'r', encoding='utf-8') as file:
            messages = json.load(file)
            cache.set('messages', messages, None) # Ставим в кэш навсегда

    return messages.get(language, {}).get(message_key, {}).get(version, "Message not found")    


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
