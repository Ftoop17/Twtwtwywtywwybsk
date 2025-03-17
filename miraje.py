from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, JobQueue
import sqlite3
import logging
import re
from datetime import time

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота
TOKEN = '7571263514:AAGBikYT7U6AtbRoSgU4ufGDoed2pvod_70'

# Подключение к базе данных SQLite
conn = sqlite3.connect('miraje_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц в базе данных
cursor.execute('''
CREATE TABLE IF NOT EXISTS phrases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase TEXT NOT NULL,
    response TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS unanswered_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL
)
''')

conn.commit()

# ID админа (замените на ваш)
ADMIN_ID = 7114988418

# Функция для добавления пользователя в базу данных
def add_user(user_id, username, first_name):
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, first_name)
    VALUES (?, ?, ?)
    ''', (user_id, username, first_name))
    conn.commit()
    
# Приветственное сообщение
def start(update: Update, context) -> None:
    welcome_text = (
        "👋 Привет! Я MIRAJE AI💙один из лучших нейросетей,если вдруг вы не нашли ответа на свой вопрос то не волнуйтесь вскоре наши администраторы добавят ответ на ваш вопрос💙\n"
        "Выберите одну из функций ниже:"
    )
    keyboard = [
        [InlineKeyboardButton("🤖 AI", callback_data='ai')],
        [InlineKeyboardButton("🧮 Калькулятор", callback_data='calculator')],
        [InlineKeyboardButton("📊 Для бухгалтеров", callback_data='accountant')],
        [InlineKeyboardButton("👤 Автор", callback_data='author')],
        [InlineKeyboardButton("🛑 Стоп", callback_data='stop')]
    ]
    if update.message.from_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🔧 Админ", callback_data='admin')])
        keyboard.append([InlineKeyboardButton("❓ Вопросы", callback_data='unanswered_questions')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_text, reply_markup=reply_markup)

# Команда для вывода списка пользователей (доступна только админу)
def list_users(update: Update, context) -> None:
    if update.message.from_user.id != ADMIN_ID:
        update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

    cursor.execute('SELECT username, first_name FROM users')
    users = cursor.fetchall()
    if users:
        user_list = "\n".join([f"👤 {user[1]} (@{user[0]})" if user[0] else f"👤 {user[1]}" for user in users])
        update.message.reply_text(f"📊 Список пользователей:\n{user_list}")
    else:
        update.message.reply_text("📊 Пользователей пока нет.")
        
# Обработчик кнопок
def button(update: Update, context) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'ai':
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="🤖 Введите ваш вопрос:", reply_markup=reply_markup)
        context.user_data['mode'] = 'ai'
    elif query.data == 'calculator':
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text=(
                "🧮 Введите математический пример:\n"
                "Примеры:\n"
                "2 + 2\n"
                "10 * 5\n"
                "20 / 4\n"
                "15% от 200"
            ),
            reply_markup=reply_markup
        )
        context.user_data['mode'] = 'calculator'
    elif query.data == 'accountant':
        context.user_data['step'] = 'salary'
        context.user_data['data'] = {}
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="📊 Введите оклад работника:", reply_markup=reply_markup)
    elif query.data == 'author':
        keyboard = [
            [InlineKeyboardButton("📘 ВК", url='https://vk.com/thetemirbolatov')],
            [InlineKeyboardButton("📸 Инстаграм", url='https://instagram.com/thetemirbolatov')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="👤 Автор: @thetemirbolatov", reply_markup=reply_markup)
    elif query.data == 'stop':
        query.edit_message_text(text="🛑 Бот остановлен. Нажмите /start чтобы продолжить.")
    elif query.data == 'admin':
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="🔧 Вы вошли в админ-панель. Введите новую фразу и ответ через '|'.", reply_markup=reply_markup)
    elif query.data == 'unanswered_questions':
        cursor.execute('SELECT * FROM unanswered_questions')
        questions = cursor.fetchall()
        if questions:
            for question in questions:
                keyboard = [
                    [InlineKeyboardButton("❌ Удалить", callback_data=f'delete_question_{question[0]}')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.message.reply_text(f"❓ Вопрос: {question[1]}", reply_markup=reply_markup)
        else:
            query.message.reply_text("❓ Нет неотвеченных вопросов.")
    elif query.data.startswith('delete_question_'):
        question_id = int(query.data.split('_')[-1])
        cursor.execute('DELETE FROM unanswered_questions WHERE id = ?', (question_id,))
        conn.commit()
        query.message.reply_text("✅ Вопрос удален.")
    elif query.data == 'back':
        # Удаляем предыдущие сообщения бота
        if 'message_ids' in context.user_data:
            for message_id in context.user_data['message_ids']:
                try:
                    context.bot.delete_message(chat_id=query.message.chat_id, message_id=message_id)
                except Exception as e:
                    logger.warning(f"Не удалось удалить сообщение {message_id}: {e}")
        # Возвращаемся в главное меню
        context.user_data.clear()
        start(update=Update(0, message=query.message), context=context)

# Функция для обработки сообщений
def handle_message(update: Update, context) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    # Сохраняем ID сообщения для возможного удаления
    if 'message_ids' not in context.user_data:
        context.user_data['message_ids'] = []
    context.user_data['message_ids'].append(update.message.message_id)

    # Блокировка рекламы
    if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text):
        update.message.reply_text("❌ Реклама запрещена!")
        return

    if user_id == ADMIN_ID and '|' in text:  # Добавление фразы и ответа
        phrase, response = text.split('|', 1)
        cursor.execute('INSERT INTO phrases (phrase, response) VALUES (?, ?)', (phrase.strip(), response.strip()))
        conn.commit()
        update.message.reply_text("✅ Фраза и ответ добавлены в базу данных.")
    elif 'mode' in context.user_data:
        if context.user_data['mode'] == 'ai':  # Режим AI
            cursor.execute('SELECT response FROM phrases WHERE phrase = ?', (text,))
            result = cursor.fetchone()
            if result:
                update.message.reply_text(result[0])
            else:
                cursor.execute('INSERT INTO unanswered_questions (question) VALUES (?)', (text,))
                conn.commit()
                update.message.reply_text("🤔 Я не знаю, что ответить на это.")
        elif context.user_data['mode'] == 'calculator':  # Режим калькулятора
            try:
                if '% от' in text:
                    value, percent = text.split('% от')
                    result = float(value.strip()) / 100 * float(percent.strip())
                else:
                    result = eval(text)
                update.message.reply_text(f"🧮 Результат: {result}")
            except Exception as e:
                update.message.reply_text(f"❌ Ошибка: {e}")
    elif 'step' in context.user_data:  # Режим для бухгалтеров
        handle_accountant(update, context)

# Логика для бухгалтеров
def handle_accountant(update: Update, context) -> None:
    step = context.user_data['step']
    data = context.user_data['data']
    text = update.message.text

    if step == 'salary':
        try:
            data['salary'] = float(text)
            context.user_data['step'] = 'children'
            update.message.reply_text("👶 Введите количество детей без инвалидности: (если нету пиши 0)")
        except ValueError:
            update.message.reply_text("❌ Ошибка: введите число.")
    elif step == 'children':
        try:
            data['children'] = int(text)
            context.user_data['step'] = 'disabled_children'
            update.message.reply_text("♿ Введите количество детей-инвалидов: (если нету пиши 0")
        except ValueError:
            update.message.reply_text("❌ Ошибка: введите число.")
    elif step == 'disabled_children':
        try:
            data['disabled_children'] = int(text)
            calculate_salary(update, context)
        except ValueError:
            update.message.reply_text("❌ Ошибка: введите число.")

# Расчет зарплаты
def calculate_salary(update: Update, context) -> None:
    data = context.user_data['data']
    salary = data['salary']
    children = data.get('children', 0)
    disabled_children = data.get('disabled_children', 0)

    # Расчет вычетов
    deductions = 0
    if children == 1:
        deductions += 1400
    elif children == 2:
        deductions += 2800
    elif children >= 3:
        deductions += 2800 + (children - 2) * 6000

    deductions += disabled_children * 12000

    # Расчет НДФЛ
    taxable_base = max(0, salary - deductions)
    ndfl = taxable_base * 0.13

    # Итоговая сумма
    total = salary - ndfl

    # Вывод результатов
    result = (
        f"💵 Оклад: {salary}\n"
        f"🧾 Вычеты: {deductions}\n"
        f"📊 Налогооблагаемая база: {taxable_base}\n"
        f"🧮 НДФЛ: {ndfl}\n"
        f"💸 Итого к выплате: {total}"
    )
    update.message.reply_text(result)
    context.user_data.clear()

# Рассылка рекламы
def send_advertisement(context):
    advertisement_text = (
        "🌟 Присоединяйтесь к нашей странице в Instagram! 🌟\n"
        "Хотите быть в курсе последних новинок, интересных акций и вдохновляющего контента? 💡 Подписывайтесь на нашу страницу @thetemirbolatov !\n"
        "✨ Здесь вы найдете:\n"
        "- Уникальные предложения и скидки 🎉\n"
        "- Полезные советы и лайфхаки 💡\n"
        "- Яркие фото и видео нашего продукта в действии 📸\n"
        "- Участие в конкурсах и розыгрышах 🎁\n"
        "! ❤️ Нажмите 'Подписаться' и будьте с нами на связи!"
    )
    context.bot.send_message(chat_id=ADMIN_ID, text=advertisement_text)

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("users", list_users))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Настройка рассылки рекламы
    job_queue = updater.job_queue
    job_queue.run_daily(send_advertisement, time(hour=10, minute=0))
    job_queue.run_daily(send_advertisement, time(hour=17, minute=0))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()