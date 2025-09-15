import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
import config

# Логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Стани
class TestStates(StatesGroup):
    waiting_for_contact = State()

# Створення бази даних
async def create_db():
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                phone TEXT,
                test_completed INTEGER DEFAULT 0
            )
        ''')
        await db.commit()

# Збереження користувача
async def save_user(user_id, first_name, username, phone):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (user_id, first_name, username, phone)
            VALUES (?, ?, ?, ?)
        ''', (user_id, first_name, username, phone))
        await db.commit()

# Команда /start
@dp.message_handler(commands=['start'], state='*')
async def start_command(message: types.Message, state: FSMContext):
    await state.finish()
    
    # Перевіряємо результат
    if message.text and 'result_' in message.text:
        await handle_quiz_result(message)
        return
    
    # Звичайний старт
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        cursor = await db.execute(
            'SELECT phone FROM users WHERE user_id = ?', 
            (message.from_user.id,)
        )
        result = await cursor.fetchone()
    
    if result and result[0]:
        await show_main_menu(message)
    else:
        await request_contact(message)

# Обробка результатів квізу з картинками
async def handle_quiz_result(message: types.Message):
    try:
        score_text = message.text.split('result_')[1]
        score = int(score_text)
        
        # Збереження результату
        async with aiosqlite.connect(config.DATABASE_NAME) as db:
            await db.execute('''
                UPDATE users SET test_completed = ? WHERE user_id = ?
            ''', (score, message.from_user.id))
            await db.commit()
        
        # Збереження результату в Google Sheets
        try:
            from google_sheets import add_quiz_result
            add_quiz_result(message.from_user.id, score)
        except Exception as e:
            print(f"Помилка збереження результату в Google Sheets: {e}")
        
        # Перше повідомлення замість результату
        await message.answer("🎉 ВАШІ РЕЗУЛЬТАТИ!\n\nМожете поділитись в сторіс та відмітити мене")
        
        # Затримка 3 секунди і відправка картинки результату
        await asyncio.sleep(3)
        
        # Визначаємо яку картинку відправити на основі балів (13 питань * 3 = максимум 39 балів)
        if 13 <= score <= 19:
            image_url = "https://raw.githubusercontent.com/molfartaro/molfa-webapp/main/result1.png"
            result_type = "Прихований потенціал"
        elif 20 <= score <= 29:
            image_url = "https://raw.githubusercontent.com/molfartaro/molfa-webapp/main/result2.png"
            result_type = "Помірні здібності"
        elif 30 <= score <= 35:
            image_url = "https://raw.githubusercontent.com/molfartaro/molfa-webapp/main/result3.png"
            result_type = "Сильні здібності"
        else:  # 36-39 балів
            image_url = "https://raw.githubusercontent.com/molfartaro/molfa-webapp/main/result4.png"
            result_type = "Виняткові здібності"
        
        # Спробуємо відправити картинку
        try:
            await message.answer_photo(photo=image_url)
            print(f"Картинка результату відправлена: {result_type} (бали: {score})")
        except Exception as e:
            print(f"Помилка відправки картинки: {e}")
            await message.answer(f"📊 Ваш результат: {result_type}\nБали: {score}/39")
        
        # Затримка 30 секунд і маркетингові повідомлення
        await asyncio.sleep(30)  # 30 секунд
        
        # Перше повідомлення про академію - БЕЗ кнопки
        first_academy_message = (
            "✨ Вітаю вас!\n"
            "Ви щойно побачили, що здібності у вас є — і вони не випадкові. "
            "Такі здібності зустрічаються справді рідко — і це підтверджує, що ви маєте особливий дар.\n\n"
            "Я шукаю саме таких як ви!\n\n"
            "Пам'ятаю себе на вашому місці, коли не знав як і де розвивати їх. "
            "Саме тому я створив першу Академію Таро.\n\n"
            "Це простір, де ви зможете не просто підтвердити свій дар, а й розкрити його на максимум:\n"
            "- пізнаєте свої здібності та опануєте методи їх розвитку;\n"
            "- опануєте безпечну методику роботи з Таро, щоб впевнено проводити розклади без ризику нашкодити собі чи клієнту;\n"
            "- наповните своє життя сенсом і новими фарбами, відкривши своє покликання через Таро;\n"
            "- перетворите свою місію допомоги людям у стабільне джерело доходу."
        )
        
        await message.answer(first_academy_message)
        
        # Затримка 10 секунд перед другим повідомленням
        await asyncio.sleep(10)

        # Спочатку відправляємо фото академії
        photo_urls = [
            "https://raw.githubusercontent.com/molfartaro/molfa-webapp/main/academy-image.png",
            "https://github.com/molfartaro/molfa-webapp/blob/main/academy-image.png?raw=true",
            "https://molfartaro.github.io/molfa-webapp/academy-image.png"
        ]
        
        photo_sent = False
        for photo_url in photo_urls:
            try:
                await message.answer_photo(photo=photo_url)
                photo_sent = True
                print(f"Фото академії відправлено успішно з URL: {photo_url}")
                break
            except Exception as e:
                print(f"Помилка з URL {photo_url}: {e}")
                continue
        
        if not photo_sent:
            print("Жодна з URL-адрес не спрацювала, відправляємо без фото")
        
        # Кнопка для Академії
        academy_keyboard = InlineKeyboardMarkup()
        academy_keyboard.add(InlineKeyboardButton(
            "Дізнатись про Академію", 
            callback_data="academy_info"
        ))
        
        # Друге повідомлення з ім'ям користувача та кнопкою
        user_name = message.from_user.first_name or "друже"
        second_academy_message = (
            f"Маю честь, {user_name}, запропонувати вам персональне менторство і підтримку "
            "на шляху вашого розвитку, щоб допомогти розкрити потенціал ще глибше через практику Таро.\n\n"
            "Зараз у вас є можливість зробити перший крок, натиснувши кнопку «Дізнатись про Академію» — "
            "і отримати більше, ніж інші:\n"
            "- безкоштовну консультацію від моєї команди;\n"
            "- закріпити за собою найкращі умови навчання;\n"
            "- а також шанс увійти в число перших 50 учнів, які отримають особливий подарунок від мене особисто.\n\n"
            "⬇️Натискайте кнопку «Дізнатись про Академію» — і відкрийте двері до істинного шляху до себе.⬇️\n\n"
            "⬇️⬇️⬇️"
        )
        
        await message.answer(
            second_academy_message,
            reply_markup=academy_keyboard
        )
        
    except (ValueError, IndexError):
        await message.answer("Виникла помилка при обробці результату.")

# Функція для отримання всіх користувачів з бази
async def get_all_users():
    try:
        async with aiosqlite.connect(config.DATABASE_NAME) as db:
            cursor = await db.execute('SELECT user_id FROM users')
            users = await cursor.fetchall()
            return [user[0] for user in users]
    except Exception as e:
        print(f"Помилка отримання користувачів: {e}")
        return []

# Команда для розсилки (тільки для адміністратора)
@dp.message_handler(lambda m: m.from_user.id == config.ADMIN_TELEGRAM_ID and m.text.startswith('/send '))
async def admin_send(message: types.Message):
    text = message.text[6:]  # Прибираємо '/send '
    if not text.strip():
        await message.answer("Введіть текст після команди. Приклад: /send Привіт всім!")
        return
    
    users = await get_all_users()
    if not users:
        await message.answer("Немає користувачів для розсилки.")
        return
    
    sent_count = 0
    error_count = 0
    
    await message.answer(f"Розпочинаю розсилку для {len(users)} користувачів...")
    
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            sent_count += 1
            await asyncio.sleep(0.1)  # Затримка щоб не заблокували за спам
        except Exception as e:
            error_count += 1
            print(f"Не вдалося відправити користувачу {user_id}: {e}")
    
    await message.answer(f"Розсилка завершена!\nВідправлено: {sent_count}\nПомилок: {error_count}")

# Обробник кнопки "Дізнатись про Академію"
@dp.callback_query_handler(lambda c: c.data == 'academy_info')
async def academy_info_handler(callback_query: types.CallbackQuery):
    await callback_query.answer()
    
    # Відповідь користувачу
    await callback_query.message.answer(
        "Чудово, ваша заявка отримана! З вами звʼяжеться моя команда!"
    )
    
    # Позначка в Google Sheets
    try:
        from google_sheets import mark_academy_interest
        mark_academy_interest(callback_query.from_user.id)
    except Exception as e:
        print(f"Помилка позначки в Google Sheets: {e}")

# Запит контакту з новим текстом
async def request_contact(message: types.Message):
    contact_button = KeyboardButton("📱 Поділитися контактом", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer(
        "Вітаю, Незламні!\n\n"
        "✨ Я розробив для вас цей тест, аби ви раз і назавжди змогли відповісти собі на важливе питання: **чи дійсно я щось відчуваю і які здібності приховані в мені?**\n\n"
        "Тут ви зможете дізнатися, наскільки ваші дари вже розвинені чи поки що сплять, і отримаєте рекомендації, як їх правильно розвивати.\n\n"
        "Не відкладайте — скоріше натискайте кнопку **«Пройти тест»** і отримайте свій результат 🔮\n\n"
        "📱 Але спочатку поділіться контактом:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )
    await TestStates.waiting_for_contact.set()

# Обробка контакту
@dp.message_handler(content_types=['contact'], state=TestStates.waiting_for_contact)
async def handle_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    
    await save_user(
        user_id=message.from_user.id,
        first_name=contact.first_name,
        username=message.from_user.username or '',
        phone=contact.phone_number
    )
    
    # Google Sheets
    try:
        from google_sheets import add_user_to_sheet
        add_user_to_sheet(
            user_id=message.from_user.id,
            first_name=contact.first_name,
            username=message.from_user.username or '',
            phone=contact.phone_number
        )
    except Exception as e:
        print(f"Google Sheets помилка: {e}")
    
    print(f"Новий контакт: {contact.first_name} - {contact.phone_number}")
    
    await message.answer(
        f"✅ Дякую, {contact.first_name}!\n"
        f"📞 Контакт збережено.\n\n",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    await state.finish()
    await show_main_menu(message)

# Головне меню
async def show_main_menu(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        "🔮 Пройти тест", 
        url="https://molfartaro.github.io/molfa-webapp/"
    ))
    
    await message.answer(
    "⬇️Натисніть кнопку нижче \"Пройти тест\", щоб почати тест. ⬇️\n\n"
    "А після завершення тесту натисніть «Отримати результат в боті» — і дізнайтеся свій рівень здібностей.\n\n"
    "⬇️⬇️⬇️",
    reply_markup=keyboard
)

# Запуск бота
async def main():
    await create_db()
    print("Бот запущений!")
    await dp.start_polling(bot)

# Перевірка структури таблиці при запуску
def setup_sheet_headers():
    try:
        from google_sheets import check_sheet_structure
        check_sheet_structure()
        print("Структура таблиці перевірена!")
    except Exception as e:
        print(f"Помилка налаштування Google Sheets: {e}")

if __name__ == '__main__':
    setup_sheet_headers()
    asyncio.run(main())