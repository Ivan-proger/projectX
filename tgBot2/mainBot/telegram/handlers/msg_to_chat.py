# Ответы на обычные команды в чат пользователем из маркап клавиатуры

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from django.core.cache import cache


from mainBot.telegram.bot import get_message_text, anketa_text, category_cache, ban_words_cheking, extract_text
from mainBot.telegram.keyboards import *
from mainBot.telegram.handlers.rec_feed import recommendations_feed

from django.contrib.gis.geos import Point

from mainBot.models import * # импорт всех моделей Django


async def check_message_comannds(message: types.Message, bot: AsyncTeleBot, user: User = None):
    text = message.text
    # Лента кнопка внизу
    if text == await get_message_text('keyboards', 'callback_feed_start'):
        await recommendations_feed(message, bot, message.from_user.id, user)
    # Изминение профиля 
    elif text == await get_message_text('keyboards', 'menu_change_profile'):
        await change_post(message, bot, user)

# Изменить пост
async def change_post(message: types.Message, bot: AsyncTeleBot, user: User = None):
    if not user or user == True:
        user = await User.objects.aget(external_id=message.from_user.id)
    channels =[channel async for channel in user.channels.all()]
    if len(channels) == 1:
        channel = channels[0]
        # Сохраняем данные о канале (сохраняем названия кэша чтобы не баголась клавиатура)
        await cache.aset(f"{message.from_user.id}-channel", channel, settings.CACHE_CREATE)
        await cache.aset(f'{channel.description}-descriptionChannal', settings.CACHE_CREATE)

        try:
            folowers = await bot.get_chat_member_count(channel.external_id)
        except : # Если не можем получить канал
            await bot.send_message(
                message.chat.id,  
                await get_message_text('errors', 'chahel_tg_not_found') + f'<code>{str(channel.external_id)}</code>', 
                parse_mode='HTML'
                )
            return True            

        await cache.aset(f'{message.from_user.id}-folowers', folowers, settings.CACHE_CREATE)
        text = anketa_text(
            channel.title, 
            channel.description, 
            folowers,
            channel.region,
            channel.likes,
            channel.dislikes
            )
        imges = channel.poster.split()

        # Устанавливаем кэш для клавиатуры
        await cache.aset(f'{message.from_user.id}-id_imgs', imges, settings.CACHE_CREATE)

        await bot.send_photo(
            message.chat.id,
            imges[0],
            text,
            'HTML',
            reply_markup=await keyboard_for_change_channel(message.from_user.id)
        )

#! Выпадающий список хэштегов тех же категорий канала
async def callback_change_channel_categories(call: types.CallbackQuery, bot: AsyncTeleBot, page=1):
    """call.data == "callback_change_channel_categories"""
    list_complite_ids = await cache.aget(f'{call.from_user.id}-list_complite_ids')
    channel = await cache.aget(f"{call.from_user.id}-channel")
    if not list_complite_ids:
        list_complite_ids = [ct.id async for ct in channel.categories.all()]
        await cache.aset(f'{call.from_user.id}-list_complite_ids', list_complite_ids, settings.CACHE_CREATE)

    category = await category_cache() 

    keyboard = await generate_paginated_keyboard(
        category, 
        page = page, 
        page_size = 5, 
        callback_prefix = 'categories',
        selected_ids = list_complite_ids if list_complite_ids else [],
        text_info = await get_message_text('keyboards', 'add_channel_complite_info'),
        is_chage=True
        )
    # Кнопка в конец чтобы завершить все
    keyboard.row(
        types.InlineKeyboardButton(
            await get_message_text('keyboards', 'add_channel_back'), 
            callback_data='change_channel_back_callback'),        

        types.InlineKeyboardButton(
            await get_message_text('keyboards', 'add_channel_complite'), 
            callback_data='complete_change_channel_categories')
        )
    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.id,
        reply_markup=keyboard
    )
    await bot.answer_callback_query(
        call.id,
        await get_message_text('keyboards', 'add_channel_complite_info')
    )
#* Возращение назад к старой клавиатуре    
async def change_channel_back_callback(call: types.CallbackQuery, bot: AsyncTeleBot):
    """call.data == change_channel_back_callback"""
    await bot.edit_message_caption(
        caption=call.message.caption,
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        reply_markup=await keyboard_for_change_channel(call.from_user.id),
        parse_mode='HTML'
    )

#! Сохранение категорий канала
async def complete_change_channel_categories(call: types.CallbackQuery, bot: AsyncTeleBot):
    #todo ДОБАВИТЬ ОГРАНЕЧЕНИЯ НА ИЗМЕНЕНИЯ КАТЕГОРИЙ
    channel = await cache.aget(f"{call.from_user.id}-channel")
    # Категории канала
    list_complite_ids = await cache.aget(f'{call.from_user.id}-list_complite_ids')
    if list_complite_ids:
        # Добавляем все тэги(категории)
        category_added = []
        for category in await category_cache():
            for id in list_complite_ids:
                if category.id == id:
                    category_added.append(category) 
        await channel.categories.aset(category_added) # Финально перезаписываем
                
        print(f'\n\n {[ct.id async for ct in channel.categories.all()]} \n\n')
    await bot.answer_callback_query(
        call.id,
        await get_message_text('general', 'change_complete_categories'),
        True
    )
    await change_channel_back_callback(call, bot)

#! Callback для сохранения изменений канала
async def change_channel_complete(call: types.CallbackQuery, bot: AsyncTeleBot):
    channel = await cache.aget(f"{call.from_user.id}-channel")
    if not channel: # Если пользователь тупой
        await bot.send_message(
            call.message.chat.id,  
            await get_message_text('errors', 'cache_channel'), 
            parse_mode='HTML'
            )
        return True
    
    # Вытаскиваем текст
    title = await extract_text(call.message.caption, '>', '\n')
    description = await extract_text(call.message.caption, '⊹ ', ' ⊹')

    error = await ban_words_cheking(f'{title} \n{description}')
    if error:   #* Проверяем запрещенку
        await bot.answer_callback_query(
            call.id, # Вывод ошибки в лицо
            error,
            True
        )
        text = call.message.caption + '\r\n\r\n' + error
        keyboard = await update_keyboard_warning(call, 'add_channel_complite', 2) # Доп отдача юзеру
        # Показываем ошибку путем изменения текста в анкете
        if not (error in call.message.caption.split('\n')) and call.message.reply_markup != keyboard:
            await bot.edit_message_caption(
                caption = text,
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                reply_markup=keyboard,
                parse_mode='html'
            )
        return True

    if title != channel.title:
        channel.title = title if title else ""  # Сохраянем текст 
    if description != channel.description:
        channel.description = description if description else ""

    # Город и координаты
    city_data = await cache.aget(f'{call.from_user.id}-location')
    if city_data:
      # Добавляем регион/город
        channel.region = city_data['address']
        channel.location = Point(city_data['longitude'], city_data['latitude'])        
    
    # Несколько фото профиля
    id_imgs = await cache.aget(f'{call.from_user.id}-id_imgs')
    if id_imgs:
        poster = ' '.join(id_imgs)
        channel.poster = poster
    else:
        poster = call.message.photo[-1].file_id
        if channel.poster != poster:
            channel.poster = poster

    # Категории канала
    list_complite_ids = await cache.aget(f'{call.from_user.id}-list_complite_ids')
    if list_complite_ids:
        category_added = []
        for category in await category_cache():
            for id in list_complite_ids:
                if category.id == id:
                    category_added.append(category) 
        await channel.categories.aset(category_added) # Финально перезаписываем
    
    # Завершаем сохранение отдаем отдачу юзеру
    await bot.delete_message(call.message.chat.id, call.message.id)
    await bot.answer_callback_query(
        call.id,
        await get_message_text('general', 'change_complete'),
        True
    )

    await channel.asave() #! Сохраняем

    # Очистка кэша:
    cache.delete(f'{call.from_user.id}-channel')
    cache.delete(f'{call.from_user.id}-descriptionChannal')
    cache.delete(f'{call.from_user.id}-id_message')
    cache.delete(f'{call.from_user.id}-id_botmessage')
    cache.delete(f'{call.from_user.id}-list_complite_ids')
    cache.delete(f'{call.from_user.id}-location')
    cache.delete(f'{call.from_user.id}-stock_img')
    cache.delete(f'{call.from_user.id}-id_img_select')
