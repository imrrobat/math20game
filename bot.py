import asyncio
import random
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import API


TOTAL_QUESTIONS = 20


class GameState(StatesGroup):
    playing = State()


def generate_question():
    n1 = random.randint(0, 9)
    n2 = random.randint(0, 9)
    op = random.choice("+-")

    if op == "-" and n1 < n2:
        n1, n2 = n2, n1

    if op == "+":
        answer = n1 + n2
    else:
        answer = n1 - n2

    return f"{n1} {op} {n2}", answer


async def start_handler(pm: Message):
    await pm.answer("Welcome 👋\n" "For start new game type /newgame")


async def newgame_handler(pm: Message, state: FSMContext):
    await state.clear()

    q, ans = generate_question()

    await state.update_data(
        question_number=1,
        correct=0,
        wrong=0,
        start_time=time.time(),
        current_answer=ans,
    )

    await state.set_state(GameState.playing)

    await pm.answer(f"Game started 🧠\n\nQ1: {q} = ?")


async def answer_handler(pm: Message, state: FSMContext):
    data = await state.get_data()

    q_num = data["question_number"]
    correct = data["correct"]
    wrong = data["wrong"]
    correct_answer = data["current_answer"]

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
        total_time = round(time.time() - data["start_time"], 2)
        score = (correct * 100) - (wrong * 50) - int(total_time * 2)
        score = max(0, score)

        await pm.answer(
            "🎯 Final Result\n"
            f"Correct: {correct}\n"
            f"Wrong: {wrong}\n"
            f"Time: {total_time} sec\n"
            "-------------------\n"
            f"Score: {score}"
        )

        await state.clear()
        return

    q, ans = generate_question()

    await state.update_data(
        question_number=q_num + 1, correct=correct, wrong=wrong, current_answer=ans
    )

    await pm.answer(f"Q{q_num + 1}: {q} = ?")


async def main():
    bot = Bot(API)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(newgame_handler, Command("newgame"))
    dp.message.register(answer_handler, GameState.playing)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
