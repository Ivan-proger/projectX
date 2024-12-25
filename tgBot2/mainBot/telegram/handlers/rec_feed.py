"""
Лента рекомендаций и ее создание выдача пользователю, ее прокрутка
"""

import aiohttp
import io
import json
import string
import random
from telebot.async_telebot import AsyncTeleBot
from telebot import types

from django.core.cache import cache
from django.contrib.gis.geos import Point
from django.db.models import Q, F
from django.contrib.gis.measure import D

from mainBot.models import * # импорт всех моделей Django
from mainBot.telegram.bot import set_user_state, get_message_text, anketa_text
from mainBot.telegram.keyboards import *
from mainBot.telegram.geo_utils import geocode


# Закодирование id канала чтобы нельзя было подсмотреть через кнопку 
BASE62_ALPHABET = string.digits + string.ascii_letters

async def encode_base62(number):
    """Кодирование числа в Base62."""
    if number == 0:
        return BASE62_ALPHABET[0]
    
    is_negative = number < 0
    number = abs(number)
    base62 = []
    
    while number:
        number, rem = divmod(number, 62)
        base62.append(BASE62_ALPHABET[rem])
    
    encoded = ''.join(reversed(base62))
    return f"-{encoded}" if is_negative else encoded

async def decode_base62(base62):
    """Декодирование Base62 в число."""
    is_negative = base62[0] == "-"
    if is_negative:
        base62 = base62[1:]
    
    number = 0
    for char in base62:
        number = number * 62 + BASE62_ALPHABET.index(char)
    
    return -number if is_negative else number


#! Генерация ленты рекомендаций
async def generate_recommendations(user: User) -> list: 
    #try:
    # Извлечение истории просмотра из Django Cache
    viewed_channels = await cache.aget(f"user:{user.external_id}:viewed", [])
    channels = Channel.objects.filter(is_work=True).exclude(external_id__in=viewed_channels)

    # Учет геолокации
    if user.region:
        channels = channels.filter(
            Q(region=user.region) | Q(location__distance_lte=(Point(user.location), D(km=50)))
        )
    else:
        channels = channels.all()

    # Учет категорий пользователя
    user_categories = user.categories.all()
    if await user_categories.aexists():
        interest_based = channels.filter(categories__in=user_categories).distinct()
    else:
        interest_based = Channel.objects.none()

    # Выборка каналов по интересам (70%)
    interest_based_count = int(0.7 * 10)  # 70% от 10 рекомендаций
    interest_based = list(interest_based.order_by("-add_time")[:interest_based_count].all())

    # Выборка случайных каналов (30%)
    random_count = 10 - len(interest_based)
    all_channels = [ch async for ch in channels.exclude(id__in=[ch.id for ch in interest_based]).all()]
    random_channels = random.sample(all_channels, min(random_count, len(all_channels)))

    # Объединение списков
    combined_recommendations = interest_based + random_channels
    random.shuffle(combined_recommendations)  # Перемешиваем для разнообразия

    return combined_recommendations
    # except Exception as e:
    #     print(f"Ошибка при генерации рекомендаций: {e}")
    #     return []

# Реакция на кнопку ждя создания ленты
async def callback_feed_start(call: types.CallbackQuery, bot: AsyncTeleBot, user: User = None):
    """call.data == 'callback_feed_start'"""
    await recommendations_feed(call.message, bot, call.from_user.id, user)

async def recommendations_feed(message: types.Message, bot: AsyncTeleBot, user_id, user: User = None):
    """
    Функция по построению ленты и выдачи постов
    """
    # Убираем клавиатуру чтобы больше не нажимал
    # await bot.edit_message_reply_markup(
    #     message.chat.id,
    #     message.id,
    #     reply_markup=None
    # )

    recommendations = await cache.aget(f'{user_id}-recommendations')
    # -Рекомендации-
    if not recommendations or len(recommendations) == 0:
        if not user or user == True:
            recommendations = await generate_recommendations(await User.objects.aget(external_id=user_id))
        else:
            recommendations = await generate_recommendations(user)
        # Сохраняем в кэш список рекомендаций     
        await cache.aset(f'{user_id}-recommendations', recommendations, 60*60)



    # Берем канал для отправки
    channel = recommendations[0]
    # Удаялем
    recommendations.pop(0) 
    await cache.aset(f'{user_id}-recommendations', recommendations, 60*60)
    
    caption = anketa_text(
        channel.name,
        channel.description,
        channel.folowers,
        channel.region,
        channel.likes,
        channel.dislikes
    )
    
    #! Отправить несколько фото
    imges = channel.poster.split()
    imges_input = []
    for img in imges:
        imges_input.append(types.InputMediaPhoto(img, caption, parse_mode='HTML'))

    msg = await bot.send_media_group(
        message.chat.id, 
        imges_input
    )

    await bot.edit_message_caption(
        caption,
        message.chat.id,
        msg[0].id,
        reply_markup=(await keyboard_post(await encode_base62(channel.external_id))),
        parse_mode='HTML'
    )

# Dislike:
async def callback_dislike(call: types.CallbackQuery, bot: AsyncTeleBot, user: User = None):
    """ call.data.startswith("dislike_post-") """
    # Убираем клавиатуру чтобы больше не нажимал
    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.id,
        reply_markup=None
    )    

    hash_code = call.data.split('+')[1]
    channel_id = await decode_base62(hash_code)

    # Обновляем
    await Channel.objects.filter(external_id=channel_id).aupdate(dislikes=F("dislikes") + 1)

    await recommendations_feed(call.message, bot, call.from_user.id, user)

# Like:
async def callback_like(call: types.CallbackQuery, bot: AsyncTeleBot, user: User = None):
    """ call.data.startswith("like_post-") """
    hash_code = call.data.split('+')[1]
    channel_id = await decode_base62(hash_code)

    # Обновляем
    await Channel.objects.filter(external_id=channel_id).aupdate(likes=F("likes") + 1)


    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            "Ссылка", 
            url=f't.me/{(await bot.get_chat(channel_id)).username}'
            )
    )
    # Убираем клавиатуру чтобы больше не нажимал
    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.id,
        reply_markup=keyboard
    )    

    await recommendations_feed(call.message, bot, call.from_user.id, user)