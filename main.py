from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN
from Bot_Trade import trade_bot
import asyncio

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
trade_tasks = {}  # Словарь для хранения активных торговых задач для каждого chat_id

# Клавиатуры
main_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_menu.add(KeyboardButton("1m"), KeyboardButton("5m"),
             KeyboardButton("15m"), KeyboardButton("30m"),
             KeyboardButton("1h"), KeyboardButton("4h"))
main_menu.add(KeyboardButton("Закончить"))


currency_menu = ReplyKeyboardMarkup(resize_keyboard=True)
currency_menu.add(KeyboardButton("BTC"))
currency_menu.add(KeyboardButton("ETH"))
currency_menu.add(KeyboardButton("LTC"))


async def trade_loop(timeframe_param, symbol, chat_id):
    while chat_id in trade_tasks and trade_tasks[chat_id][0] == timeframe_param:

        output = trade_bot(timeframe_param, symbol)
        if output != 0:
            await bot.send_message(chat_id, output + "\n" + symbol + " на TimeFrame " + timeframe_param)
            await asyncio.sleep(60)

        await asyncio.sleep(5)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    text = "Инструкция:\n\n" \
           "--Чтобы выбрать другой TimeFrame, просто нажмите на него в меню выбора.\n" \
           "--Чтобы поменять пару, нажмите <b>закончить</b>, а затем выберите пару.\n"\
           "--Чтобы перезапустить бота ВВЕДИТЕ <a href='tg://resolve?domain=Trade_denis_bot'>/start</a>"
    await message.reply(text, reply_markup=currency_menu, parse_mode=types.ParseMode.HTML)

async def get_telegram_username(chat_id):
    chat = await bot.get_chat(chat_id)
    return chat.username

@dp.message_handler(lambda message: message.text in ["ETH", "BTC", "LTC"])
async def handle_currency(message: types.Message):
    chat_id = message.chat.id
    ######
    username = await get_telegram_username(chat_id)
    print(f"Пользователь https://t.me/{username}")
    ######
    if message.text == "ETH":
        await message.reply("Вы выбрали ETH. Выберите временной интервал:", reply_markup=main_menu)
        currency_symbol = "ETHUSDT"
    elif message.text == "BTC":
        await message.reply("Вы выбрали BTC. Выберите временной интервал:", reply_markup=main_menu)
        currency_symbol = "BTCUSDT"

    elif message.text == "LTC":
        await message.reply("Вы выбрали LTC. Выберите временной интервал:", reply_markup=main_menu)
        currency_symbol = "LTCUSD"

    if chat_id in trade_tasks:
        del trade_tasks[chat_id]  # Остановить предыдущую задачу, если она существует для этого пользователя

    trade_tasks[chat_id] = (None, currency_symbol)


@dp.message_handler(lambda message: message.text == "Закончить")
async def stop_bot(message: types.Message):
    print("----=== STOP ===----")
    chat_id = message.chat.id
    if chat_id in trade_tasks:
        del trade_tasks[chat_id]
        await message.reply("Завершение работы...", reply_markup=currency_menu)


@dp.message_handler(lambda message: message.text in ["1m", "5m", "15m", "30m", "1h", "4h"])
async def handle_timeframe(message: types.Message):
    chat_id = message.chat.id
    timeframe_mapping = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "1h": "60", "4h": "240"}
    timeframe_param = timeframe_mapping.get(message.text)

    if chat_id in trade_tasks and trade_tasks[chat_id][1]:
        symbol = trade_tasks[chat_id][1]
        trade_tasks[chat_id] = (timeframe_param, symbol)
        asyncio.create_task(trade_loop(timeframe_param, symbol, chat_id))
    else:
        await message.reply("Сначала выберите пару к USDT (ETH/BTC).", reply_markup=currency_menu)


if __name__ == '__main__':
    executor.start_polling(dp)