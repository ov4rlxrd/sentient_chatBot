import logging
import asyncio
import json
import datetime
import requests

from fireworks.client import Fireworks

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, \
    FSInputFile
from aiogram.filters import CommandStart, or_f, StateFilter
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from BD import create_connection, execute_query, execute_read_query
from kb import kb_1

API_TOKEN = "UR API TOKEN"

dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=API_TOKEN)

client = Fireworks(api_key="UR API TOKEN")


create_users_table = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    chat_history TEXT
);
"""
class ChatState(StatesGroup):
    chat_with_dobby = State()
    market_analysis = State()




@dp.message(CommandStart())
async def start_bot(message: Message):
    await message.answer("Hi, im Dobby, im here to help you\n\nMade by @ov4rlxrd for Sentient ❤️\n\nPlease note that this is an unofficial bot created to demonstrate the capabilities of the model. Stay safe!", reply_markup=kb_1)

@dp.callback_query(F.data == "chat_with_dobby")
async def start_chat_with_dobby(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChatState.chat_with_dobby)
    cur = await state.get_state()
    print(f"[DEBUG] state after set: {cur}")
    await callback.message.answer("What can i do for you?\n\nType exit to go back to the main menu ↩️")
    await callback.answer()


@dp.message(StateFilter(ChatState.chat_with_dobby), F.text.lower() == "exit")
async def exit_chat(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bye!")
    await message.answer("Hi, im Dobby im here to help you\n\nMade by @ov4rlxrd for Sentient ❤️", reply_markup=kb_1)

@dp.message(StateFilter(ChatState.chat_with_dobby), F.text)
async def chat_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    raw_history = execute_read_query(connection, "SELECT chat_history FROM users WHERE user_id = ?", (user_id,))
    if raw_history and raw_history[0][0]:
        messages = json.loads(raw_history[0][0])
    else:
        messages = [{"role": "system", "content": "You are a friendly assistant."}]

    messages.append({"role": "user", "content": message.text})

    response = client.chat.completions.create(
        model="accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new",
        messages=messages
    )

    answer = response.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    execute_query(
    connection,
    "INSERT INTO users (user_id, chat_history) VALUES (?, ?) "
    "ON CONFLICT(user_id) DO UPDATE SET chat_history = ?",
    (user_id, json.dumps(messages), json.dumps(messages))
)
    

    await message.answer(answer)
    

@dp.callback_query(F.data == "market_analysis")
async def market_analysis(callback: CallbackQuery, state: FSMContext):
    API_KEY = "UR API TOKEN"
    symbols = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC"]
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    end_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    params = {
        "symbol": ",".join(symbols),
        "convert": "USD"
    }

    headers = {
        "X-CMC_PRO_API_KEY": API_KEY,
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    # print(data)  
    prices = {}
    price_dates = {}
    crypto_info = {}

    for sym in symbols:
        crypto_info[sym] = {
            "price": data["data"][sym]["quote"]["USD"]["price"],
            "last_updated": data["data"][sym]["quote"]["USD"]["last_updated"]
    }
    print(crypto_info)

    prompt = (
        "You are a professional cryptocurrency market analyst. I will give you the latest prices for the main cryptocurrencies, "
        "and your task is to analyze the market situation, assess possible short-term and medium-term trends, and give your opinion "
        "on potential risks and opportunities for investors.\n\n"
        "Here are the latest market data:\n"
    )
    for sym, info in crypto_info.items():
        prompt += f"- {sym}: ${info['price']} updated in {info['last_updated']}\n"
    
    
    prompt += (
        "\nPlease provide:\n"
        "1. General market sentiment (bullish, bearish, or neutral).\n"
        "2. Key observations from current price levels and volatility.\n"
        "3. Short-term prediction (next 3–7 days) and possible catalysts.\n"
        "4. Medium-term outlook (next 1–2 months).\n"
        "5. Potential risks for investors right now.\n"
        "6. Opportunities for profit if any.\n"
        "Give your answer in a structured format."
    )
    response = client.chat.completions.create(
        model="accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]
    )
    await callback.message.answer(response.choices[0].message.content)
    await callback.message.answer("‼️‼️Please note that the information provided in Dobby may be incomplete. This is not financial advice, but merely one example of how this model can be used.‼️‼️")
    await callback.answer()

# inline mode
@dp.inline_query()
async def inline_handler(inline_query: InlineQuery):
    query_text = inline_query.query.strip()

    if not query_text:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Hi, im Dobby ask me about u want 🤖",
                description="Type ur question",
                input_message_content=InputTextMessageContent(
                    message_text="Type ur question 👇"
                ),
            )
        ]
        await bot.answer_inline_query(inline_query.id, results=results, cache_time=1)
        return

    response = client.chat.completions.create(
        model="accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new",
        messages=[
            {"role": "system", "content": "You are a friendly assistant."},
            {"role": "user", "content": query_text},
        ]
    )

    answer = response.choices[0].message.content

    result_id: str = hashlib.md5(query_text.encode()).hexdigest()
    article = InlineQueryResultArticle(
        id=result_id,
        title=f"Answer on: {query_text}",
        description=answer[:50] + "..." if len(answer) > 50 else answer,
        input_message_content=InputTextMessageContent(message_text=answer),
    )

    await bot.answer_inline_query(inline_query.id, results=[article], cache_time=1)




connection = create_connection("users.sqlite")
execute_query(connection, create_users_table)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    await dp.start_polling(bot)


if __name__ == '__main__':

    asyncio.run(main())
