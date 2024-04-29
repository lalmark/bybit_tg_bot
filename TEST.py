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
main_menu.add(KeyboardButton("Закончить все процессы"), KeyboardButton("Создать еще 1 процесс"))


currency_menu = ReplyKeyboardMarkup(resize_keyboard=True)
currency_menu.add(KeyboardButton("BTC"))
currency_menu.add(KeyboardButton("ETH"))
currency_menu.add(KeyboardButton("LTC"))
currency_menu.add(KeyboardButton("Текущие процессы"))

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    text = "Инструкция:\n\n" \
           "--Чтобы выбрать другой TimeFrame, просто нажмите на него в меню выбора.\n" \
           "--Чтобы поменять пару, нажмите <b>закончить</b>, а затем выберите пару.\n"\
           "--Чтобы перезапустить бота ВВЕДИТЕ <a href='tg://resolve?domain=Trade_denis_bot'>/start</a>"
    await message.reply(text, reply_markup=currency_menu, parse_mode=types.ParseMode.HTML)

async def trade_loop(task_id, timeframe_param, symbol, chat_id):
    # Проверяем, существует ли задача с данным task_id в списке активных задач
    while task_id in [t['task_id'] for t in trade_tasks.get(chat_id, []) if 'task_id' in t]:
        output, data_time = trade_bot(timeframe_param, symbol)
        if output != 0:
            # Использование HTML для выделения текста жирным
            message_text = (f"{output}\n"
                            f"<i>Время: {str(data_time)}</i>\n\n\n"
                            f"<b>{symbol} на TimeFrame {timeframe_param}</b>")
            await bot.send_message(chat_id, message_text, parse_mode=types.ParseMode.HTML)
            if timeframe_param == "240":
                await asyncio.sleep(595)  # Задержка для симуляции трейдинга
            if timeframe_param == "60":
                await asyncio.sleep(300)  # Задержка для симуляции трейдинга
            if timeframe_param == "30" or timeframe_param == "15":
                await asyncio.sleep(200)
        await asyncio.sleep(5)  # Задержка между итерациями цикла

def generate_task_id(chat_id, symbol, timeframe):
    return f"{chat_id}_{symbol}_{timeframe}"

async def get_telegram_username(chat_id):
    chat = await bot.get_chat(chat_id)
    return chat.username

@dp.message_handler(lambda message: message.text == "Текущие процессы")
async def show_current_processes(message: types.Message):
    chat_id = message.chat.id
    # Проверяем, есть ли активные процессы для данного пользователя
    if chat_id in trade_tasks and trade_tasks[chat_id]:
        processes_list = []
        for task in trade_tasks[chat_id]:
            currency = task.get('currency', 'Неизвестная валюта')
            timeframe = task.get('timeframe', 'Неизвестный timeframe')
            processes_list.append(f"{currency} на TimeFrame {timeframe}")
        processes_text = "\n".join(processes_list)
        reply_text = f"Активные процессы:\n\n{processes_text}"
    else:
        reply_text = "Нет активных процессов."

    await message.reply(reply_text, reply_markup=currency_menu, parse_mode=types.ParseMode.HTML)


async def get_telegram_username(chat_id):
    chat = await bot.get_chat(chat_id)
    return chat.username

@dp.message_handler(lambda message: message.text == "Создать еще 1 процесс")
async def create_another_process(message: types.Message):
    await message.reply("Выберите другую валюту для торговли:", reply_markup=currency_menu)

@dp.message_handler(lambda message: message.text in ["ETH", "BTC", "LTC"])
async def handle_currency(message: types.Message):
    chat_id = message.chat.id
    #############
    username = await get_telegram_username(chat_id)
    print(f"Пользователь https://t.me/{username}")
    ##############
    if chat_id not in trade_tasks:
        trade_tasks[chat_id] = []
    currency_symbol = {"ETH": "ETHUSDT", "BTC": "BTCUSDT", "LTC": "LTCUSDT"}[message.text]

    # Найти и удалить существующие задачи с той же валютой, что и выбранная, для этого пользователя
    trade_tasks[chat_id] = [task for task in trade_tasks[chat_id] if task['currency'] != currency_symbol]

    trade_tasks[chat_id].append({'currency': currency_symbol, 'timeframe': None, 'task_id': None})
    await message.reply(f"Вы выбрали {message.text}. Выберете TimeFrame:", reply_markup=main_menu)


@dp.message_handler(lambda message: message.text in ["1m", "5m", "15m", "30m", "1h", "4h"])
async def handle_timeframe(message: types.Message):
    chat_id = message.chat.id
    if not trade_tasks:
        await message.reply("Бот запущен заново.", reply_markup=currency_menu)
        return

    last_currency_selection = next((item for item in trade_tasks[chat_id] if item['timeframe'] is None), None)

    if not last_currency_selection:
        await message.reply("Сначала выберите валюту.", reply_markup=currency_menu)
        return

    timeframe_param = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "1h": "60", "4h": "240"}[message.text]
    task_id = generate_task_id(chat_id, last_currency_selection['currency'], timeframe_param)

    # Обновить информацию о задаче
    last_currency_selection.update({'timeframe': timeframe_param, 'task_id': task_id})

    # Запуск торгового цикла для новой задачи
    asyncio.create_task(trade_loop(task_id, timeframe_param, last_currency_selection['currency'], chat_id))
    await message.reply(f"Бот запущен на<b> {message.text} для {last_currency_selection['currency']}</b>.", reply_markup=main_menu, parse_mode=types.ParseMode.HTML)

@dp.message_handler(lambda message: message.text == "Закончить все процессы")
async def stop_bot(message: types.Message):
    print("----=== STOP ===----")
    chat_id = message.chat.id
    if chat_id in trade_tasks:
        del trade_tasks[chat_id]
        await message.reply("Все процессы завершены...", reply_markup=currency_menu)


if __name__ == '__main__':
    executor.start_polling(dp)