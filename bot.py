import asyncio
import random
import time
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from utils import HELP_MENU, main_menu
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from db import (
    init_db,
    get_conn,
    add_user,
    user_exists,
    get_user,
    update_best_score,
    get_top_players,
    add_game_played,
)

init_db()
load_dotenv()
API = os.getenv("API")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

TOTAL_QUESTIONS = 20
leaderboard_modes = {
    "جمع": "score_add",
    "تفریق": "score_sub",
    "ضرب": "score_mul",
    "تقسیم": "score_div",
    "میکس": "score_mix",
}

mode_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ جمع"), KeyboardButton(text="➖ تفریق")],
        [KeyboardButton(text="✖️ ضرب"), KeyboardButton(text="➗ تقسیم")],
        [KeyboardButton(text="⚡ میکس")],  # حالت میکس اضافه شد
    ],
    resize_keyboard=True,
)


class GameState(StatesGroup):
    waiting_for_nickname = State()
    choosing_mode = State()
    playing = State()


def mixin_generate():
    n1 = random.randint(0, 9)
    n2 = random.randint(1, 9)

    op = random.choice("+-*/")

    if op == "+":
        answer = n1 + n2
        display_op = "+"
    elif op == "-":
        if n1 < n2:
            n1, n2 = n2, n1
        answer = n1 - n2
        display_op = "-"
    elif op == "*":
        answer = n1 * n2
        display_op = "x"
    else:
        answer = random.randint(1, 9)
        n2 = random.randint(1, 9)
        n1 = answer * n2
        display_op = "÷"

    return f"{n1} {display_op} {n2}", answer


def generate_question(mode="+"):
    n1 = random.randint(0, 9)
    n2 = random.randint(1, 9)

    op = mode

    if op == "+":
        answer = n1 + n2
        display_op = "+"
    elif op == "-":
        if n1 < n2:
            n1, n2 = n2, n1
        answer = n1 - n2
        display_op = "-"
    elif op == "*":
        answer = n1 * n2
        display_op = "x"
    elif op == "/":
        answer = random.randint(1, 9)
        n2 = random.randint(1, 9)
        n1 = answer * n2
        display_op = "÷"

    return f"{n1} {display_op} {n2}", answer


async def start_handler(pm: Message, state: FSMContext):
    if user_exists(pm.from_user.id):
        await pm.answer("خوش برگشتی 👋", reply_markup=main_menu)
        return

    await pm.answer("اسمت چیه؟ این اسم توی رتبه‌بندی نمایش داده میشه 👤")
    await state.set_state(GameState.waiting_for_nickname)


async def help_handler(pm: Message):
    await pm.answer(HELP_MENU, reply_markup=main_menu)


async def nickname_handler(pm: Message, state: FSMContext):
    nickname = pm.text.strip()

    add_user(pm.from_user.id, nickname)

    await pm.answer("پروفایلت ساخته شد ✅", reply_markup=main_menu)
    await state.set_state(GameState.choosing_mode)


async def newgame_handler(pm: Message, state: FSMContext):
    user = get_user(pm.from_user.id)

    if not user:
        await pm.answer("اول با /start پروفایل بساز 👤")
        return

    await state.clear()

    await pm.answer("حالت بازی رو انتخاب کن 👇", reply_markup=mode_keyboard)
    await state.set_state(GameState.choosing_mode)


async def mode_handler(pm: Message, state: FSMContext):
    text = pm.text

    mode_map = {
        "➕ جمع": "+",
        "➖ تفریق": "-",
        "✖️ ضرب": "*",
        "➗ تقسیم": "/",
        "⚡ میکس": "mixin",
    }

    if text not in mode_map:
        await pm.answer(
            "لطفا یکی از گزینه‌ها رو انتخاب کن 👇", reply_markup=mode_keyboard
        )
        return

    mode = mode_map[text]

    start_msg = await pm.answer("بازی شروع شد 🧠", reply_markup=ReplyKeyboardRemove())

    if mode == "mixin":
        q, ans = mixin_generate()
    else:
        q, ans = generate_question(mode)

    question_msg = await pm.answer(f"1: {q} = ?")

    await state.update_data(
        mode=mode,
        question_number=1,
        correct=0,
        wrong=0,
        start_time=time.time(),
        current_answer=ans,
        question_message_id=question_msg.message_id,
    )

    await state.set_state(GameState.playing)


async def answer_handler(pm: Message, state: FSMContext):
    data = await state.get_data()

    mode = data.get("mode")
    q_num = data.get("question_number", 1)
    correct = data.get("correct", 0)
    wrong = data.get("wrong", 0)
    correct_answer = data.get("current_answer")
    question_message_id = data.get("question_message_id")
    start_message_id = data.get("start_message_id")

    try:
        await pm.delete()
    except:
        pass

    try:
        user_answer = int(pm.text)
    except ValueError:
        wrong += 1
    else:
        if user_answer == correct_answer:
            correct += 1
        else:
            wrong += 1

    if q_num >= TOTAL_QUESTIONS:
        total_time = round(time.time() - data.get("start_time", time.time()), 2)
        score = (correct * 100) - (wrong * 200) - int(total_time * 2)
        # score = max(0, score)

        update_best_score(pm.from_user.id, mode, score)
        add_game_played(pm.from_user.id)
        for msg_id in [question_message_id, start_message_id]:
            try:
                await pm.bot.delete_message(pm.chat.id, msg_id)
            except:
                pass
        mode_title_map = {
            "+": "جمع",
            "-": "تفریق",
            "*": "ضرب",
            "/": "تقسیم",
            "mixin": "میکس",
        }
        mode_title = mode_title_map.get(mode, "نامشخص")
        await pm.answer(
            f"🎯 نتیجه نهایی در {mode_title}\n"
            f"تعداد درست‌ها: {correct}\n"
            f"تعداد غلط‌ها: {wrong}\n"
            f"زمان: {total_time} ثانیه\n"
            "-------------------\n"
            f"امتیاز شما: {score}",
            reply_markup=main_menu,
        )

        await state.clear()
        return

    if mode == "mixin":
        q, ans = mixin_generate()
    else:
        q, ans = generate_question(mode)

    await state.update_data(
        question_number=q_num + 1, correct=correct, wrong=wrong, current_answer=ans
    )

    try:
        await pm.bot.edit_message_text(
            chat_id=pm.chat.id,
            message_id=question_message_id,
            text=f"{q_num + 1}: {q} = ?",
        )
    except:
        new_msg = await pm.answer(f"{q_num + 1}: {q} = ?")
        await state.update_data(question_message_id=new_msg.message_id)


async def profile_handler(pm: Message):
    user = get_user(pm.from_user.id)

    if not user:
        await pm.answer("اول با /start پروفایل بساز 👤")
        return

    nickname, add, sub, mul, div, mix = user

    text = (
        "👤 پروفایل شما\n\n"
        f"نام مستعار: {nickname}\n\n"
        "🏆 امتیازها\n"
        f"➕ جمع: {add}\n"
        f"➖ تفریق: {sub}\n"
        f"✖️ ضرب: {mul}\n"
        f"➗ تقسیم: {div}\n"
        f"🎲 میکس: {mix}"
    )

    await pm.answer(text, reply_markup=main_menu)


async def leaderboard_handler(pm: Message):
    text_parts = []

    for title, column in leaderboard_modes.items():
        top_players = get_top_players(column)

        text_parts.append(f"🏆 بهترین امتیازات در حالت {title}:")

        if not top_players:
            text_parts.append("فعلا امتیازی ثبت نشده\n")
            continue

        for i, (nickname, score) in enumerate(top_players, start=1):
            map_i = {1: "اول", 2: "دوم", 3: "سوم", 4: "چهارم", 5: "پنجم"}
            text_parts.append(f"{map_i.get(i)}. {nickname} — {score}")

        text_parts.append("")  # خط خالی بین مودها

    await pm.answer("\n".join(text_parts))


async def log_handler(pm: Message):
    # بررسی اینکه فقط ادمین بتونه اجرا کنه
    if pm.from_user.id != ADMIN_ID:
        await pm.answer("❌ شما اجازه دسترسی به این بخش را ندارید.")
        return

    conn = get_conn()  # استفاده از تابع get_conn از db.py
    c = conn.cursor()

    # تعداد کاربران
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    # تعداد کل بازی‌ها
    c.execute("SELECT SUM(games_played) FROM users")
    total_games = c.fetchone()[0] or 0

    conn.close()

    await pm.answer(
        f"📊 آمار سرور:\n"
        f"تعداد کل کاربران: {total_users}\n"
        f"تعداد کل بازی‌های انجام شده: {total_games}"
    )


async def main():
    bot = Bot(API)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(newgame_handler, Command("newgame"))
    dp.message.register(profile_handler, Command("profile"))
    dp.message.register(leaderboard_handler, Command("leaderboard"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(log_handler, Command("log"))

    dp.message.register(newgame_handler, F.text == "🎮 شروع بازی")
    dp.message.register(profile_handler, F.text == "👤 پروفایل من")
    dp.message.register(leaderboard_handler, F.text == "🏆 برترین ها")
    # سپس state-based handlers
    dp.message.register(nickname_handler, GameState.waiting_for_nickname)
    dp.message.register(mode_handler, GameState.choosing_mode)
    dp.message.register(answer_handler, GameState.playing)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
