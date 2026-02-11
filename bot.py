import asyncio
import random
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from menu import START_MENU
from config import API


TOTAL_QUESTIONS = 20


class GameState(StatesGroup):
    playing = State()


def generate_question():
    n1 = random.randint(0, 9)
    n2 = random.randint(1, 9)

    op = random.choice("+-*/")

    if op == "+":
        answer = n1 + n2

    elif op == "-":
        if n1 < n2:
            n1, n2 = n2, n1
        answer = n1 - n2

    elif op == "*":
        answer = n1 * n2

    else:
        answer = random.randint(0, 9)
        n2 = random.randint(1, 9)
        n1 = answer * n2

    return f"{n1} {op} {n2}", answer


async def start_handler(pm: Message):
    await pm.answer(START_MENU)


async def newgame_handler(pm: Message, state: FSMContext):
    await state.clear()

    q, ans = generate_question()

    msg = await pm.answer(f"بازی شروع شد 🧠\n\n{q} = ?")

    await state.update_data(
        question_number=1,
        correct=0,
        wrong=0,
        start_time=time.time(),
        current_answer=ans,
        question_message_id=msg.message_id,
    )

    await state.set_state(GameState.playing)


async def answer_handler(pm: Message, state: FSMContext):
    data = await state.get_data()

    q_num = data["question_number"]
    correct = data["correct"]
    wrong = data["wrong"]
    correct_answer = data["current_answer"]
    question_message_id = data["question_message_id"]

    # پاک کردن پیام کاربر برای تمیز موندن چت
    try:
        await pm.delete()
    except:
        pass

    # بررسی جواب
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
        total_time = round(time.time() - data["start_time"], 2)
        score = (correct * 100) - (wrong * 150) - int(total_time * 2)
        score = max(0, score)

        await pm.bot.edit_message_text(
            chat_id=pm.chat.id,
            message_id=question_message_id,
            text=(
                "🎯 نتیجه نهایی\n"
                f"تعداد درست ها: {correct}\n"
                f"تعداد غلط ها: {wrong}\n"
                f"زمان: {total_time} ثانیه\n"
                "-------------------\n"
                f"امتیاز شما: {score}"
            ),
        )

        await state.clear()
        return

    # سوال بعدی
    q, ans = generate_question()

    await state.update_data(
        question_number=q_num + 1, correct=correct, wrong=wrong, current_answer=ans
    )

    await pm.bot.edit_message_text(
        chat_id=pm.chat.id, message_id=question_message_id, text=f"{q} = ?"
    )


async def main():
    bot = Bot(API)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(newgame_handler, Command("newgame"))
    dp.message.register(answer_handler, GameState.playing)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
