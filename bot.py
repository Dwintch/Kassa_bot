import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = '8197209578:AAH4ypgRz9Butww_HxDTBeXJCgTzHQO1D_E'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

DB_NAME = 'transactions.db'
user_states = {}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_transaction(amount):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO transactions (amount) VALUES (?)", (amount,))
    conn.commit()
    conn.close()

def get_total():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM transactions")
    result = cur.fetchone()[0]
    conn.close()
    return result if result else 0

def clear_transactions():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()

def get_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("💰 Перевод", "🔙 Возврат", "📊 Отчёт")
    return keyboard

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Выбери действие или введи сумму перевода.", reply_markup=get_keyboard())

@dp.message_handler(lambda message: message.text == "💰 Перевод")
async def set_deposit(message: types.Message):
    user_states[message.from_user.id] = "deposit"
    await message.answer("Введи сумму перевода:")

@dp.message_handler(lambda message: message.text == "🔙 Возврат")
async def set_refund(message: types.Message):
    user_states[message.from_user.id] = "refund"
    await message.answer("Введи сумму возврата:")

@dp.message_handler(lambda message: message.text == "📊 Отчёт")
async def show_report(message: types.Message):
    total = get_total()
    await message.answer(f"Что-то сегодня плохо, накосил всего: {total} руб.")
    clear_transactions()
    user_states[message.from_user.id] = None  # сброс состояния

@dp.message_handler(lambda message: message.text.isdigit())
async def process_amount(message: types.Message):
    user_id = message.from_user.id
    amount = int(message.text)
    state = user_states.get(user_id)

    if state == "refund":
        save_transaction(-amount)
        await message.answer(f"И эти копейки возвращают? Хорошо, я учту эти: -{amount} руб.")
    else:
        save_transaction(amount)
        await message.answer(f"О лавешка капнула, целых: +{amount} руб.")

    user_states[user_id] = None  # сброс состояния после ввода

@dp.message_handler()
async def unknown_message(message: types.Message):
    await message.answer("Введи сумму перевода числом или выбери действие с кнопками.", reply_markup=get_keyboard())

if __name__ == '__main__':
    init_db()
    executor.start_polling(dp, skip_updates=True)

