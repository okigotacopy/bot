import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
API_TOKEN = '7827603551:AAG_Ui4ZiHWMc_arF5TQBStDO_cjQGnMIMU'  # Ваш API-ключ
bot = Bot(token=API_TOKEN)
dp = Dispatcher()  # Инициализация диспетчера

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            country TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            balance REAL DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promocodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            discount REAL NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Юзернейм админа
ADMIN_USERNAME = 'wwaswhere'  # Ваш юзернейм

# Основное меню
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Добавляем пользователя в базу данных, если его нет
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close()

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💰 Профиль", callback_data='profile')
    keyboard.button(text="💳 Пополнить счет", callback_data='deposit')
    keyboard.button(text="🛒 Купить товар", callback_data='buy_product')
    keyboard.button(text="📦 История заказов", callback_data='order_history')
    keyboard.button(text="📞 Поддержка", callback_data='support')
    keyboard.adjust(2)  # Две кнопки в строке
    await message.answer(
        "🌟 Добро пожаловать в магазин! 🌟\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup()
    )

# Профиль
@dp.callback_query(F.data == 'profile')
async def profile(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()
    conn.close()

    if balance:
        await callback_query.answer()
        await callback_query.message.answer(
            f"👤 Ваш профиль:\n"
            f"💰 Баланс: *{balance[0]} USD*\n\n"
            f"Используйте команду /deposit для пополнения счета.",
            parse_mode="Markdown"
        )
    else:
        await callback_query.answer()
        await callback_query.message.answer('Вы еще не пополняли баланс.')

# Пополнение счета
@dp.callback_query(F.data == 'deposit')
async def deposit(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()
    conn.close()

    if balance:
        await callback_query.answer()
        await callback_query.message.answer(
            f"💳 Запрос на пополнение счета:\n"
            f"👤 Юзернейм: @{username}\n"
            f"💰 Текущий баланс: *{balance[0]} USD*\n\n"
            f"Напишите админу: @{ADMIN_USERNAME}",
            parse_mode="Markdown"
        )

# История заказов
@dp.callback_query(F.data == 'order_history')
async def order_history(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT products.name, orders.quantity, orders.total_price, orders.status
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.user_id = ?
    ''', (user_id,))
    orders = cursor.fetchall()
    conn.close()

    if orders:
        orders_list = "\n".join([f"🛒 {order[0]} | 🧮 {order[1]} шт. | 💰 {order[2]} USD | 🚦 {order[3]}" for order in orders])
        await callback_query.answer()
        await callback_query.message.answer(
            f"📦 Ваши заказы:\n{orders_list}",
            parse_mode="Markdown"
        )
    else:
        await callback_query.answer()
        await callback_query.message.answer('У вас пока нет заказов.')

# Поддержка
@dp.callback_query(F.data == 'support')
async def support(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(
        f"📞 Свяжитесь с поддержкой: @{ADMIN_USERNAME}",
        parse_mode="Markdown"
    )

# Меню покупки товаров
@dp.callback_query(F.data == 'buy_product')
async def buy_product(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📄 Сканы SSN", callback_data='category_ssn')
    keyboard.button(text="📄 Сканы паспортов", callback_data='category_passport')
    keyboard.button(text="📄 Сканы DL", callback_data='category_dl')
    keyboard.button(text="🔙 Назад", callback_data='back_to_main')
    keyboard.adjust(1)  # Одна кнопка в строке
    await callback_query.answer()
    await callback_query.message.answer(
        "🛒 Выберите категорию товаров:",
        reply_markup=keyboard.as_markup()
    )

# Подменю с выбором стран
@dp.callback_query(F.data.startswith('category_'))
async def category_menu(callback_query: types.CallbackQuery):
    category = callback_query.data.split('_')[1]  # Получаем категорию (ssn, passport, dl)

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🇺🇸 США", callback_data=f'country_{category}_usa')
    keyboard.button(text="🇨🇦 Канада", callback_data=f'country_{category}_canada')
    keyboard.button(text="🇪🇺 Европа", callback_data=f'country_{category}_europe')
    keyboard.button(text="🔙 Назад", callback_data='buy_product')
    keyboard.adjust(2)  # Две кнопки в строке
    await callback_query.answer()
    await callback_query.message.answer(
        f"🛒 Выберите страну в категории *{category}*:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

# Показать товары в выбранной категории и стране
@dp.callback_query(F.data.startswith('country_'))
async def show_products(callback_query: types.CallbackQuery):
    data = callback_query.data.split('_')
    category = data[1]  # Категория (ssn, passport, dl)
    country = data[2]   # Страна (usa, canada, europe)

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, price, description FROM products WHERE category = ? AND country = ?', (category, country))
    products = cursor.fetchall()
    conn.close()

    if products:
        keyboard = InlineKeyboardBuilder()
        for product in products:
            keyboard.button(text=f"{product[1]} - {product[2]} USD", callback_data=f'product_{product[0]}')
        keyboard.button(text="🔙 Назад", callback_data=f'category_{category}')
        keyboard.adjust(1)  # Одна кнопка в строке
        await callback_query.answer()
        await callback_query.message.answer(
            f"🛒 Товары в категории *{category}* ({country}):",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    else:
        await callback_query.answer()
        await callback_query.message.answer('Товары в этой категории отсутствуют.')

# Обработчик для выбора товара
@dp.callback_query(F.data.startswith('product_'))
async def select_product(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]  # Получаем ID товара

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, price, description FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()

    if product:
        name, price, description = product
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🛒 Купить", callback_data=f'buy_{product_id}')
        keyboard.button(text="🔙 Назад", callback_data=f'category_{callback_query.message.text.split()[-2]}')  # Возврат в категорию
        keyboard.adjust(1)

        await callback_query.answer()
        await callback_query.message.answer(
            f"🛒 Товар: *{name}*\n"
            f"💰 Цена: *{price} USD*\n"
            f"📄 Описание: *{description}*\n\n"
            f"Выберите действие:",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    else:
        await callback_query.answer("Товар не найден.")

# Обработчик для покупки товара
@dp.callback_query(F.data.startswith('buy_'))
async def buy_product(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]  # Получаем ID товара

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, price, description FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()

    if product:
        name, price, description = product
        user_id = callback_query.from_user.id

        # Проверяем баланс пользователя
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        balance = cursor.fetchone()
        conn.close()

        if balance and balance[0] >= price:
            # Списание средств и создание заказа
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (price, user_id))
            cursor.execute('INSERT INTO orders (user_id, product_id, quantity, total_price) VALUES (?, ?, 1, ?)',
                          (user_id, product_id, price))
            conn.commit()
            conn.close()

            # Отправляем описание товара
            await callback_query.answer()
            await callback_query.message.answer(
                f"✅ Товар *{name}* успешно куплен!\n\n"
                f"📄 Описание товара:\n"
                f"{description}",
                parse_mode="Markdown"
            )
        else:
            await callback_query.answer("❌ Недостаточно средств на балансе.")
    else:
        await callback_query.answer("Товар не найден.")

# Админка: просмотр всех пользователей
@dp.message(Command("users"))
async def view_users(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, balance FROM users')
    users = cursor.fetchall()
    conn.close()

    if users:
        users_list = "\n".join([f"👤 @{user[0]} | 💰 {user[1]} USD" for user in users])
        await message.answer(
            f"📊 Список пользователей:\n{users_list}",
            parse_mode="Markdown"
        )
    else:
        await message.answer("Пользователи не найдены.")

# Админка: просмотр всех заказов
@dp.message(Command("orders"))
async def view_orders(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT orders.id, users.username, products.name, orders.quantity, orders.total_price, orders.status
        FROM orders
        JOIN users ON orders.user_id = users.user_id
        JOIN products ON orders.product_id = products.id
    ''')
    orders = cursor.fetchall()
    conn.close()

    if orders:
        orders_list = "\n".join([f"📦 Заказ #{order[0]} | 👤 @{order[1]} | 🛒 {order[2]} | 🧮 {order[3]} шт. | 💰 {order[4]} USD | 🚦 {order[5]}" for order in orders])
        await message.answer(
            f"📦 Список заказов:\n{orders_list}",
            parse_mode="Markdown"
        )
    else:
        await message.answer("Заказы не найдены.")

# Админка: добавление товара
@dp.message(Command("add_product"))
async def add_product(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split(maxsplit=5)  # Формат: /add_product <категория> <страна> <название> <цена> <описание>
    if len(args) < 6:
        await message.answer("Использование: /add_product <категория> <страна> <название> <цена> <описание>")
        return

    _, category, country, name, price, description = args

    try:
        price = float(price.replace(',', '.'))  # Заменяем запятую на точку, если она есть
    except ValueError:
        await message.answer("Цена должна быть числом. Пример: 50.0 или 50")
        return

    valid_categories = ['ssn', 'passport', 'dl']
    valid_countries = ['usa', 'canada', 'europe']

    if category not in valid_categories:
        await message.answer(f"Недопустимая категория. Допустимые категории: {', '.join(valid_categories)}")
        return

    if country not in valid_countries:
        await message.answer(f"Недопустимая страна. Допустимые страны: {', '.join(valid_countries)}")
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (category, country, name, price, description) VALUES (?, ?, ?, ?, ?)',
                   (category, country, name, price, description))
    conn.commit()
    conn.close()

    await message.answer(f'Товар "{name}" успешно добавлен в категорию "{category}" ({country}).')

# Админка: удаление товара
@dp.message(Command("delete_product"))
async def delete_product(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split(maxsplit=1)  # Формат: /delete_product <id товара>
    if len(args) < 2:
        await message.answer("Использование: /delete_product <id товара>")
        return

    _, product_id = args

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

    await message.answer(f'Товар с ID {product_id} успешно удален.')

# Админка: добавление промокода
@dp.message(Command("add_promo"))
async def add_promo(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split(maxsplit=2)  # Формат: /add_promo <код> <скидка>
    if len(args) < 3:
        await message.answer("Использование: /add_promo <код> <скидка>")
        return

    _, code, discount = args

    try:
        discount = float(discount.replace(',', '.'))  # Заменяем запятую на точку, если она есть
    except ValueError:
        await message.answer("Скидка должна быть числом. Пример: 10.0 или 10")
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO promocodes (code, discount) VALUES (?, ?)', (code, discount))
    conn.commit()
    conn.close()

    await message.answer(f'Промокод "{code}" успешно добавлен.')

# Админка: удаление промокода
@dp.message(Command("delete_promo"))
async def delete_promo(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split(maxsplit=1)  # Формат: /delete_promo <код>
    if len(args) < 2:
        await message.answer("Использование: /delete_promo <код>")
        return

    _, code = args

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM promocodes WHERE code = ?', (code,))
    conn.commit()
    conn.close()

    await message.answer(f'Промокод "{code}" успешно удален.')

# Админка: изменение баланса пользователя
@dp.message(Command("set_balance"))
async def set_balance(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split(maxsplit=2)  # Формат: /set_balance <username> <баланс>
    if len(args) < 3:
        await message.answer("Использование: /set_balance <username> <баланс>")
        return

    _, username, balance = args

    try:
        balance = float(balance.replace(',', '.'))  # Заменяем запятую на точку, если она есть
    except ValueError:
        await message.answer("Баланс должен быть числом. Пример: 100.0 или 100")
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = ? WHERE username = ?', (balance, username))
    conn.commit()
    conn.close()

    await message.answer(f'Баланс пользователя @{username} успешно изменён на *{balance} USD*.', parse_mode="Markdown")

# Кнопка "Назад" в главное меню
@dp.callback_query(F.data == 'back_to_main')
async def back_to_main(callback_query: types.CallbackQuery):
    await start(callback_query.message)

# Запуск бота
if __name__ == '__main__':
    import asyncio
    asyncio.run(dp.start_polling(bot))
