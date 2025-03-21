from telebot.async_telebot import AsyncTeleBot
from telebot import types

from mainBot.telegram.keyboards import murkup_keboard_stay

from mainBot.midleware.cache_tools import set_user_state
from mainBot.midleware.text_tools import get_message_text

#! Общая функция для стопа
async def stop_action(message: types.Message, bot: AsyncTeleBot):
    """ Если пользователь хочет выйти из действия -- True иначе False - не хочет """

    if message.text == await get_message_text("absolute_messages", "stop"):
        await set_user_state(message.from_user.id, None)
        await bot.send_message(
            chat_id=message.chat.id,
            text=await get_message_text("absolute_messages", "stop"),
            parse_mode="HTML",
            reply_markup=await murkup_keboard_stay()
        ) 

        return True  
    return False  