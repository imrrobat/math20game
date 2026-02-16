import sqlite3

DB_NAME = "game.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            nickname TEXT NOT NULL,
            score_add INTEGER DEFAULT 0,
            score_sub INTEGER DEFAULT 0,
            score_mul INTEGER DEFAULT 0,
            score_div INTEGER DEFAULT 0,
            score_mix INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0
        )
        """
    )

    conn.commit()
    conn.close()


def add_user(user_id: int, nickname: str):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users 
        (user_id, nickname, score_add, score_sub, score_mul, score_div, score_mix)
        VALUES (?, ?, 0, 0, 0, 0, 0)
    """,
        (user_id, nickname),
    )

    conn.commit()
    conn.close()


def user_exists(user_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result is not None


def get_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT nickname,
               score_add,
               score_sub,
               score_mul,
               score_div,
               score_mix
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    )

    row = cur.fetchone()
    conn.close()

    return row


def update_best_score(user_id: int, mode: str, new_score: int):
    """
    mode: '+', '-', '*', '/', 'mixin'
    """

    column_map = {
        "+": "score_add",
        "-": "score_sub",
        "*": "score_mul",
        "/": "score_div",
        "mixin": "score_mix",
    }

    column = column_map.get(mode)
    if not column:
        return

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # گرفتن امتیاز فعلی
    cur.execute(f"SELECT {column} FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return

    current_score = row[0] or 0

    # اگر رکورد جدید بهتر بود → آپدیت
    if new_score > current_score:
        cur.execute(
            f"UPDATE users SET {column} = ? WHERE user_id = ?",
            (new_score, user_id),
        )
        conn.commit()

    conn.close()


def get_top_players(column: str, limit: int = 5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT nickname, {column}
        FROM users
        WHERE {column} > 0
        ORDER BY {column} DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def add_game_played(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "UPDATE users SET games_played = games_played + 1 WHERE user_id = ?", (user_id,)
    )

    conn.commit()
    conn.close()


def get_all_users():
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT telegram_id FROM users")
    rows = c.fetchall()

    conn.close()

    # تبدیل [(123,), (456,)] ➜ [123, 456]
    return [row[0] for row in rows]


def reset_all_scores():
    conn = get_conn()
    c = conn.cursor()

    c.execute(
        """
        UPDATE users
        SET
            score_add = 0,
            score_sub = 0,
            score_mul = 0,
            score_div = 0,
            score_mix = 0,
            games_played = 0
    """
    )

    conn.commit()
    conn.close()
