"""
Команды для бота

"""
import uuid
from telebot.async_telebot import AsyncTeleBot
from telebot import types
#from django.core.cache import cache

from mainBot.models import * # импорт всех моделей Django
from mainBot.telegram.bot import get_user_state, set_user_state, get_message_text, anketa_text
from mainBot.telegram.keyboards import *

#! Ответ на /start
async def start_and_register(message: types.Message, bot: AsyncTeleBot):
    # Генерация уникального кода (12 символов)
    async def genering_code():
        code = str(uuid.uuid4())[:12] 
        if await User.objects.filter(ref_code=code).acount() == 0:
            return code
        else:
            await genering_code() # Опять по новой
    # Регистрация в бд 
    user, created = await User.objects.aget_or_create(
        external_id=message.from_user.id,    
        defaults={
            'name': message.from_user.username,  
        }
    )
    #await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    # Создаем клавиатуру
    keyboard = types.InlineKeyboardMarkup() 

    button1 = types.InlineKeyboardButton(
        text=await get_message_text('keyboards', 'add_channel_start'), callback_data=f"add_channel_start"
        )
    button2 = types.InlineKeyboardButton(
        text=await get_message_text('keyboards', 'callback_feed_start'), callback_data=f"callback_feed_start"
        )
        
    keyboard.row(button1,button2)
    await bot.send_message(
        message.chat.id, 
        await get_message_text('general', 'welcome'), 
        reply_markup=keyboard, 
        parse_mode='HTML'
        )

    if created:
        await bot.send_message(
            message.chat.id,
            await get_message_text('general', 'new_user'),
            parse_mode='HTML',
            reply_markup=await murkup_keboard_stay()
        )

        user.ref_code = await genering_code()
        if (" " in message.text) and created:
            if not user.invited_by:
                friend = await User.objects.aget(ref_code=message.text.split()[1])
                user.invited_by = friend
                friend.ref_people += 1
                await friend.asave()
        await user.asave()
    else:
        await set_user_state(message.from_user.id, None)        


# async def echo_handler(message: types.Message, bot: AsyncTeleBot):
#     await bot.send_message(message.chat.id, f"Вы сказали: {message.text} \r\n-- {await get_user_state(message.from_user.id)}")


#! BAN
async def ban_handler(message: types.Message, bot: AsyncTeleBot): 
    await bot.send_message(
        message.chat.id, 
        await get_message_text('errors', 'ban'), 
        parse_mode='HTML'
        )