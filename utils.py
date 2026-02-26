from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


HELP_MENU = """
سلام! این یه بازیه برای شکوندن قلنج مغزی شما 😃 
20 تا سوال ریاضی میپرسم و هر چی تونستی باید زود جواب بدی، جواب‌های غلط هم نمره منفی دارن! 

شروع: /newgame
پروفایل شما: /profile
برترین‌ها: /leaderboard
"""


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎮 شروع بازی")],
        [KeyboardButton(text="👤 پروفایل من")],
        [KeyboardButton(text="🏆 برترین ها")],
    ],
    resize_keyboard=True,
)

mode_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ جمع"), KeyboardButton(text="➖ تفریق")],
        [KeyboardButton(text="✖️ ضرب"), KeyboardButton(text="➗ تقسیم")],
        [KeyboardButton(text="⚡ میکس")],  # حالت میکس اضافه شد
    ],
    resize_keyboard=True,
)


def build_options_keyboard(options):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(opt), callback_data=f"ans:{opt}")]
            for opt in options
        ]
    )
    return keyboard
