import os
import time


from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    CallbackQuery,
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from db import (
    # init_db,
    get_conn,
    add_user,
    user_exists,
    get_user,
    update_best_score,
    get_top_players,
    add_game_played,
    get_all_users,
    reset_all_scores,
    change_user_nickname,
)

from game import mixin_generate, generate_question, generate_options
from utils import HELP_MENU, main_menu, mode_keyboard, build_options_keyboard

router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID"))


TOTAL_QUESTIONS = 20
leaderboard_modes = {
    "جمع": "score_add",
    "تفریق": "score_sub",
    "ضرب": "score_mul",
    "تقسیم": "score_div",
    "میکس": "score_mix",
}


class GameState(StatesGroup):
    waiting_for_nickname = State()
    choosing_mode = State()
    playing = State()


@router.message(CommandStart())
async def start_handler(pm: Message, state: FSMContext):
    if user_exists(pm.from_user.id):
        await pm.answer("خوش برگشتی 👋", reply_markup=main_menu)
        return

    await pm.answer("اسمت (فارسی) چیه؟ این اسم توی رتبه‌بندی نمایش داده میشه 👤")
    await state.set_state(GameState.waiting_for_nickname)


@router.message(Command("help"))
async def help_handler(pm: Message):
    await pm.answer(HELP_MENU, reply_markup=main_menu)


@router.message(Command("newgame"))
@router.message(F.text == "🎮 شروع بازی")
async def newgame_handler(pm: Message, state: FSMContext):
    user = get_user(pm.from_user.id)

    if not user:
        await pm.answer("اول با /start پروفایل بساز 👤")
        return

    await state.clear()

    await pm.answer("حالت بازی رو انتخاب کن 👇", reply_markup=mode_keyboard)
    await state.set_state(GameState.choosing_mode)


@router.message(Command("profile"))
@router.message(F.text == "👤 پروفایل من")
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


@router.message(Command("leaderboard"))
@router.message(F.text == "🏆 برترین ها")
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

        text_parts.append("")

    await pm.answer("\n".join(text_parts))


@router.message(Command("log"))
async def log_handler(pm: Message):
    if pm.from_user.id != ADMIN_ID:
        await pm.answer("❌ شما اجازه دسترسی به این بخش را ندارید.")
        return

    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT SUM(games_played) FROM users")
    total_games = c.fetchone()[0] or 0

    conn.close()

    await pm.answer(
        f"📊 آمار سرور:\n"
        f"تعداد کل کاربران: {total_users}\n"
        f"تعداد کل بازی‌های انجام شده: {total_games}"
    )


@router.message(Command("send"))
async def send_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ فقط ادمین می‌تواند این پیام را ارسال کند")
        return

    text = message.text[len("/send") :].strip()
    if not text:
        await message.answer("❌ لطفا متن پیام را بعد از /send وارد کنید")
        return

    users = get_all_users()
    count = 0
    for user_id in users:
        try:
            await message.bot.send_message(chat_id=user_id, text=text)
            count += 1
        except:
            pass

    await message.answer(f"✅ پیام به {count} کاربر ارسال شد")


@router.message(Command("reset"))
async def reset_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما اجازه انجام این دستور را ندارید.")
        return

    reset_all_scores()

    await message.answer("✅ تمام امتیازات کاربران ریست شد.")


@router.message(Command("change_name"))
async def change_name_handler(pm: Message):
    if pm.from_user.id != ADMIN_ID:
        await pm.answer("❌ فقط ادمین می‌تواند این دستور را اجرا کند")
        return

    parts = pm.text.split(maxsplit=2)

    if len(parts) < 3:
        await pm.answer("❌ فرمت درست:\n/change_name old_name new_name")
        return

    old_name = parts[1]
    new_name = parts[2]

    updated = change_user_nickname(old_name, new_name)

    if updated == 0:
        await pm.answer("⚠️ کاربری با این اسم پیدا نشد")
    else:
        await pm.answer(f"✅ نام کاربر با موفقیت به «{new_name}» تغییر کرد")


#########################


# @router.message(GameState.choosing_mode)
# async def mode_handler(pm: Message, state: FSMContext):
#     text = pm.text

#     mode_map = {
#         "➕ جمع": "+",
#         "➖ تفریق": "-",
#         "✖️ ضرب": "*",
#         "➗ تقسیم": "/",
#         "⚡ میکس": "mixin",
#     }

#     if text not in mode_map:
#         await pm.answer(
#             "لطفا یکی از گزینه‌ها رو انتخاب کن 👇", reply_markup=mode_keyboard
#         )
#         return

#     mode = mode_map[text]

#     start_msg = await pm.answer("بازی شروع شد 🧠", reply_markup=ReplyKeyboardRemove())

#     if mode == "mixin":
#         q, ans = mixin_generate()
#     else:
#         q, ans = generate_question(mode)

#     question_msg = await pm.answer(f"1: {q} = ?")

#     await state.update_data(
#         mode=mode,
#         question_number=1,
#         correct=0,
#         wrong=0,
#         start_time=time.time(),
#         current_answer=ans,
#         question_message_id=question_msg.message_id,
#     )

#     await state.set_state(GameState.playing)


# @router.message(GameState.playing)
# async def answer_handler(pm: Message, state: FSMContext):
#     data = await state.get_data()

#     mode = data.get("mode")
#     q_num = data.get("question_number", 1)
#     correct = data.get("correct", 0)
#     wrong = data.get("wrong", 0)
#     correct_answer = data.get("current_answer")
#     question_message_id = data.get("question_message_id")
#     start_message_id = data.get("start_message_id")

#     try:
#         await pm.delete()
#     except:
#         pass

#     try:
#         user_answer = int(pm.text)
#     except ValueError:
#         wrong += 1
#     else:
#         if user_answer == correct_answer:
#             correct += 1
#         else:
#             wrong += 1

#     if q_num >= TOTAL_QUESTIONS:
#         total_time = round(time.time() - data.get("start_time", time.time()), 2)
#         score = (correct * 100) - (wrong * 200) - int(total_time * 2)

#         update_best_score(pm.from_user.id, mode, score)
#         add_game_played(pm.from_user.id)
#         for msg_id in [question_message_id, start_message_id]:
#             try:
#                 await pm.bot.delete_message(pm.chat.id, msg_id)
#             except:
#                 pass
#         mode_title_map = {
#             "+": "جمع",
#             "-": "تفریق",
#             "*": "ضرب",
#             "/": "تقسیم",
#             "mixin": "میکس",
#         }
#         mode_title = mode_title_map.get(mode, "نامشخص")
#         await pm.answer(
#             f"🎯 نتیجه نهایی در {mode_title}\n"
#             f"تعداد درست‌ها: {correct}\n"
#             f"تعداد غلط‌ها: {wrong}\n"
#             f"زمان: {total_time} ثانیه\n"
#             "-------------------\n"
#             f"امتیاز شما: {score}",
#             reply_markup=main_menu,
#         )

#         await state.clear()
#         return

#     if mode == "mixin":
#         q, ans = mixin_generate()
#     else:
#         q, ans = generate_question(mode)

#     await state.update_data(
#         question_number=q_num + 1, correct=correct, wrong=wrong, current_answer=ans
#     )

#     try:
#         await pm.bot.edit_message_text(
#             chat_id=pm.chat.id,
#             message_id=question_message_id,
#             text=f"{q_num + 1}: {q} = ?",
#         )
#     except:
#         new_msg = await pm.answer(f"{q_num + 1}: {q} = ?")
#         await state.update_data(question_message_id=new_msg.message_id)


@router.message(GameState.choosing_mode)
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

    options = generate_options(ans)
    keyboard = build_options_keyboard(options)

    question_msg = await pm.answer(f"1️⃣ {q} = ؟", reply_markup=keyboard)

    await state.update_data(
        mode=mode,
        question_number=1,
        correct=0,
        wrong=0,
        start_time=time.time(),
        current_answer=ans,
        question_message_id=question_msg.message_id,
        start_message_id=start_msg.message_id,
    )

    await state.set_state(GameState.playing)


@router.callback_query(GameState.playing, F.data.startswith("ans:"))
async def answer_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    mode = data.get("mode")
    q_num = data.get("question_number", 1)
    correct = data.get("correct", 0)
    wrong = data.get("wrong", 0)
    correct_answer = data.get("current_answer")
    question_message_id = data.get("question_message_id")
    start_message_id = data.get("start_message_id")

    user_answer = int(callback.data.split(":")[1])

    if user_answer == correct_answer:
        correct += 1
        result_emoji = "✅"
    else:
        wrong += 1
        result_emoji = "❌"

    # اگر بازی تموم شد
    if q_num >= TOTAL_QUESTIONS:
        total_time = round(time.time() - data.get("start_time", time.time()), 2)
        score = (correct * 100) - (wrong * 200) - int(total_time * 2)

        update_best_score(callback.from_user.id, mode, score)
        add_game_played(callback.from_user.id)

        for msg_id in [question_message_id, start_message_id]:
            try:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
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

        await callback.message.answer(
            f"🎯 نتیجه نهایی در {mode_title}\n"
            f"تعداد درست‌ها: {correct}\n"
            f"تعداد غلط‌ها: {wrong}\n"
            f"زمان: {total_time} ثانیه\n"
            "-------------------\n"
            f"امتیاز شما: {score}",
            reply_markup=main_menu,
        )

        await state.clear()
        await callback.answer()
        return

    # سوال بعدی
    if mode == "mixin":
        q, ans = mixin_generate()
    else:
        q, ans = generate_question(mode)

    options = generate_options(ans)
    keyboard = build_options_keyboard(options)

    await state.update_data(
        question_number=q_num + 1,
        correct=correct,
        wrong=wrong,
        current_answer=ans,
    )

    try:
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=question_message_id,
            text=f"{result_emoji}\n\n{q_num + 1}️⃣ {q} = ؟",
            reply_markup=keyboard,
        )
    except:
        new_msg = await callback.message.answer(
            f"{q_num + 1}️⃣ {q} = ؟",
            reply_markup=keyboard,
        )
        await state.update_data(question_message_id=new_msg.message_id)

    await callback.answer()


@router.message(GameState.waiting_for_nickname)
async def nickname_handler(pm: Message, state: FSMContext):
    nickname = pm.text.strip()

    add_user(pm.from_user.id, nickname)

    await pm.answer("پروفایلت ساخته شد ✅", reply_markup=main_menu)
    await state.set_state(GameState.choosing_mode)
