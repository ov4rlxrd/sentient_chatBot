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
load_dotenv()

API_TOKEN = os.getenv("TG_API_TOKEN")

dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=API_TOKEN)


client = Fireworks(api_key=os.getenv("FW_API_KEY"))

BEARER_TOKEN = os.getenv("BEARER_TOKEN")

create_users_table = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    chat_history TEXT
);
"""
class ChatState(StatesGroup):
    chat_with_dobby = State()
    market_analysis = State()
    ai_battle_1 = State()
    ai_battle_2 = State()
    ai_battle_3 = State()
    roma_search = State()
    tweet_details = State()



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

@dp.callback_query(F.data == 'ai_battle')
async def ai_battle_1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChatState.ai_battle_1)
    await callback.message.answer("Welcome to AI Battle, Here, Dobby will analyze the two people you entered and try to predict what their battle would look like in the comics. Please enter first fighter 👇")
    await callback.answer()

@dp.message(StateFilter(ChatState.ai_battle_1), F.text)
async def ai_battle_2(message: Message, state: FSMContext):
    await state.update_data(fighter1=message.text)
    await message.answer("Enter second fighter 👇")
    await state.set_state(ChatState.ai_battle_2)

@dp.message(StateFilter(ChatState.ai_battle_2), F.text)
async def ai_battle_3(message: Message, state: FSMContext):
    await state.update_data(fighter2=message.text)
    await message.answer("Please wait!")
    data = await state.get_data()
    prompt = f'Describe an epic battle between {data["fighter1"]} and {data["fighter2"]} in 3 rounds, as if they were comic book heroes, without politics or hate speech. Add humor and drama. At the end, name the winner.'
    response = client.chat.completions.create(
            model="accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}]
        )
    await message.answer(response.choices[0].message.content)
    await message.answer("‼️‼️Please note that the information provided in Dobby may be incomplete.")
    await message.answer("Hi, im Dobby im here to help you\n\nMade by @ov4rlxrd for Sentient ❤️", reply_markup=kb_1)

@dp.callback_query(F.data == 'tweet_details')
async def tweet_details_1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChatState.tweet_details)
    await callback.message.answer("Please enter the tweet URL 👇")
    await callback.answer()


@dp.message(StateFilter(ChatState.tweet_details), F.text)
async def tweet_details_2(message: Message, state: FSMContext):
    prompt = (
        "You are a social media analyst. I will provide you with posts from Twitter (X)." 
        "Your task is to:"

        "1. Identify the main topic and context of the post. " 
        "2. Determine the emotional tone (positive, neutral, negative).  "
        "3. Define the target audience (e.g., investors, fans, project community, general public, etc.)."
        "4. Summarize the post in 1–2 sentences.  "
        "5. (Optional) Suggest an idea for a reply or retweet if appropriate."
        "Post text is below:\n"
    )

    text = get_tweet_text(message.text)
    prompt += text

    response = client.chat.completions.create(
        model="accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new",
        messages=[{"role": "system", "content": "You are a social media analyst"},
                  {"role": "user", "content": prompt}]
    )
    await message.answer(response.choices[0].message.content)

def get_tweet_text(url: str) -> str:

    tweet_id = url.rstrip("/").split("/")[-1]

    endpoint = f"https://api.twitter.com/2/tweets/{tweet_id}?tweet.fields=created_at,author_id"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    response = requests.get(endpoint, headers=headers)

    data = response.json()
    return data["data"]["text"]




@dp.callback_query(F.data == 'roma_search')
async def roma_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChatState.roma_search)
    await callback.message.answer("Describe what you want to research or accomplish.. 👇")
    await callback.answer()


@dp.message(StateFilter(ChatState.roma_search), F.text)
async def roma_search_2(message: Message, state: FSMContext):
    user_search = message.text
    await message.answer("Sending your request to the server...")
    
    timeout = aiohttp.ClientTimeout(total=3600)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(API_URL, json={"goal": user_search, "profile": "general_agent"}) as resp:
            if resp.status != 200: 
                await message.answer(f"Server returned error: {resp.status}")
                return
            task = await resp.json()

    status = task.get("status")
    if status.lower() == "completed":
        with open("task_debug.json", "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        content = task["final_output"]
        await message.answer(content)
    else:
        await message.answer(f"Task status: {status}. Result not ready yet.")
    
    await state.clear()





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



