from telebot import types
from .bot import get_user_state, set_user_state, get_message_text, anketa_text


async def complite_and_close():
    """Конопки 'Готово' и 'Отмена' под сообщениями"""
    return types.InlineKeyboardMarkup(row_width=2).row(
        types.InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_complite'), 
                                    callback_data='message_complite'),                         
        types.InlineKeyboardButton(await get_message_text("absolute_messages", "stop"), 
                                    callback_data='message_close'),
    )                                

#* Клавиатура для кнопки стоп
async def stop_message():
    return types.ReplyKeyboardMarkup(row_width=1).row(
        types.InlineKeyboardButton(await get_message_text("absolute_messages", "stop")))

#* Клавиатура для редактирования канала 
async def keyboard_add_chennal():
    keyboard = types.InlineKeyboardMarkup(row_width=2).add( 
        # Добавить фото
        types.InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_img_chat'), 
                                   callback_data='add_channel_img_chat'),
        # Добавить описание                           
        types.InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_description_chat'), 
                                   callback_data='add_channel_description_chat'),
        # Добавить город                           
        types.InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_location'), 
                                   callback_data='add_channel_location'),                                   
        # Готово
        types.InlineKeyboardButton(await get_message_text('keyboards', 'add_channel_complite'), 
                                   callback_data='add_channel_precomplite'),         
    )  
    return keyboard 

#* Функция для обновления клавиатуры с добавлением смайлика к кнопке
async def update_keyboard_warning(call: types.CallbackQuery, callback_data, row_width=1):
    # Получаем текущую клавиатуру из сообщения
    keyboard = call.message.reply_markup
    # Перебираем кнопки и добавляем смайлик к нажатой кнопке
    updated_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
    for buttons in keyboard.keyboard:
        for button in buttons:
            if button.callback_data == callback_data:
                # Добавляем смайлик "осторожно" к тексту нажатой кнопки
                if str(button.text[0]) != str('⚠️')[0]:
                    updated_button = types.InlineKeyboardButton(text=f"⚠️ {button.text}", callback_data=button.callback_data)
                else:
                    updated_button = button    
            else:         
                updated_button = types.InlineKeyboardButton(text=button.text, callback_data=button.callback_data)
            updated_keyboard.add(updated_button)

    return updated_keyboard

# Метод для генерации пагинированной клавиатуры
async def generate_paginated_keyboard(items, page, page_size, callback_prefix, selected_ids=[], text_info=None):
    """
    Генерация inline-клавиатуры с пагинацией.
    
    -items: Список объектов.
    -page: Номер текущей страницы (от 1).
    -page_size: Количество объектов на странице.
    -callback_prefix: Префикс callback данных.
    = return: InlineKeyboardMarkup.
    """
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = items[start_idx:end_idx]
    
    keyboard = types.InlineKeyboardMarkup()
    # Добавляем для информации кнопку
    if text_info:
        keyboard.row(types.InlineKeyboardButton(
            text_info, 
            callback_data=f"trash123"
            )
        )            

    buttons = []
    for item in page_items:
        button = types.InlineKeyboardButton(
            text=f"{item.name} {'✅' if item.id in selected_ids else ''}",  # Отображаемое название объекта
            callback_data=f"{callback_prefix}:{item.id}:page:{page}"  # Метаданные
        )
        buttons.append(button)
    keyboard.add(*buttons, row_width=2)
    
    button_next = types.InlineKeyboardButton(
        "➡️", 
        callback_data=f"{callback_prefix}:page:{page+1}"
        )
    button_back = types.InlineKeyboardButton(
        "⬅️", 
        callback_data=f"{callback_prefix}:page:{page-1}"
        )
    button_no = types.InlineKeyboardButton(
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
async def keyboard_post(hash):
    """
    Клавиатура для поста в ленте
    """
    keyboard = types.InlineKeyboardMarkup(row_width=4).add( 
        # Лайка
        types.InlineKeyboardButton("💖", callback_data=f'like_post+{hash}'),
        # Коментарий                           
        types.InlineKeyboardButton("💬", callback_data=f'comment_post+{hash}'),
        # Дизлайк                           
        types.InlineKeyboardButton("👎", callback_data=f'dislike_post+{hash}'),                                   
        # Жалоба
        types.InlineKeyboardButton("⚠️", callback_data=f'complaint_post+{hash}'),         
    ) 

    return keyboard 