from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, \
    filters
from peewee import *
import main2
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Подключаем базу данных
db = SqliteDatabase('wallapop_items.db')
PARSE_INPUT = 1
default = "9"
domen = "1"
db.connect()


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    name = CharField()
    registration_date = CharField()
    sales_count = IntegerField()
    user_link = CharField()
    check_status = BooleanField(default=False)


class Item(BaseModel):
    name = CharField()
    image_link = CharField()
    stuff_url = CharField()
    # last_modified = CharField()
    user = ForeignKeyField(User, backref='items')
    update_time = CharField(null=True)


# Создаем пул потоков для выполнения длительных задач
executor = ThreadPoolExecutor()


# Функция для создания инлайн-клавиатуры с категориями
def create_categories_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Все товары", callback_data='cat_1')],
        [InlineKeyboardButton("Мото", callback_data='cat_2')],
        [InlineKeyboardButton("Мото аксессуары", callback_data='cat_3')],
        [InlineKeyboardButton("Электроника", callback_data='cat_4')],
        [InlineKeyboardButton("Телефонные аксессуары", callback_data='cat_5')],
        [InlineKeyboardButton("Спорт", callback_data='cat_6')],
        [InlineKeyboardButton("Детские товары", callback_data='cat_7')],
        [InlineKeyboardButton("Инструменты", callback_data='cat_8')],
        [InlineKeyboardButton("Одежда", callback_data='cat_9')],
        [InlineKeyboardButton("Все товары(Новые)", callback_data='cat_10')],
        [InlineKeyboardButton("Одежда(Новая)", callback_data='cat_11')],
        [InlineKeyboardButton("Спорт(Новые)", callback_data='cat_12')],
        [InlineKeyboardButton("Открыть меню", callback_data='back_to_menu')],
    ])
    return keyboard


def create_domen_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("IT", callback_data='dom_1')],
        [InlineKeyboardButton("ES", callback_data='dom_2')],
        [InlineKeyboardButton("EN(Не работает)", callback_data='dom_3')],
        [InlineKeyboardButton("PT", callback_data='dom_4')],
        [InlineKeyboardButton("FR", callback_data='dom_5')],
    ])
    return keyboard


# Обработчик команды /start
# Обработчик команды /start
async def start(update: Update, context):
    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton("Поиск анкет в БД", callback_data='1')],
        [InlineKeyboardButton("Начать парсинг", callback_data='2')],
        [InlineKeyboardButton("Настройка парсинга", callback_data='3')],
        [InlineKeyboardButton("Настройка домена", callback_data='4')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Проверяем, какой тип update пришел — сообщение или callback_query
    if update.message:  # Если это вызов команды /start
        await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
    elif update.callback_query:  # Если это был вызов через кнопку
        await update.callback_query.edit_message_text('Выберите действие:', reply_markup=reply_markup)


# Функция для поиска пользователей с check_status = False
async def search_users(update: Update, context, page=0):

    # Количество пользователей на одной странице
    users_per_page = 1

    # Получаем всех пользователей с check_status = False
    users = User.select().where(User.check_status == False).order_by(User.id.desc())  # ебать прикол ==\is по разному работают

    # Если пользователей нет, отправляем сообщение
    if not users.exists():
        if update.message:
            await update.message.reply_text("Не найдено пользователей с check_status = False.")
            await start(update, context)  # Открываем меню через сообщение
        elif update.callback_query:
            await update.callback_query.edit_message_text("Не найдено пользователей с check_status = False.")
            await start(update, context)  # Открываем меню через callback_query

        db.close()

        return

    # Считаем общее количество пользователей и страницы
    total_users = users.count()
    start_idx = page * users_per_page
    end_idx = start_idx + users_per_page

    # Получаем пользователей для текущей страницы
    current_users = users[start_idx:end_idx]

    response = "Пользователи с не проверенным статусом (стр. {}/{}):\n\n".format(page + 1, (
                total_users + users_per_page - 1) // users_per_page)

    # Кнопки для каждого пользователя
    keyboard = []
    for user in current_users:
        # Собираем информацию о пользователе и его товарах
        response += f"Имя: {user.name}\nДата регистрации: {user.registration_date}\nСделок: {user.sales_count}\nСсылка на пользователя: {user.user_link}\n"
        active_time = None
        # Получаем все товары пользователя
        items = Item.select().where(Item.user == user)
        for item in items:
            # Отправляем картинку товара
            active_time = item.update_time if item.update_time is not None else "Не найдено"
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=item.image_link,  # Ссылка на изображение товара
                caption=f"{item.name}: {item.stuff_url}"
            )
            break  # Можно удалить для вывода всех товаров
        response += f"Последняя активность: {active_time}\n"
        response += "\n"  # Добавляем пустую строку для разделения пользователей

        # Кнопка для изменения статуса
        keyboard.append([InlineKeyboardButton(f"Поменять статус {user.name}", callback_data=f'change_{user.id}')])

    # Определяем кнопки для навигации
    nav_keyboard = []
    if page > 0:
        nav_keyboard.append(InlineKeyboardButton("Предыдущие", callback_data=f'prev_{page - 1}'))
    if end_idx < total_users:
        nav_keyboard.append(InlineKeyboardButton("Следующие", callback_data=f'next_{page + 1}'))

    keyboard.append([InlineKeyboardButton("Открыть меню", callback_data='back_to_menu')])

    if nav_keyboard:
        keyboard.append(nav_keyboard)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем пользователю текстовый результат (информация о пользователях)
    await update.message.reply_text(response, reply_markup=reply_markup)

    db.close()


# Обработчик нажатий на кнопки
async def button(update: Update, context):
    global default, domen  # используем глобальную переменную
    query = update.callback_query
    await query.answer()  # Подтверждение клика

    # Определяем, какая кнопка была нажата
    choice = query.data

    # Поиск пользователей в базе данных
    if choice == '1':
        await query.edit_message_text(text="Выполняется поиск пользователей с check_status = False...")
        await search_users(query, context, page=0)  # Первая страница

    # Если нажата кнопка "Следующие" или "Предыдущие"
    elif choice.startswith('next_') or choice.startswith('prev_'):
        _, page = choice.split('_')
        page = int(page)
        await query.edit_message_text(text=f"Загружаем пользователей, страница {page + 1}...")
        await search_users(query, context, page)

    # Если нажата кнопка "Поменять статус"
    elif choice.startswith('change_'):
        _, user_id = choice.split('_')
        user = User.get_by_id(user_id)
        user.check_status = True
        user.save()

        # Сообщение остается таким же, только удаляем кнопку для этого пользователя
        await query.edit_message_reply_markup(reply_markup=None)  # Убираем кнопки из сообщения

        # Обновляем кнопки, оставляя возможность перехода между страницами
        page = 0  # Или номер текущей страницы, если он был сохранен в контексте
        await search_users(query, context, page)

    # Если выбор парсинга
    elif choice == '2':
        await query.edit_message_text(text="Введите количество для парсинга(Или 0 для отмены):")
        return PARSE_INPUT

    # Если настройка
    elif choice == '3':
        # Показать категории для выбора
        await query.edit_message_text(text="Выберите категорию:", reply_markup=create_categories_keyboard())

    elif choice == '4':
        await query.edit_message_text(text="Выберите домен:", reply_markup=create_domen_keyboard())

    # Обработка выбора категории
    elif choice.startswith('cat_'):
        # Извлекаем номер категории из callback_data
        default = choice.split('_')[1]  # Получаем числовое значение после 'cat_'

        # Отправляем сообщение с выбранной категорией
        await query.edit_message_text(text=f"Вы выбрали категорию: {default}")

        # Показываем основное меню после выбора категории
        await start(update, context)

    elif choice.startswith('dom_'):
        # Извлекаем номер категории из callback_data
        domen = choice.split('_')[1]  # Получаем числовое значение после 'dom_'

        # Отправляем сообщение с выбранной категорией
        await query.edit_message_text(text=f"Вы выбрали домен: {default}")

        # Показываем основное меню после выбора категории
        await start(update, context)

    elif choice == 'back_to_menu':
        await start(update, context)

    return ConversationHandler.END

# Асинхронная обертка для парсинга
async def run_parsing(count, update):
    loop = asyncio.get_event_loop()
    # Запускаем синхронную функцию парсинга в отдельном потоке
    await loop.run_in_executor(executor, main2.parsing, count, default, domen)
    await update.message.reply_text(f'Парсинг завершен для {count} элементов на домене {domen}.')


# Обработчик ввода числа
async def parse_input(update: Update, context):
    try:
        # Получаем введенное число
        user_input = int(update.message.text)

        # Если пользователь вводит 0, отменяем операцию
        if user_input == 0:
            await update.message.reply_text("Парсинг отменен.")
            await start(update, context)  # Возвращаемся к основному меню
            return ConversationHandler.END

        # Отправляем сообщение пользователю о начале парсинга
        await update.message.reply_text(f'Начинаем парсинг {user_input} элементов...')
        await start(update, context)

        # Запускаем парсинг асинхронно
        asyncio.create_task(run_parsing(user_input, update))

    except ValueError:
        # Если пользователь ввел не число
        await update.message.reply_text("Пожалуйста, введите корректное число.")
        return PARSE_INPUT

    return ConversationHandler.END


# Обработчик отмены диалога
async def cancel(update: Update, context):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Основная функция
if __name__ == '__main__':
    # Вставь сюда свой токен от BotFather
    TOKEN = ''

    # Создаем приложение для бота
    app = ApplicationBuilder().token(TOKEN).build()

    # Обработчик команды /start
    app.add_handler(CommandHandler("start", start))

    # Создаем ConversationHandler для обработки диалога
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button)],  # Начало диалога с кнопками
        states={
            PARSE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, parse_input)]  # Ожидаем ввод числа
        },
        fallbacks=[CommandHandler("cancel", cancel)],  # Обработчик отмены
        per_message=False  # Явно указываем, что per_message отключен
    )

    # Добавляем ConversationHandler в приложение
    app.add_handler(conv_handler)

    # Запуск бота
    app.run_polling()
