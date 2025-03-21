import json
import re

from django.conf import settings
from django.core.cache import cache, caches

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