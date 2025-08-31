from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData

kb_1 = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Chat with Dobby 📚', callback_data='chat_with_dobby'),
            InlineKeyboardButton(text='Market analysis 📈', callback_data='market_analysis'),
        ],
        [
            InlineKeyboardButton(text='AI Battle ⚔️ ', callback_data='ai_battle'),
        ],
    ]
)

)
