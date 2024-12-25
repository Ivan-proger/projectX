from telebot.async_telebot import AsyncTeleBot
from telebot import types

from mainBot.telegram.handlers.rec_feed import *
from mainBot.telegram.handlers.adding_profile import *
from mainBot.telegram.handlers.commands import *


#! Oбновление последней активности
async def update_activity(external_id):
    user_last_activity = await cache.aget(f'activity-{external_id}')
    current_date = timezone.now()
    if not user_last_activity:
        if await cache.aget(f'ban-{external_id}'):
            return False # Выйти сразу
        # Получаем юзера
        user = await User.objects.aget(external_id=external_id) 

        if user.is_ban:
            await cache.aset(f'ban-{external_id}', True, 60*60*2)
            return False # Выйти сразу
        user_last_activity = user.last_activity 

        # Премиум
        if user.premium:
            await cache.aset(f'{external_id}-premium', True, 60*2+1)

        await cache.aset(f'activity-{external_id}', current_date, 60*2) 
        if user_last_activity.day != current_date.day: #Собираем статистику уникальных пользователей за день
            # Получение записи по текущей дате
            service_usage, create = await ServiceUsage.objects.aget_or_create(
                date=current_date,
                defaults={
                    'count': 1,
                    }
                )
            if not create:
                service_usage.count += 1
                await service_usage.asave()   
        await user.update_last_activity() # Обновляем в бд  
        # Вернем пользователя вдруг пригодится
        return user
    return True  


def register_handlers(bot: AsyncTeleBot):
    bot.register_message_handler(start_and_register, 
                                 commands=['start'], 
                                 pass_bot=True, 
                                 func=lambda message: message.chat.type == "private") # Команда старт
    bot.register_message_handler(test_rabbit, 
                                 commands=['rb'], 
                                 pass_bot=True,
                                 func=lambda message: message.chat.type == "private") # Команда тестовая

    #* Обработчик просто сообщений
    async def pass_function(message: types.Message, bot: AsyncTeleBot):
        user = await update_activity(message.from_user.id)
        if user:
            state = await get_user_state(message.from_user.id)
            if not state:
                await echo_handler(message, bot)
            elif state == 'comment':
                await comment_send(message, bot, user)
            elif state == 'add_channel_img_chat':
                await add_channel_img_chat_chat(message, bot)
            elif state == 'add_channel_description_chat':
                await add_channel_description_chat_chat(message, bot)
            elif state == "add_channel_parsing":
                await add_channel_parsing(message, bot)
            elif state == "add_channel_location_callback":
                await add_channel_location(message, bot)
        else:
            await ban_handler(message, bot)
    bot.register_message_handler(
        pass_function, 
        pass_bot=True, 
        content_types=['text', 'photo', 'location'], 
        func=lambda message: message.chat.type == "private" # Только личные сообщения
        )
    
    #* Колбэк оbработчик
    async def callback_pass_function(call: types.CallbackQuery, bot: AsyncTeleBot):
        user = await update_activity(call.from_user.id)
        if user:
            # Like/Dislike
            if call.data.startswith("dislike_post+"):
                await callback_dislike(call, bot, user)
            elif call.data.startswith("like_post+"):
                await callback_like(call, bot, user) 

            # Статус 'comment'
            elif call.data.startswith('comment_post+'):   
                await  comment_status(call, bot)

            # Лента из кнопки
            elif call.data == "callback_feed_start":
                await callback_feed_start(call, bot, user)

            # Добавить тгк начала из /start
            elif call.data == "add_channel_start":
                await callback_add_channel_start(call, bot)

            # Добавить из профиля канал
            elif call.data == "add_channel_bio":
                await callback_add_channel_bio(call, bot)

            # Изменить описание
            elif call.data == "add_channel_description_chat":
                await add_channel_description_chat(call, bot)

            # Добавить/изменить кастомное фото
            elif call.data == "add_channel_img_chat":
                await add_channel_img_chat(call, bot)

            # Добавит через админа бота в тгк
            elif call.data == "add_channel_parsing":
                await callback_add_channel_parsing(call, bot)
            
            # Добавить город к анкете
            elif call.data == "add_channel_location":
                await add_channel_location_callback(call, bot)
            elif call.data =='message_complite': # Подтвепждение 
                await add_channel_location_complite(call, bot)    
            elif call.data == 'message_close':
                await add_channel_location_close(call, bot)

            # Финальное добавление канала
            elif call.data == "add_channel_complite":
                await callback_add_channel_complite(call, bot)

            # Финальное добавление канала--Выпадающий список категорий
            elif call.data == "add_channel_precomplite":
                await callback_add_channel_categories(call, bot) 

            # страницу переключаем 
            elif call.data.startswith('categories:page'):
                data = call.data.split(":")
                page = int(data[2])
                await callback_add_channel_categories(call, bot, page)
            elif call.data.startswith('categories:'):     
                await callback_categories_add(call, bot)
            elif call.data == 'add_channel_back':
                await add_channel_back_callback(call, bot)
            
            

        else:
            await ban_handler(call.message, bot)
    bot.register_callback_query_handler(callback_pass_function, pass_bot=True, func=lambda call: True)