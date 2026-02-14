from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


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
