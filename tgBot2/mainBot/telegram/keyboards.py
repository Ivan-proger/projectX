from telebot.types import *
from mainBot.models import СategoryComplaint, Channel
from django.core.cache import cache
from django.conf import settings

from mainBot.midleware.text_tools import get_message_text


async def complite_and_close():
    """Конопки 'Готово' и 'Отмена' под сообщениями"""
    return InlineKeyboardMarkup(row_width=2).row(
        InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_complite'), 
                                    callback_data='message_complite'),                         
        InlineKeyboardButton(await get_message_text("absolute_messages", "stop"), 
                                    callback_data='message_close'),
    )                                

#* Клавиатура для кнопки стоп
async def stop_message():
    return ReplyKeyboardMarkup(True).row(
        InlineKeyboardButton(await get_message_text("absolute_messages", "stop")))

#* Клавиатура для редактирования канала 
async def keyboard_add_chennal(user_id: int|str =None, number_img: int = 0) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    if user_id:
        id_imgs = await cache.aget(f'{user_id}-id_imgs')
        if number_img == 0:
            number_img = await cache.aget(f'{user_id}-id_img_select')
        if id_imgs:
            buttons = []
            for i in range(len(id_imgs)):
                if i != number_img:
                    buttons.append(InlineKeyboardButton(
                            f'{i+1}', callback_data=f'add_imgs:{i}'
                        )
                    )
                else:
                    buttons.append(InlineKeyboardButton(
                            f'📷', callback_data=f'trash123'
                        )
                    )                    
            keyboard.row(*buttons)
            # Удалить второстепенные фото
            keyboard.add(
                InlineKeyboardButton(
                    await get_message_text('keyboards', 'add_channel_delete_imgs'), 
                    callback_data='add_channel_delete_imgs'
                    )
                )
    
    keyboard.add( 
        # Добавить фото
        InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_img_chat'), 
                                   callback_data='add_channel_img_chat'),
        # Добавить еще фото
        InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_more_img'), 
                                   callback_data='add_channel_more_img'),                                   
        # Добавить описание                           
        InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_description_chat'), 
                                   callback_data='add_channel_description_chat'),
        # Добавить город                           
        InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_location'), 
                                   callback_data='add_channel_location'),                                   
        # Готово
        InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_complite'), 
                                   callback_data='add_channel_precomplite'),         
    )  
    return keyboard 

#* Изменение уже добавленого канала с помощью InlineKeyboardMarkup
async def keyboard_for_change_channel(user_id: int|str =None, n: int=0) -> InlineKeyboardMarkup:
    """ Редактирования канала """
    base_keyboard = await keyboard_add_chennal(user_id, n)

    if base_keyboard.keyboard:
        last_row = base_keyboard.keyboard[-1]
        if last_row:
            # Удаляем последнюю кнопку в последней строке
            last_row.pop()
            # Если строка стала пустой, удаляем её
            if not last_row:
                base_keyboard.keyboard.pop()

    base_keyboard.add(
        InlineKeyboardButton(await get_message_text('keyboards', 'change_categories'), 
                                   callback_data='callback_change_channel_categories'),                   
    )

    base_keyboard.row(
        # Готово
        InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_complite'), 
                                   callback_data='change_channel_complete'),           
    )

    return base_keyboard

#* Функция для обновления клавиатуры с добавлением смайлика к кнопке
async def update_keyboard_warning(call: CallbackQuery, callback_data, row_width=1):
    # Получаем текущую клавиатуру из сообщения
    keyboard = call.message.reply_markup
    # Перебираем кнопки и добавляем смайлик к нажатой кнопке
    updated_keyboard = InlineKeyboardMarkup(row_width=row_width)
    for buttons in keyboard.keyboard:
        for button in buttons:
            if button.callback_data == callback_data:
                # Добавляем смайлик "осторожно" к тексту нажатой кнопки
                if str(button.text[0]) != str('⚠️')[0]:
                    updated_button = InlineKeyboardButton(text=f"⚠️ {button.text}", callback_data=button.callback_data)
                else:
                    updated_button = button    
            else:         
                updated_button = InlineKeyboardButton(text=button.text, callback_data=button.callback_data)
            updated_keyboard.add(updated_button)

    return updated_keyboard

# Метод для генерации пагинированной клавиатуры
async def generate_paginated_keyboard(items, page, page_size, callback_prefix, selected_ids=[], text_info=None, is_chage=False):
    """
    Генерация inline-клавиатуры с пагинацией.
    
    :param items: Список объектов.
    :param page: Номер текущей страницы (от 1).
    :param page_size: Количество объектов на странице.
    :param callback_prefix: Префикс callback данных.
    :return: InlineKeyboardMarkup.
    """
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = items[start_idx:end_idx]
    
    keyboard = InlineKeyboardMarkup()
    # Добавляем для информации кнопку
    if text_info:
        keyboard.row(InlineKeyboardButton(
            text_info, 
            callback_data=f"trash123"
            )
        )            

    buttons = []
    for item in page_items:
        button = InlineKeyboardButton(
            text=f"{item.name} {'✅' if item.id in selected_ids else ''}",  # Отображаемое название объекта
            callback_data=f"{callback_prefix}:{item.id}:page:{page}{':change' if is_chage else ''}"  # Метаданные
        )
        buttons.append(button)
    keyboard.add(*buttons, row_width=2)
    
    button_next = InlineKeyboardButton(
        "➡️", 
        callback_data=f"{callback_prefix}:page:{page+1}{':change' if is_chage else ''}"
        )
    button_back = InlineKeyboardButton(
        "⬅️", 
        callback_data=f"{callback_prefix}:page:{page-1}{':change' if is_chage else ''}"
        )
    button_no = InlineKeyboardButton(
        "📛", 
        callback_data=f"trash123"
        )
    # Кнопки пагинации
    pagination_buttons = []
    if page == 1 and end_idx < len(items):
        pagination_buttons.append(button_no)
        pagination_buttons.append(button_next)
    elif page > 1 and end_idx < len(items):
        pagination_buttons.append(button_back)
        pagination_buttons.append(button_next)
    elif end_idx >= len(items):
        pagination_buttons.append(button_back)
        pagination_buttons.append(button_no)

    if pagination_buttons:
        keyboard.row(*pagination_buttons)

    return keyboard

# Клаиатура для ленты
async def keyboard_post(hash: str, hash_id_channel: str, n: int = 0):
    """
    Клавиатура для поста в ленте
    """
    async def imgs_button(id_imgs: list, hash: str) -> list:
        buttons = []
        for i in range(len(id_imgs)):
            if i != n:
                buttons.append(InlineKeyboardButton(
                        f'{i+1}', 
                        callback_data=f'imgs:{i}:{hash}:{hash_id_channel}'
                    )
                )
            else:    
                buttons.append(InlineKeyboardButton(
                        f'📷', 
                        callback_data=f'trash123'
                    )
                )        
        return buttons
    
    keyboard = InlineKeyboardMarkup(row_width=4)

    id_imgs = await cache.aget(f'{hash}-imgs')

    if id_imgs: # Создания кнопок для остальных фотографий анкеты
        keyboard.row( *(await imgs_button(id_imgs, hash)))
    elif id_imgs != False:
        from mainBot.telegram.handlers.rec_feed import decode_base62

        external_id = await decode_base62(hash) 
        posters = (await Channel.objects.aget(external_id=external_id)).poster.split()
        if len(posters) >= 1:
            await cache.aset(f'{hash}', posters, 5*60)
            keyboard.row( *(await imgs_button(posters, hash)))
        else:
            await cache.aset(f'{hash}-imgs', False, 5*60)

    keyboard.add( 
        # Лайка
        InlineKeyboardButton("💖", callback_data=f'like_post:{hash}:{hash_id_channel}'),
        # Коментарий                           
        InlineKeyboardButton("💬", callback_data=f'comment_post:{hash}:{hash_id_channel}'),
        # Дизлайк                           
        InlineKeyboardButton("👎", callback_data=f'dislike_post:{hash}'),                                   
        # Жалоба
        InlineKeyboardButton("⚠️", callback_data=f'complaint_post:{hash}:{hash_id_channel}'),         
    ) 

    return keyboard 

# Клава жалоб
async def complite_tags_keybord(hash, hash_id_channel):
    """
    Список аргументов для жалобы
    """
    keyboard = await cache.aget('complite_tags_keybord')
    if not keyboard:
        keyboard = InlineKeyboardMarkup()
        async for cp in СategoryComplaint.objects.all():
            keyboard.add(InlineKeyboardButton(cp.name, callback_data=f'complite_tags:{cp.id}:{hash}:{hash_id_channel}'))

        keyboard.row(
            InlineKeyboardButton(
                await get_message_text('keyboards', 'add_channel_back'),
                callback_data=f'feed_back:{hash}:{hash_id_channel}'
            ),            
        )
        await cache.aset('complite_tags_keybord', keyboard, 1 if settings.DEBUG else None)
    return keyboard

async def complite_tags_keybord_finish(item_id, hash, hash_id_channel):
    """ Подтверждение перед жалобой """

    keyboard = InlineKeyboardMarkup()
    item = await cache.aget(f'{item_id}-tags_keybord')
    if not item:
        item = await СategoryComplaint.objects.aget(id=int(item_id))
        await cache.aset(f'{item_id}-tags_keybord', item, 1 if settings.DEBUG else None)

    keyboard.row(InlineKeyboardButton(f'{item.name}', callback_data='trash123'))    
    keyboard.row(
        InlineKeyboardButton(
            await get_message_text('keyboards', 'add_channel_back'),
            callback_data=f'feed_back:{hash}:{hash_id_channel}'
        ),            
        InlineKeyboardButton(
            await get_message_text('keyboards', 'add_channel_complite'),
            callback_data=f'tags_complite:{item_id}:{hash}:{hash_id_channel}'
        )

        )        
    return keyboard

async def murkup_keboard_stay() -> ReplyKeyboardMarkup:
    """Кнопки снизу обычные сообщения в чат"""
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(
        KeyboardButton(await get_message_text('keyboards', 'callback_feed_start')),
        KeyboardButton(await get_message_text('keyboards', 'menu_change_profile')),
        KeyboardButton(await get_message_text('keyboards', 'menu_referals')),
        KeyboardButton(await get_message_text('keyboards', 'menu_change_location')),
    )

    return keyboard