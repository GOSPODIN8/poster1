import aiosqlite
import time
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    posted_at INTEGER,
    text_preview TEXT,
    had_image INTEGER,
    success INTEGER,
    error TEXT
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def log_post(text_preview: str, had_image: bool, success: bool, error: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO posts (posted_at, text_preview, had_image, success, error) VALUES (?, ?, ?, ?, ?)",
            (int(time.time()), text_preview[:200], int(had_image), int(success), error[:300]),
        )
        await db.commit()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COUNT(*) as c FROM posts WHERE success = 1")
        total_ok = (await cur.fetchone())["c"]

        cur = await db.execute("SELECT COUNT(*) as c FROM posts WHERE success = 0")
        total_fail = (await cur.fetchone())["c"]

        day_ago = int(time.time()) - 86400
        cur = await db.execute("SELECT COUNT(*) as c FROM posts WHERE posted_at >= ? AND success = 1", (day_ago,))
        today_ok = (await cur.fetchone())["c"]

        cur = await db.execute(
            "SELECT posted_at, success, error FROM posts ORDER BY posted_at DESC LIMIT 5"
        )
        last_posts = await cur.fetchall()

        return {
            "total_ok": total_ok,
            "total_fail": total_fail,
            "today_ok": today_ok,
            "last_posts": last_posts,
        }
