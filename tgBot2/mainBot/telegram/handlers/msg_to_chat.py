# Ответы на обычные команды в чат пользователем из маркап клавиатуры

from telebot.async_telebot import AsyncTeleBot
from telebot import types
from django.core.cache import cache

from mainBot.telegram.bot import get_user_state, set_user_state, get_message_text, anketa_text
from mainBot.telegram.keyboards import *
from mainBot.telegram.handlers.rec_feed import *
from mainBot.telegram.handlers.adding_profile import *
from mainBot.models import * # импорт всех моделей Django

async def check_message_comannds(message: types.Message, bot: AsyncTeleBot, user: User = None):
    text = message.text
    # Лента кнопка внизу
    if text == await get_message_text('keyboards', 'callback_feed_start'):
        await recommendations_feed(message, bot, message.from_user.id, user)
    # Изминение профиля 
    elif text == await get_message_text('keyboards', 'menu_change_profile'):
        await change_post(message, bot, user)


async def change_post(message: types.Message, bot: AsyncTeleBot, user: User = None):
    #if not user:
    user = await User.objects.aget(external_id=message.from_user.id)
    channels =[channel async for channel in user.channels.all()]
    if len(channels) == 1:
        channel = channels[0]
        # Сохраняем данные о канале (сохраняем названия кэша чтобы не баголась клавиатура)
        await cache.aset(f"{message.from_user.id}-channel", channel, 60*25)
        await cache.aset(f'{channel.description}-descriptionChannal', 60*25)
        folowers = await bot.get_chat_member_count(channel.external_id)
        await cache.aset(f'{message.from_user.id}-folowers', folowers, 25*60)
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
        await cache.aset(f'{message.from_user.id}-id_imgs', imges, 25*60)

        await bot.send_photo(
            message.chat.id,
            imges[0],
            text,
            'HTML',
            reply_markup=await keyboard_for_change_channel(message.from_user.id)
        )
# Callback для сохранения изменений канала
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
        # Добавляем все тэги(категории)
        async for category in await category_cache():
            await channel.categories.aadd(category)

    await channel.asave() #! Сохраняем


