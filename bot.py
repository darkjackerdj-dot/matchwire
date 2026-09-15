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
    raise ValueError("BOT_TOKEN not found in .env file")

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
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    conn = sqlite3.connect(DB)

    conn.execute("""
        INSERT INTO subscribers
        (chat_id, active)
        VALUES (?, 1)
        ON CONFLICT(chat_id)
        DO UPDATE SET active = 1
    """, (chat_id,))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "<b>🟢 MATCHWIRE UPDATES STARTED!</b>\n\n"
        "⚽ You will receive genuine football news automatically.\n\n"
        "Use /stop to stop updates.",
        parse_mode="HTML"
    )

    print(f"🟢 Subscriber activated: {chat_id}")


# ============================================================
# STOP
# ============================================================

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    conn = sqlite3.connect(DB)

    conn.execute(
        "UPDATE subscribers SET active = 0 WHERE chat_id = ?",
        (chat_id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "<b>🔴 MATCHWIRE UPDATES STOPPED.</b>\n\n"
        "Use /start to activate updates again.",
        parse_mode="HTML"
    )

    print(f"🔴 Subscriber deactivated: {chat_id}")


# ============================================================
# NEWS HASH
# ============================================================

def get_news_hash(article):

    return hashlib.sha256(
        article["link"].encode()
    ).hexdigest()


# ============================================================
# DUPLICATE CHECK
# ============================================================

def already_sent(news_hash):

    conn = sqlite3.connect(DB)

    result = conn.execute(
        "SELECT 1 FROM sent_news WHERE news_hash = ?",
        (news_hash,)
    ).fetchone()

    conn.close()

    return result is not None


# ============================================================
# SAVE SENT NEWS
# ============================================================

def save_sent_news(article):

    news_hash = get_news_hash(article)

    conn = sqlite3.connect(DB)

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
# ACTIVE SUBSCRIBERS
# ============================================================

def get_active_subscribers():

    conn = sqlite3.connect(DB)

    subscribers = conn.execute(
        "SELECT chat_id FROM subscribers WHERE active = 1"
    ).fetchall()

    conn.close()

    return subscribers


# ============================================================
# BUILD TELEGRAM MESSAGE
# ============================================================

def build_message(article):

    title = html.escape(article["title"])
    source = html.escape(article["source"])

    if article.get("rumour"):

        message = (
            "<b>⚠️ MATCHWIRE — RUMOUR</b>\n\n"
            f"📰 <b>{title}</b>\n\n"
            f"🗞 Source: {source}\n\n"
            "⚠️ This report contains speculation or transfer-rumour language."
        )

    else:

        message = (
            "<b>⚽ MATCHWIRE FOOTBALL UPDATE</b>\n\n"
            f"📰 <b>{title}</b>\n\n"
            f"🗞 Source: {source}"
        )

    keyboard = [[
        InlineKeyboardButton(
            "🔗 READ FULL STORY",
            url=article["link"]
        )
    ]]

    return message, InlineKeyboardMarkup(keyboard)


# ============================================================
# SEND ARTICLE
# ============================================================

async def send_article(
    context: ContextTypes.DEFAULT_TYPE,
    article,
    subscribers,
    save_to_database=True
):

    message, reply_markup = build_message(article)

    sent_to_someone = False

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
                f"📤 SENT → {chat_id}: "
                f"{article['title']}"
            )

        except Exception as error:

            print(
                f"❌ TELEGRAM SEND ERROR → {chat_id}: "
                f"{error}"
            )

    if sent_to_someone and save_to_database:

        if save_sent_news(article):

            print(
                f"💾 Saved to database: "
                f"{article['title']}"
            )


# ============================================================
# AUTOMATIC NEWS CHECK
# ============================================================

async def check_news(context: ContextTypes.DEFAULT_TYPE):

    print("")
    print("===================================")
    print("🔎 AUTOMATIC NEWS CHECK")
    print("===================================")

    try:

        articles = collect_news()

    except Exception as error:

        print(
            f"❌ Collector error: {error}"
        )

        return

    if not articles:

        print(
            "ℹ️ No important articles found."
        )

        return

    subscribers = get_active_subscribers()

    if not subscribers:

        print(
            "ℹ️ No active Telegram subscribers."
        )

        return

    total_articles = len(articles)

    duplicate_count = 0
    new_articles = 0
    sent_count = 0

    print(
        f"📰 Articles received: "
        f"{total_articles}"
    )

    print(
        f"👤 Active subscribers: "
        f"{len(subscribers)}"
    )

    print("")

    for article in articles:

        news_hash = get_news_hash(article)

        # --------------------------------------------
        # DUPLICATE PROTECTION
        # --------------------------------------------

        if already_sent(news_hash):

            duplicate_count += 1

            print(
                f"⏭️ Already sent: "
                f"{article['title']}"
            )

            continue

        # --------------------------------------------
        # NEW ARTICLE
        # --------------------------------------------

        new_articles += 1

        print(
            f"🆕 NEW ARTICLE: "
            f"{article['title']}"
        )

        message, reply_markup = build_message(article)

        sent_to_someone = False

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

                sent_count += 1

                print(
                    f"📤 Sent to {chat_id}: "
                    f"{article['title']}"
                )

            except Exception as error:

                print(
                    f"❌ Failed to send to "
                    f"{chat_id}: {error}"
                )

        # --------------------------------------------
        # SAVE ONLY AFTER SUCCESSFUL SEND
        # --------------------------------------------

        if sent_to_someone:

            if save_sent_news(article):

                print(
                    f"💾 Saved to database: "
                    f"{article['title']}"
                )

    print("")

    print("===================================")
    print("📊 AUTOMATIC CHECK SUMMARY")
    print("===================================")

    print(
        f"📰 Articles checked: "
        f"{total_articles}"
    )

    print(
        f"⏭️ Already sent: "
        f"{duplicate_count}"
    )

    print(
        f"🆕 New articles: "
        f"{new_articles}"
    )

    print(
        f"📤 Telegram messages sent: "
        f"{sent_count}"
    )

    print("===================================")
    print("")


# ============================================================
# TEST NEWS
# ============================================================

async def testnews(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    print("")
    print("🧪 TEST NEWS REQUESTED")

    try:

        articles = collect_news()

    except Exception as error:

        print(
            f"❌ Test collector error: "
            f"{error}"
        )

        await update.message.reply_text(
            "❌ Could not collect football news right now."
        )

        return

    if not articles:

        await update.message.reply_text(
            "❌ No football articles found."
        )

        return

    article = articles[0]

    message, reply_markup = build_message(article)

    try:

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

        print(
            f"🧪 Test sent: "
            f"{article['title']}"
        )

    except Exception as error:

        print(
            f"❌ Test send failed: "
            f"{error}"
        )


# ============================================================
# FORCE CHECK TEST
# ============================================================

async def forcecheck(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    print("")
    print("🧪 FORCE CHECK REQUESTED")

    subscribers = get_active_subscribers()

    if not subscribers:

        await update.message.reply_text(
            "❌ No active subscribers.\n"
            "Send /start first."
        )

        return

    try:

        articles = collect_news()

    except Exception as error:

        print(
            f"❌ Force collector error: "
            f"{error}"
        )

        await update.message.reply_text(
            "❌ News collector failed."
        )

        return

    if not articles:

        await update.message.reply_text(
            "❌ No important football news found."
        )

        return

    # Take the highest-ranked current article
    article = articles[0]

    print(
        f"🧪 FORCE SEND: "
        f"{article['title']}"
    )

    # IMPORTANT:
    # This sends through the same Telegram sending path,
    # but DOES NOT modify sent_news database.
    await send_article(
        context,
        article,
        [(chat_id,)],
        save_to_database=False
    )

    await update.message.reply_text(
        "🧪 Force-check completed.\n\n"
        "This test does NOT modify your sent-news history."
    )


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

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("stop", stop)
    )

    app.add_handler(
        CommandHandler("testnews", testnews)
    )

    app.add_handler(
        CommandHandler("forcecheck", forcecheck)
    )

    # Automatic news check
    app.job_queue.run_repeating(
        check_news,
        interval=300,
        first=10
    )

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
    print("🧪 /testnews: ENABLED")
    print("🧪 /forcecheck: ENABLED")
    print("===================================")
    print("")

    app.run_polling()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
