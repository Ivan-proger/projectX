from telebot.async_telebot import AsyncTeleBot
from telebot import types

from mainBot.telegram.handlers.rec_feed import *
from mainBot.telegram.handlers.adding_profile import *
from mainBot.telegram.handlers.commands import *
from mainBot.telegram.handlers.msg_to_chat import *
from mainBot.midleware.cache_tools import get_user_state, set_user_state
from mainBot.models import *

#! Oбновление последней активности
async def update_activity(external_id, message: types.Message, bot: AsyncTeleBot):
    user_last_activity = await caches['redis'].aget(f'activity-{external_id}')
    current_date = timezone.now()

    if not user_last_activity:
        if await caches['redis'].aget(f'ban-{external_id}'):
            return False # Выйти сразу
        # Получаем юзера
        user = await User.objects.filter(external_id=external_id).afirst()

        if not user:
            await bot.send_message(
                chat_id = message.chat.id,
                text=await get_message_text("errors", "user_not_found"),
                parse_mode='HTML'
            )
            return False

        if user.is_ban:
            await caches['redis'].aset(f'ban-{external_id}', True, 60*60*2)
            await ban_handler(message, bot)
            return False # Выйти сразу
        user_last_activity = user.last_activity 

        # Премиум
        if user.premium:
            await caches['redis'].aset(f'{external_id}-premium', True, 60*2+1)

        await caches['redis'].aset(f'activity-{external_id}', current_date, 60*2) 
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
        user = await update_activity(message.from_user.id, message, bot)
        if user:
            state = await get_user_state(message.from_user.id)
            if not state:
                if message.text == await get_message_text("absolute_messages", "stop"):
                    await stop_action(message, bot)
                await check_message_comannds(message, bot, user)
            else:
                if await stop_action(message, bot):
                    # Выход из любой активности с помощью сообщения 'Отмена'
                    msgs = await cache.aget(f'{message.from_user.id}-id_botmessage') 
                    await bot.delete_messages(
                        message.chat.id, 
                        ([message.id] + msgs) if msgs else [message.id]
                        )                     
                    cache.delete(f'{message.from_user.id}-comment-tg')
                    cache.delete(f'{message.from_user.id}-id_botmessage')
                    await set_user_state(message.from_user.id, None)                      
                    return True
                
                elif state == 'comment':
                    await comment_send(message, bot, user)
                elif state == 'add_channel_img_chat':
                    await add_channel_img_chat_chat(message, bot)
                elif state == 'add_channel_more_img_chat':
                    await add_channel_more_img_chat(message, bot)
                elif state == 'add_channel_description_chat':
                    await add_channel_description_chat_chat(message, bot)
                elif state == "add_channel_parsing":
                    await add_channel_parsing(message, bot)
                elif state == "add_channel_location_callback":
                    await add_channel_location(message, bot)

    bot.register_message_handler(
        pass_function, 
        pass_bot=True, 
        content_types=['text', 'photo', 'location'], 
        func=lambda message: message.chat.type == "private" # Только личные сообщения
        )
    
    #* Колбэк оbработчик
    async def callback_pass_function(call: types.CallbackQuery, bot: AsyncTeleBot):
        user = await update_activity(call.from_user.id, call.message, bot)
        if user:
            # Like/Dislike
            if call.data.startswith("dislike_post:"):
                await callback_dislike(call, bot, user)
            elif call.data.startswith("like_post:"):
                await callback_like(call, bot, user) 
            
            # Переключение фотографий
            elif call.data.startswith('imgs:'):
                await swap_imgs(call, bot)

            # Статус 'comment'
            elif call.data.startswith('comment_post:'):   
                await  comment_status(call, bot)

            # Отправить жалобу
            elif call.data.startswith("complaint_post:"):
                await complite_category_collback(call, bot)
            elif call.data.startswith("complite_tags:"): # Реакцию на кнопку только
                await complite_category_choice(call, bot)
            elif call.data.startswith("tags_complite:"): # Финал
                await complite_category_complite(call, bot, user)

            # Кнопка назад в оценку анкеты
            elif call.data.startswith('feed_back'):
                await feed_back_collback(call, bot)    

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

            # Изменить кастомное фото
            elif call.data == "add_channel_img_chat":
                await add_channel_img_chat(call, bot)
            # Добавить фото    
            elif call.data == "add_channel_more_img":
                await add_channel_more_img(call, bot)
            # Удалить второстпенные фото
            elif call.data == "add_channel_delete_imgs":
                await add_channel_delete_imgs(call, bot)
            elif call.data.startswith('add_imgs:'):
                await add_channel_swap_imgs(call, bot)

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

            # Подтверждение на редактирование канала
            elif call.data == 'change_channel_complete':
                await change_channel_complete(call, bot)

            # Финальное добавление канала
            elif call.data == "add_channel_complite":
                await callback_add_channel_complite(call, bot)

            # Финальное добавление канала--Выпадающий список категорий
            elif call.data == "add_channel_precomplite":
                await callback_add_channel_categories(call, bot) 
            
            # Выбор для изменений категорий у канала
            elif call.data == "callback_change_channel_categories":
                await callback_change_channel_categories(call, bot)

            # страницу переключаем 
            elif call.data.startswith('categories:page'):
                data = call.data.split(":")
                page = int(data[2])
                if len(data) == 4:
                    await callback_add_channel_categories(call, bot, page)
                else:
                    await callback_change_channel_categories(call, bot, page)    
                    
            elif call.data.startswith('categories:'):     
                await callback_categories_add(call, bot)
            elif call.data == 'add_channel_back':
                await add_channel_back_callback(call, bot)
            
            # Назад к редактированию
            elif call.data == "change_channel_back_callback":
                await change_channel_back_callback(call, bot)
            # Сохранение категорий внутри их списка редактирования 
            elif call.data == "complete_change_channel_categories":
                await complete_change_channel_categories(call, bot)

    bot.register_callback_query_handler(callback_pass_function, pass_bot=True, func=lambda call: True)