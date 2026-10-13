
import time
import uuid
from pathlib import Path

import aiosqlite

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # PostgreSQL kutubxonasi o‘rnatilmagan bo‘lsa, SQLite ishlayveradi.
    psycopg = None
    dict_row = None

from nexus.config import settings


REWARD_AMOUNT = 10
COOLDOWN_SECONDS = 30 * 60
LEADERBOARD_LIMIT = 50


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL DEFAULT '',
    crystals INTEGER NOT NULL DEFAULT 0 CHECK (crystals >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_collect_at INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'telegram',
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_game_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_actions_user
ON actions(telegram_id);

CREATE INDEX IF NOT EXISTS idx_users_crystals
ON users(crystals DESC);

CREATE TABLE IF NOT EXISTS shop_items (
    item_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price INTEGER NOT NULL CHECK (price >= 0),
    kind TEXT NOT NULL DEFAULT 'cosmetic',
    emoji TEXT NOT NULL DEFAULT '✨',
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    purchased_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (telegram_id, item_id),
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id),
    FOREIGN KEY (item_id) REFERENCES shop_items(item_id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_user
ON inventory(telegram_id);

CREATE TABLE IF NOT EXISTS crystal_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    reference TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_user
ON crystal_transactions(telegram_id);

CREATE TABLE IF NOT EXISTS game_sessions (
    session_id TEXT PRIMARY KEY,
    telegram_id INTEGER NOT NULL,
    started_at INTEGER NOT NULL,
    finished_at INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    reward INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_game_sessions_user
ON game_sessions(telegram_id, started_at DESC);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL DEFAULT '',
    crystals BIGINT NOT NULL DEFAULT 0 CHECK (crystals >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_collect_at BIGINT NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'telegram',
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_game_at BIGINT NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS actions (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
    action_type TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_actions_user ON actions(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_crystals ON users(crystals DESC);
CREATE TABLE IF NOT EXISTS shop_items (
    item_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price BIGINT NOT NULL CHECK (price >= 0),
    kind TEXT NOT NULL DEFAULT 'cosmetic',
    emoji TEXT NOT NULL DEFAULT '✨',
    active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS inventory (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
    item_id TEXT NOT NULL REFERENCES shop_items(item_id),
    purchased_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (telegram_id, item_id)
);
CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(telegram_id);
CREATE TABLE IF NOT EXISTS crystal_transactions (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
    amount BIGINT NOT NULL,
    transaction_type TEXT NOT NULL,
    reference TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON crystal_transactions(telegram_id);
CREATE TABLE IF NOT EXISTS game_sessions (
    session_id TEXT PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
    started_at BIGINT NOT NULL,
    finished_at BIGINT NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    reward INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user ON game_sessions(telegram_id, started_at DESC);
CREATE TABLE IF NOT EXISTS nexus_migrations (
    name TEXT PRIMARY KEY,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""



DEFAULT_SHOP_ITEMS = [
    (
        "aura_green",
        "Emerald Aura",
        "Profil uchun yashil kosmik aura.",
        50,
        "effect",
        "🌿",
    ),
    (
        "frame_neon",
        "Neon Frame",
        "Neon uslubidagi profil ramkasi.",
        100,
        "frame",
        "💠",
    ),
    (
        "avatar_comet",
        "Comet Avatar",
        "Kometa mavzusidagi maxsus avatar.",
        150,
        "avatar",
        "☄️",
    ),
    (
        "aura_galaxy",
        "Galaxy Aura",
        "Galaktik binafsha effekt.",
        250,
        "effect",
        "🌌",
    ),
    (
        "frame_gold",
        "Royal Gold",
        "Oltin rangli premium ramka.",
        400,
        "frame",
        "👑",
    ),
]


class PostgresConnection:
    """SQLite funksiyalariga yaqin, kichik async psycopg adapteri."""
    def __init__(self, connection):
        self.connection = connection

    async def execute(self, sql, params=()):
        sql = sql.replace("?", "%s")
        if sql.strip().upper() in {"BEGIN", "BEGIN IMMEDIATE"}:
            # Psycopg autocommit=False tranzaksiyani birinchi so‘rovda boshlaydi.
            return await self.connection.execute("SELECT 1")
        return await self.connection.execute(sql, params or ())

    async def executemany(self, sql, rows):
        sql = sql.replace("?", "%s")
        async with self.connection.cursor() as cursor:
            await cursor.executemany(sql, rows)

    async def commit(self):
        await self.connection.commit()

    async def rollback(self):
        await self.connection.rollback()

    async def close(self):
        await self.connection.close()


async def connect():
    if settings.DATABASE_URL:
        if psycopg is None:
            raise RuntimeError("PostgreSQL uchun psycopg kutubxonasi o‘rnatilmagan.")
        url = settings.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        connection = await psycopg.AsyncConnection.connect(
            url, row_factory=dict_row, autocommit=False
        )
        return PostgresConnection(connection)

    db = await aiosqlite.connect(settings.database_file(), timeout=30)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("PRAGMA busy_timeout = 30000")
    return db


async def _import_legacy_sqlite_users(pg_db):
    """Agar eski Render/SQLite fayli hali mavjud bo‘lsa, balanslarni bir marta ko‘chiradi."""
    legacy_path = Path(settings.database_file())
    if not legacy_path.exists() or legacy_path.stat().st_size == 0:
        return
    cursor = await pg_db.execute("SELECT name FROM nexus_migrations WHERE name = ?", ("sqlite_users_import_v1",))
    if await cursor.fetchone():
        return
    old_db = await aiosqlite.connect(str(legacy_path))
    old_db.row_factory = aiosqlite.Row
    try:
        cursor = await old_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not await cursor.fetchone():
            return
        cursor = await old_db.execute("PRAGMA table_info(users)")
        columns = {row["name"] for row in await cursor.fetchall()}
        cursor = await old_db.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        for row_obj in rows:
            row = dict(row_obj)
            telegram_id = int(row.get("telegram_id") or 0)
            if telegram_id <= 0:
                continue
            await pg_db.execute("""INSERT INTO users
                (telegram_id, username, first_name, crystals, created_at, last_collect_at, source, last_game_at)
                VALUES (?, ?, ?, ?, COALESCE(?::timestamptz, CURRENT_TIMESTAMP), ?, ?, ?)
                ON CONFLICT (telegram_id) DO NOTHING""",
                (telegram_id, row.get("username"), row.get("first_name") or "",
                 int(row.get("crystals") or 0), row.get("created_at"),
                 int(row.get("last_collect_at") or 0),
                 row.get("source") if "source" in columns else "telegram",
                 int(row.get("last_game_at") or 0)))
        await pg_db.execute("INSERT INTO nexus_migrations(name) VALUES (?) ON CONFLICT (name) DO NOTHING", ("sqlite_users_import_v1",))
    finally:
        await old_db.close()


async def init_db():
    db = await connect()
    try:
        if settings.DATABASE_URL:
            for statement in POSTGRES_SCHEMA.split(";"):
                if statement.strip():
                    await db.execute(statement)
            await db.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'telegram'"
            )
            await db.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP"
            )
            await db.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_game_at BIGINT NOT NULL DEFAULT 0"
            )
            shop_insert = """INSERT INTO shop_items
                (item_id, name, description, price, kind, emoji)
                VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (item_id) DO NOTHING"""
        else:
            await db.execute("PRAGMA journal_mode = WAL")
            await db.executescript(SCHEMA)
            # Eski SQLite bazalarini yangilash.
            for statement in (
                "ALTER TABLE users ADD COLUMN source TEXT NOT NULL DEFAULT 'telegram'",
                "ALTER TABLE users ADD COLUMN last_seen_at TEXT NOT NULL DEFAULT ''",
                "ALTER TABLE users ADD COLUMN last_game_at INTEGER NOT NULL DEFAULT 0",
            ):
                try:
                    await db.execute(statement)
                except Exception as exc:
                    if "duplicate column" not in str(exc).lower():
                        raise
            shop_insert = """INSERT OR IGNORE INTO shop_items
                (item_id, name, description, price, kind, emoji)
                VALUES (?, ?, ?, ?, ?, ?)"""

        await db.executemany(shop_insert, DEFAULT_SHOP_ITEMS)
        if settings.DATABASE_URL:
            await _import_legacy_sqlite_users(db)
        else:
            await db.execute("UPDATE users SET last_seen_at = CURRENT_TIMESTAMP WHERE last_seen_at = ''")
        await db.commit()
    finally:
        await db.close()


async def upsert_user(user: dict, source: str = "telegram"):
    telegram_id = int(user["id"])
    username = user.get("username")
    first_name = user.get("first_name", "")
    source = source if source in {"telegram", "telegram_miniapp", "web"} else "telegram"
    db = await connect()
    try:
        await db.execute(
            """INSERT INTO users
                (telegram_id, username, first_name, source, last_seen_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                source = excluded.source,
                last_seen_at = CURRENT_TIMESTAMP""",
            (telegram_id, username, first_name, source),
        )
        await db.commit()
    finally:
        await db.close()


async def get_user(telegram_id: int):
    db = await connect()
    try:
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (int(telegram_id),),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_world_stats():
    db = await connect()
    try:
        cursor = await db.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM users) AS players,
                (SELECT COALESCE(SUM(crystals), 0) FROM users)
                    AS crystals,
                (SELECT COUNT(*) FROM actions) AS actions
            """
        )
        return dict(await cursor.fetchone())
    finally:
        await db.close()


async def get_leaderboard(limit: int = LEADERBOARD_LIMIT):
    limit = max(1, min(int(limit), LEADERBOARD_LIMIT))

    db = await connect()
    try:
        cursor = await db.execute(
            """
            SELECT
                telegram_id,
                username,
                first_name,
                crystals,
                ROW_NUMBER() OVER (
                    ORDER BY crystals DESC, created_at ASC, telegram_id ASC
                ) AS position
            FROM users
            ORDER BY crystals DESC, created_at ASC, telegram_id ASC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in await cursor.fetchall()]
    finally:
        await db.close()


async def get_player_position(telegram_id: int):
    db = await connect()
    try:
        cursor = await db.execute(
            """
            SELECT position
            FROM (
                SELECT
                    telegram_id,
                    ROW_NUMBER() OVER (
                        ORDER BY crystals DESC, created_at ASC,
                                 telegram_id ASC
                    ) AS position
                FROM users
            )
            WHERE telegram_id = ?
            """,
            (int(telegram_id),),
        )
        row = await cursor.fetchone()
        return int(row["position"]) if row else None
    finally:
        await db.close()


async def get_shop_items(telegram_id: int):
    db = await connect()
    try:
        cursor = await db.execute(
            """
            SELECT
                s.item_id,
                s.name,
                s.description,
                s.price,
                s.kind,
                s.emoji,
                CASE WHEN i.id IS NULL THEN 0 ELSE 1 END AS owned
            FROM shop_items AS s
            LEFT JOIN inventory AS i
                ON i.item_id = s.item_id
                AND i.telegram_id = ?
            WHERE s.active = 1
            ORDER BY s.price ASC, s.name ASC
            """,
            (int(telegram_id),),
        )
        return [dict(row) for row in await cursor.fetchall()]
    finally:
        await db.close()


async def get_inventory(telegram_id: int):
    db = await connect()
    try:
        cursor = await db.execute(
            """
            SELECT
                s.item_id,
                s.name,
                s.description,
                s.kind,
                s.emoji,
                i.purchased_at
            FROM inventory AS i
            JOIN shop_items AS s ON s.item_id = i.item_id
            WHERE i.telegram_id = ?
            ORDER BY i.id DESC
            """,
            (int(telegram_id),),
        )
        return [dict(row) for row in await cursor.fetchall()]
    finally:
        await db.close()


async def buy_shop_item(telegram_id: int, item_id: str):
    """
    Narxni klientdan olmaydi.
    Balans tekshiruvi, pul yechish va xarid yozuvi
    bitta tranzaksiyada bajariladi.
    """

    db = await connect()

    try:
        await db.execute("BEGIN IMMEDIATE")

        cursor = await db.execute(
            """
            SELECT item_id, name, price, active
            FROM shop_items
            WHERE item_id = ?
            """,
            (item_id,),
        )
        item = await cursor.fetchone()

        if not item or int(item["active"]) != 1:
            await db.rollback()
            return {"status": "item_not_found"}

        cursor = await db.execute(
            """
            SELECT crystals
            FROM users
            WHERE telegram_id = ?
            """,
            (int(telegram_id),),
        )
        user = await cursor.fetchone()

        if user is None:
            await db.rollback()
            return {"status": "user_not_found"}

        cursor = await db.execute(
            """
            SELECT id
            FROM inventory
            WHERE telegram_id = ? AND item_id = ?
            """,
            (int(telegram_id), item_id),
        )

        if await cursor.fetchone():
            await db.rollback()
            return {"status": "already_owned"}

        price = int(item["price"])
        balance = int(user["crystals"])

        if balance < price:
            await db.rollback()
            return {
                "status": "insufficient_funds",
                "crystals": balance,
                "price": price,
            }

        await db.execute(
            """
            UPDATE users
            SET crystals = crystals - ?
            WHERE telegram_id = ? AND crystals >= ?
            """,
            (price, int(telegram_id), price),
        )

        cursor = await db.execute(
            """
            SELECT crystals
            FROM users
            WHERE telegram_id = ?
            """,
            (int(telegram_id),),
        )
        updated_user = await cursor.fetchone()

        if updated_user is None:
            await db.rollback()
            return {"status": "user_not_found"}

        await db.execute(
            """
            INSERT INTO inventory (telegram_id, item_id)
            VALUES (?, ?)
            """,
            (int(telegram_id), item_id),
        )

        await db.execute(
            """
            INSERT INTO actions (telegram_id, action_type, details)
            VALUES (?, 'shop_purchase', ?)
            """,
            (int(telegram_id), item_id),
        )

        await db.execute(
            """
            INSERT INTO crystal_transactions
                (telegram_id, amount, transaction_type, reference)
            VALUES (?, ?, 'purchase', ?)
            """,
            (int(telegram_id), -price, item_id),
        )

        await db.commit()

        return {
            "status": "success",
            "item_id": item_id,
            "item_name": item["name"],
            "price": price,
            "crystals": int(updated_user["crystals"]),
        }

    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()


async def get_creator_overview():
    db = await connect()
    try:
        cursor = await db.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM users) AS players,
                (SELECT COALESCE(SUM(crystals), 0) FROM users)
                    AS total_crystals,
                (SELECT COUNT(*) FROM actions) AS total_actions,
                (SELECT COUNT(*) FROM inventory) AS total_purchases
            """
        )
        stats = dict(await cursor.fetchone())

        cursor = await db.execute(
            """
            SELECT
                telegram_id,
                username,
                first_name,
                crystals,
                created_at
            FROM users
            ORDER BY crystals DESC, created_at ASC
            LIMIT 10
            """
        )
        stats["top_players"] = [
            dict(row) for row in await cursor.fetchall()
        ]
        return stats
    finally:
        await db.close()


async def collect_crystals(telegram_id: int):
    """Har 30 daqiqada bir marta serverdan 10 kristall olish."""

    db = await connect()

    try:
        await db.execute("BEGIN IMMEDIATE")

        cursor = await db.execute(
            """
            SELECT crystals, last_collect_at
            FROM users
            WHERE telegram_id = ?
            """,
            (int(telegram_id),),
        )
        user = await cursor.fetchone()

        if user is None:
            await db.rollback()
            return {"status": "not_registered"}

        now = int(time.time())
        last_collect_at = int(user["last_collect_at"])
        next_allowed = last_collect_at + COOLDOWN_SECONDS

        if last_collect_at > 0 and now < next_allowed:
            remaining = next_allowed - now
            crystals = int(user["crystals"])
            await db.rollback()

            return {
                "status": "cooldown",
                "remaining": remaining,
                "crystals": crystals,
            }

        await db.execute(
            """
            UPDATE users
            SET crystals = crystals + ?,
                last_collect_at = ?
            WHERE telegram_id = ?
            """,
            (REWARD_AMOUNT, now, int(telegram_id)),
        )

        await db.execute(
            """
            INSERT INTO actions
                (telegram_id, action_type, details)
            VALUES (?, 'collect', ?)
            """,
            (int(telegram_id), f"+{REWARD_AMOUNT} crystals"),
        )

        await db.execute(
            """
            INSERT INTO crystal_transactions
                (telegram_id, amount, transaction_type, reference)
            VALUES (?, ?, 'collect', 'cooldown_reward')
            """,
            (int(telegram_id), REWARD_AMOUNT),
        )

        cursor = await db.execute(
            """
            SELECT crystals, last_collect_at
            FROM users
            WHERE telegram_id = ?
            """,
            (int(telegram_id),),
        )
        updated_user = await cursor.fetchone()

        await db.commit()

        return {
            "status": "success",
            "reward": REWARD_AMOUNT,
            "crystals": int(updated_user["crystals"]),
            "last_collect_at": int(updated_user["last_collect_at"]),
        }

    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()

# ==========================================
# CREATOR PANEL + GAME REWARDS
# ==========================================

GAME_DURATION_SECONDS = 15
GAME_COOLDOWN_SECONDS = 5 * 60
GAME_MAX_CLICKS = 60
GAME_MAX_REWARD = 30


async def get_admin_overview():
    db = await connect()
    try:
        cursor = await db.execute("""SELECT
            (SELECT COUNT(*) FROM users) AS players,
            (SELECT COALESCE(SUM(crystals), 0) FROM users) AS total_crystals,
            (SELECT COUNT(*) FROM actions) AS total_actions,
            (SELECT COUNT(*) FROM inventory) AS total_purchases,
            (SELECT COUNT(*) FROM users WHERE source = 'web') AS web_users,
            (SELECT COUNT(*) FROM users WHERE source <> 'web') AS telegram_users,
            (SELECT COUNT(*) FROM game_sessions WHERE finished_at > 0) AS games_played
        """)
        row = await cursor.fetchone()
        return dict(row)
    finally:
        await db.close()


async def get_admin_users(query: str = "", limit: int = 50, offset: int = 0):
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    query = (query or "").strip()[:100]
    db = await connect()
    try:
        if query:
            like = f"%{query}%"
            cursor = await db.execute("""SELECT telegram_id, username, first_name,
                crystals, created_at, last_seen_at, source
                FROM users
                WHERE CAST(telegram_id AS TEXT) LIKE ?
                   OR LOWER(COALESCE(username, '')) LIKE LOWER(?)
                   OR LOWER(first_name) LIKE LOWER(?)
                ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (like, like, like, limit, offset))
        else:
            cursor = await db.execute("""SELECT telegram_id, username, first_name,
                crystals, created_at, last_seen_at, source
                FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (limit, offset))
        rows = [dict(row) for row in await cursor.fetchall()]
        # SQLite ILIKE mavjud emas; adapter orqali SQLni moslashtirish quyida bajariladi.
        for row in rows:
            for key in ("created_at", "last_seen_at"):
                value = row.get(key)
                if hasattr(value, "isoformat"):
                    row[key] = value.isoformat()
        return rows
    finally:
        await db.close()


async def start_crystal_game(telegram_id: int):
    db = await connect()
    try:
        await db.execute("BEGIN IMMEDIATE")
        cursor = await db.execute(
            "SELECT last_game_at FROM users WHERE telegram_id = ?", (int(telegram_id),)
        )
        user = await cursor.fetchone()
        if not user:
            await db.rollback()
            return {"status": "not_registered"}
        now = int(time.time())
        last_game = int(user["last_game_at"] or 0)
        remaining = max(0, last_game + GAME_COOLDOWN_SECONDS - now)
        if remaining:
            await db.rollback()
            return {"status": "cooldown", "remaining_seconds": remaining}
        session_id = uuid.uuid4().hex
        await db.execute(
            "INSERT INTO game_sessions (session_id, telegram_id, started_at) VALUES (?, ?, ?)",
            (session_id, int(telegram_id), now),
        )
        await db.execute(
            "UPDATE users SET last_game_at = ? WHERE telegram_id = ?", (now, int(telegram_id))
        )
        await db.commit()
        return {"status": "started", "session_id": session_id,
                "duration_seconds": GAME_DURATION_SECONDS,
                "cooldown_seconds": GAME_COOLDOWN_SECONDS}
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()


async def finish_crystal_game(telegram_id: int, session_id: str, clicks: int):
    db = await connect()
    try:
        await db.execute("BEGIN IMMEDIATE")
        lock_suffix = " FOR UPDATE" if settings.DATABASE_URL else ""
        cursor = await db.execute(
            "SELECT * FROM game_sessions WHERE session_id = ? AND telegram_id = ?" + lock_suffix,
            (str(session_id)[:64], int(telegram_id)),
        )
        game = await cursor.fetchone()
        if not game:
            await db.rollback()
            return {"status": "invalid_session"}
        if int(game["finished_at"] or 0) > 0:
            await db.rollback()
            return {"status": "already_finished"}
        now = int(time.time())
        elapsed = now - int(game["started_at"])
        if elapsed < GAME_DURATION_SECONDS - 2:
            await db.rollback()
            return {"status": "too_early", "remaining_seconds": GAME_DURATION_SECONDS - elapsed}
        if elapsed > 90:
            await db.execute(
                "UPDATE game_sessions SET finished_at = ?, clicks = 0, reward = 0 WHERE session_id = ?",
                (now, str(session_id)),
            )
            await db.commit()
            return {"status": "expired"}
        safe_clicks = max(0, min(int(clicks), GAME_MAX_CLICKS))
        reward = min(GAME_MAX_REWARD, safe_clicks // 2)
        await db.execute(
            "UPDATE game_sessions SET finished_at = ?, clicks = ?, reward = ? WHERE session_id = ?",
            (now, safe_clicks, reward, str(session_id)),
        )
        if reward:
            await db.execute(
                "UPDATE users SET crystals = crystals + ? WHERE telegram_id = ?",
                (reward, int(telegram_id)),
            )
            await db.execute(
                "INSERT INTO actions (telegram_id, action_type, details) VALUES (?, 'game_reward', ?)",
                (int(telegram_id), f"Crystal Rush: +{reward} crystals ({safe_clicks} clicks)"),
            )
            await db.execute(
                "INSERT INTO crystal_transactions (telegram_id, amount, transaction_type, reference) VALUES (?, ?, 'game_reward', ?)",
                (int(telegram_id), reward, str(session_id)),
            )
        cursor = await db.execute("SELECT crystals FROM users WHERE telegram_id = ?", (int(telegram_id),))
        user = await cursor.fetchone()
        await db.commit()
        return {"status": "success", "clicks": safe_clicks, "reward": reward,
                "crystals": int(user["crystals"]), "cooldown_seconds": GAME_COOLDOWN_SECONDS}
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
