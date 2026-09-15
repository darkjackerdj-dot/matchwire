import os
import sqlite3
import hashlib
import html

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from telegram.request import HTTPXRequest

from collector import collect_news


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError(
        "BOT_TOKEN not found in .env file"
    )

DB = "football.db"


# ============================================================
# DATABASE
# ============================================================

def init_db():

    conn = sqlite3.connect(DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY,
            active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sent_news (
            news_hash TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            source TEXT
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# START COMMAND
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    conn = sqlite3.connect(DB)

    conn.execute(
        """
        INSERT INTO subscribers
        (chat_id, active)
        VALUES (?, 1)

        ON CONFLICT(chat_id)
        DO UPDATE SET active = 1
        """,
        (chat_id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "<b>🟢 MATCHWIRE UPDATES STARTED!</b>\n\n"
        "⚽ You will receive genuine football news "
        "automatically.\n\n"
        "Use /stop to stop updates.",
        parse_mode="HTML"
    )


# ============================================================
# STOP COMMAND
# ============================================================

async def stop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    conn = sqlite3.connect(DB)

    conn.execute(
        """
        UPDATE subscribers
        SET active = 0
        WHERE chat_id = ?
        """,
        (chat_id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "<b>🔴 MATCHWIRE UPDATES STOPPED.</b>\n\n"
        "Use /start to activate updates again.",
        parse_mode="HTML"
    )


# ============================================================
# CHECK IF NEWS WAS ALREADY SENT
# ============================================================

def already_sent(news_hash):

    conn = sqlite3.connect(DB)

    result = conn.execute(
        """
        SELECT 1
        FROM sent_news
        WHERE news_hash = ?
        """,
        (news_hash,)
    ).fetchone()

    conn.close()

    return result is not None


# ============================================================
# SAVE SENT NEWS
# ============================================================

def save_sent_news(article):

    conn = sqlite3.connect(DB)

    news_hash = hashlib.sha256(
        article["link"].encode()
    ).hexdigest()

    try:

        conn.execute(
            """
            INSERT INTO sent_news
            (news_hash, title, link, source)
            VALUES (?, ?, ?, ?)
            """,
            (
                news_hash,
                article["title"],
                article["link"],
                article["source"]
            )
        )

        conn.commit()

        saved = True

    except sqlite3.IntegrityError:

        saved = False

    conn.close()

    return saved


# ============================================================
# CREATE TELEGRAM MESSAGE
# ============================================================

def build_message(article):

    title = html.escape(
        article["title"]
    )

    source = html.escape(
        article["source"]
    )

    if article["rumour"]:

        message = (
            "<b>⚠️ MATCHWIRE — RUMOUR</b>\n\n"
            f"📰 <b>{title}</b>\n\n"
            f"🗞 Source: {source}\n\n"
            "⚠️ This report contains "
            "speculation or transfer-rumour language."
        )

    else:

        message = (
            "<b>⚽ MATCHWIRE FOOTBALL UPDATE</b>\n\n"
            f"📰 <b>{title}</b>\n\n"
            f"🗞 Source: {source}"
        )

    # --------------------------------------------------------
    # READ FULL STORY BUTTON
    # --------------------------------------------------------

    keyboard = [
        [
            InlineKeyboardButton(
                "🔗 READ FULL STORY",
                url=article["link"]
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    return message, reply_markup


# ============================================================
# CHECK NEWS
# ============================================================

async def check_news(
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "\n🔎 Checking for new football news..."
    )

    try:

        articles = collect_news()

    except Exception as error:

        print(
            f"❌ Collector error: {error}"
        )

        return


    if not articles:

        print(
            "ℹ️ No articles found."
        )

        return


    # --------------------------------------------------------
    # GET ACTIVE SUBSCRIBERS
    # --------------------------------------------------------

    conn = sqlite3.connect(DB)

    subscribers = conn.execute(
        """
        SELECT chat_id
        FROM subscribers
        WHERE active = 1
        """
    ).fetchall()

    conn.close()


    if not subscribers:

        print(
            "ℹ️ No active Telegram subscribers."
        )

        return


    # --------------------------------------------------------
    # PROCESS ARTICLES
    # --------------------------------------------------------

    for article in articles:

        news_hash = hashlib.sha256(
            article["link"].encode()
        ).hexdigest()


        # Already sent?
        if already_sent(news_hash):

            continue


        # Build message + button
        message, reply_markup = build_message(
            article
        )


        sent_to_someone = False


        # ----------------------------------------------------
        # SEND TO ACTIVE USERS
        # ----------------------------------------------------

        for (chat_id,) in subscribers:

            try:

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )

                sent_to_someone = True

                print(
                    f"📤 Sent: "
                    f"{article['title']}"
                )

            except Exception as error:

                print(
                    f"❌ Failed to send to "
                    f"{chat_id}: {error}"
                )


        # ----------------------------------------------------
        # SAVE AFTER SUCCESSFUL SEND
        # ----------------------------------------------------

        if sent_to_someone:

            save_sent_news(article)


# ============================================================
# MAIN
# ============================================================

def main():

    init_db()


    request = HTTPXRequest(
        connect_timeout=60,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=60
    )


    app = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .build()
    )


    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "stop",
            stop
        )
    )


    # --------------------------------------------------------
    # NEWS CHECKER
    # --------------------------------------------------------

    app.job_queue.run_repeating(
        check_news,
        interval=300,
        first=10
    )


    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    print("")
    print("===================================")
    print("       MATCHWIRE TELEGRAM BOT")
    print("===================================")
    print("🤖 Bot: ONLINE")
    print("⚽ News checker: EVERY 5 MINUTES")
    print("📰 Sources: BBC + ESPN")
    print("🛡️ Filters: ENABLED")
    print("🔁 Duplicate protection: ENABLED")
    print("🔗 READ FULL STORY BUTTON: ENABLED")
    print("===================================")
    print("")


    app.run_polling()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
