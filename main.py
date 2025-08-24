# main.py
import logging
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

from bot import GiveawayBot  # admin features and shared state

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ===== User Commands (in main.py) =====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot_data["gbot"].start_command_user(update, context)

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot_data["gbot"].redeem_command_user(update, context)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot_data["gbot"].info_command_user(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot_data["gbot"].help_command_user(update, context)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot_data["gbot"].leaderboard_command_user(update, context)


def main():
    # Replace with your values
    BOT_TOKEN = "8490064023:AAFVXBx26FdJxlI-aJWPxdmOvMpWFw3qXxU"
    ADMIN_ID = 6446086262

    if not BOT_TOKEN or "REPLACE_WITH" in BOT_TOKEN:
        print("❌ Please set your bot token in main.py")
        return

    # Create shared admin bot/state holder
    gbot = GiveawayBot(token=BOT_TOKEN, admin_id=ADMIN_ID)

    # Build app
    application = Application.builder().token(BOT_TOKEN).build()

    # Make GiveawayBot accessible to all handlers
    application.bot_data["gbot"] = gbot

    # User command handlers (main.py)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("redeem", redeem_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))

    # Admin command handlers (delegated to bot.py implementation)
    application.add_handler(CommandHandler("stats", gbot.stats_command_admin))
    application.add_handler(CommandHandler("listcodes", gbot.listcodes_command_admin))
    application.add_handler(CommandHandler("addcode", gbot.addcode_command_admin))
    application.add_handler(CommandHandler("addprize", gbot.addprize_command_admin))
    application.add_handler(CommandHandler("delcode", gbot.delcode_command_admin))
    application.add_handler(CommandHandler("gencode", gbot.gencode_command_admin))
    application.add_handler(CommandHandler("broadcast", gbot.broadcast_command_admin))
    application.add_handler(CommandHandler("ban", gbot.ban_command_admin))
    application.add_handler(CommandHandler("unban", gbot.unban_command_admin))
    application.add_handler(CommandHandler("resetgiveaway", gbot.resetgiveaway_command_admin))
    application.add_handler(CommandHandler("stopbot", gbot.stopbot_command_admin))

    print("🤖 ZIHAN GIVEAWAY Bot is starting...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    application.run_polling()


if __name__ == "__main__":
    main()
