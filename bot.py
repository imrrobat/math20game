import asyncio
import random
import time
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from utils import START_MENU
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


load_dotenv()
API = os.getenv("API")

TOTAL_QUESTIONS = 20

mode_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ جمع"), KeyboardButton(text="➖ تفریق")],
        [KeyboardButton(text="✖️ ضرب"), KeyboardButton(text="➗ تقسیم")],
        [KeyboardButton(text="⚡ میکس")],  # حالت میکس اضافه شد
    ],
    resize_keyboard=True,
)


class GameState(StatesGroup):
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
        display_op = "˟"  # علامت نمایشی
    else:  # /
        answer = n1 * n2  # تضمین تقسیم صحیح
        n1 = answer
        display_op = "÷"

    return f"{n1} {display_op} {n2}", answer


def generate_question(mode="+"):
    n1 = random.randint(0, 9)
    n2 = random.randint(1, 9)

    op = mode

    # محاسبه جواب واقعی
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
        display_op = "x"  # برای نمایش ضرب
    elif op == "/":
        # تقسیم درست: جواب عدد صحیح
        answer = random.randint(1, 9)
        n2 = random.randint(1, 9)
        n1 = answer * n2
        display_op = "÷"  # برای نمایش تقسیم

    return f"{n1} {display_op} {n2}", answer


async def start_handler(pm: Message):
    await pm.answer(START_MENU)


async def newgame_handler(pm: Message, state: FSMContext):
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

    # پیام شروع بازی جدا
    start_msg = await pm.answer("بازی شروع شد 🧠", reply_markup=ReplyKeyboardRemove())

    # تولید سوال اول
    if mode == "mixin":
        q, ans = mixin_generate()
    else:
        q, ans = generate_question(mode)

    question_msg = await pm.answer(f"1: {q} = ?")

    # ذخیره اطلاعات در state
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

    # حذف پیام کاربر برای تمیز بودن چت
    try:
        await pm.delete()
    except:
        pass

    # بررسی جواب کاربر
    try:
        user_answer = int(pm.text)
    except ValueError:
        wrong += 1
    else:
        if user_answer == correct_answer:
            correct += 1
        else:
            wrong += 1

    # اگر بازی تموم شده
    if q_num >= TOTAL_QUESTIONS:
        total_time = round(time.time() - data.get("start_time", time.time()), 2)
        score = (correct * 100) - (wrong * 150) - int(total_time * 2)
        score = max(0, score)

        # حذف پیام سوال آخر و پیام شروع بازی
        for msg_id in [question_message_id, start_message_id]:
            try:
                await pm.bot.delete_message(pm.chat.id, msg_id)
            except:
                pass

        # نمایش نتیجه نهایی
        await pm.answer(
            "🎯 نتیجه نهایی\n"
            f"تعداد درست‌ها: {correct}\n"
            f"تعداد غلط‌ها: {wrong}\n"
            f"زمان: {total_time} ثانیه\n"
            "-------------------\n"
            f"امتیاز شما: {score}"
        )

        await state.clear()
        return

    # تولید سوال بعدی بر اساس مود
    if mode == "mixin":
        q, ans = mixin_generate()
    else:
        q, ans = generate_question(mode)

    # بروزرسانی state
    await state.update_data(
        question_number=q_num + 1, correct=correct, wrong=wrong, current_answer=ans
    )

    # سعی در ادیت پیام سوال قبلی
    try:
        await pm.bot.edit_message_text(
            chat_id=pm.chat.id,
            message_id=question_message_id,
            text=f"{q_num + 1}: {q} = ?",
        )
    except:
        # اگر قابل ادیت نبود، پیام جدید بفرست و id جدید ذخیره کن
        new_msg = await pm.answer(f"{q_num + 1}: {q} = ?")
        await state.update_data(question_message_id=new_msg.message_id)


async def main():
    bot = Bot(API)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(newgame_handler, Command("newgame"))
    dp.message.register(mode_handler, GameState.choosing_mode)
    dp.message.register(answer_handler, GameState.playing)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
