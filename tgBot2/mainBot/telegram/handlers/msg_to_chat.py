# Ответы на обычные команды в чат пользователем из маркап клавиатуры

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from django.core.cache import cache

from mainBot.models import * # импорт всех моделей Django
from mainBot.telegram.bot import get_user_state, set_user_state, get_message_text, anketa_text
from mainBot.telegram.keyboards import *
from mainBot.telegram.handlers.rec_feed import *

async def check_message_comannds(message: types.Message, bot: AsyncTeleBot, user: User = None):
    text = message.text
    if text == await get_message_text('keyboards', 'callback_feed_start'):
        await recommendations_feed(message, bot, message.from_user.id, user)
    pass

