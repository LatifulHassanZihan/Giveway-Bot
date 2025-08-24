# bot.py
import asyncio
import json
import logging
import os
import random
import string
from datetime import datetime
from typing import Dict, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class GiveawayBot:
    def __init__(self, token: str, admin_id: int, data_file: str = "bot_data.json"):
        self.token = token
        self.admin_id = admin_id
        self.data_file = data_file
        self.codes: Dict[str, bool] = {}
        self.redeemed_codes: Dict[str, dict] = {}
        self.users: set[int] = set()
        self.banned_users: set[int] = set()
        self.prizes: Dict[str, str] = {}
        self.load_data()

    # ===== Persistence =====
    def load_data(self):
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
            self.codes = data.get("codes", {})
            self.redeemed_codes = data.get("redeemed_codes", {})
            self.users = set(data.get("users", []))
            self.banned_users = set(data.get("banned_users", []))
            self.prizes = data.get("prizes", {})
        except FileNotFoundError:
            self.codes = {}
            self.redeemed_codes = {}
            self.users = set()
            self.banned_users = set()
            self.prizes = {}
            self.save_data()

    def save_data(self):
        data = {
            "codes": self.codes,
            "redeemed_codes": self.redeemed_codes,
            "users": list(self.users),
            "banned_users": list(self.banned_users),
            "prizes": self.prizes,
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)

    # ===== Shared helpers =====
    async def is_admin(self, user_id: int) -> bool:
        return user_id == self.admin_id

    # ===== User command implementations (called from main.py) =====
    async def start_command_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user:
            return
        user_id = user.id

        if user_id in self.banned_users:
            if update.message:
                await update.message.reply_text("❌ You are banned from using this bot.")
            return

        self.users.add(user_id)
        self.save_data()

        keyboard = [
            [InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem_help")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
            [InlineKeyboardButton("ℹ️ Bot Info", callback_data="info")],
            [InlineKeyboardButton("❓ Help", callback_data="help")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = f"""
🎉 **Welcome to ZIHAN GIVEAWAY Bot!** 🇵🇸

Hello {user.first_name}! 👋

🎁 Ready to claim some amazing prizes? Use your redemption codes here!
🏆 Compete with others and see who's winning!
📱 Easy to use - just follow the commands!

Choose an option below to get started:
        """

        if update.message:
            await update.message.reply_text(
                welcome_text, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def redeem_command_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or not update.message:
            return
        user_id = user.id

        if user_id in self.banned_users:
            await update.message.reply_text("❌ You are banned from using this bot.")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a code!\n\n"
                "**Usage:** `/redeem <code>`\n"
                "**Example:** `/redeem GIFT123`",
                parse_mode="Markdown",
            )
            return

        code = context.args[0].upper()

        if code not in self.codes:
            await update.message.reply_text("❌ **Invalid code!** The code you entered doesn't exist.")
            return

        if code in self.redeemed_codes:
            redeemer_info = self.redeemed_codes[code]
            await update.message.reply_text(
                f"❌ **Code already redeemed!**\n\n"
                f"👤 **Redeemed by:** {redeemer_info['username']}\n"
                f"🕐 **Date:** {redeemer_info['date']}\n"
                f"🆔 **User ID:** {redeemer_info['user_id']}"
            )
            return

        prize = self.prizes.get(code, "🎁 Mystery Prize")
        redemption_info = {
            "user_id": user_id,
            "username": f"@{user.username}" if user.username else user.first_name,
            "first_name": user.first_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prize": prize,
        }

        self.redeemed_codes[code] = redemption_info
        self.save_data()

        await update.message.reply_text(
            f"🎉 **Congratulations!** 🎉\n\n"
            f"✅ **Code:** `{code}`\n"
            f"🎁 **Prize:** {prize}\n"
            f"👤 **Winner:** {user.first_name}\n"
            f"🕐 **Redeemed:** {redemption_info['date']}\n\n"
            f"**Take a Screenshot and send to @alwayszihan and wait a few**\n"
            f"🎊 Enjoy your prize!",
            parse_mode="Markdown",
        )

        try:
            admin_message = (
                f"🔔 **New Code Redemption!**\n\n"
                f"👤 **User:** {redemption_info['username']}\n"
                f"🆔 **ID:** {user_id}\n"
                f"📛 **Name:** {user.first_name}\n"
                f"✅ **Code:** `{code}`\n"
                f"🎁 **Prize:** {prize}\n"
                f"🕐 **Time:** {redemption_info['date']}"
            )
            await context.bot.send_message(
                chat_id=self.admin_id, text=admin_message, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

    async def info_command_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        info_text = """
🤖 **ZIHAN GIVEAWAY BOT** 🇵🇸

👨‍💻 **Developer:** Latiful Hassan Zihan
📱 **Telegram:** @alwayzihan  
🌍 **Location:** Bangladesh 🇧🇩
💻 **Language:** Python

📋 **Available Commands:**

👤 **User Commands**
/start - Shows the main welcome menu
/redeem <code> - Claim a prize with your code
/leaderboard - See the top winners
/help - Shows this help message

👑 **Admin Commands**
/stats - View bot statistics
/listcodes - List all codes and prizes  
/addcode <code> - Add a new code
/addprize <code> <prize> - Set prize for a code
/delcode <code> - Delete a code
/gencode <num> <prefix> - Generate codes
/broadcast <msg> - Send a message to all users
/ban <user_id> - Ban a user
/unban <user_id> - Unban a user
/resetgiveaway - Clear the winner list for a new giveaway
/stopbot - Stop the bot

🎁 **Happy claiming!**
        """
        await update.message.reply_text(info_text, parse_mode="Markdown")

    async def help_command_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        help_text = """
❓ **HELP & INSTRUCTIONS**

🎁 **How to redeem codes:**
1. Get a code from @alwayszihan
2. Use `/redeem <your_code>`
3. Enjoy your prize! 🎉

📝 **Examples:**
• `/redeem GIFT123` - Redeem code GIFT123
• `/leaderboard` - See top winners
• `/info` - Bot information

⚠️ **Important Notes:**
• Each code can only be used once
• Codes are case-insensitive
• Contact @alwayszihan for new codes

🆘 **Need help?** Contact @alwayszihan
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def leaderboard_command_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not self.redeemed_codes:
            await update.message.reply_text("🏆 **Leaderboard is empty!**\n\nNo codes have been redeemed yet.")
            return

        user_stats: Dict[int, dict] = {}
        for _, info in self.redeemed_codes.items():
            user_id = info["user_id"]
            username = info["username"]
            if user_id not in user_stats:
                user_stats[user_id] = {"username": username, "count": 0, "prizes": []}
            user_stats[user_id]["count"] += 1
            user_stats[user_id]["prizes"].append(info["prize"])

        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["count"], reverse=True)

        leaderboard_text = "🏆 **LEADERBOARD** 🏆\n\n"
        emojis = ["🥇", "🥈", "🥉"] + ["🏅"] * 7

        for i, (_, stats) in enumerate(sorted_users[:10]):
            emoji = emojis[i] if i < len(emojis) else "🎯"
            leaderboard_text += f"{emoji} **{stats['username']}** - {stats['count']} codes\n"

        await update.message.reply_text(leaderboard_text, parse_mode="Markdown")

    # ===== Admin-only commands (exposed directly to handlers in main.py) =====
    async def stats_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        total_codes = len(self.codes)
        redeemed_count = len(self.redeemed_codes)
        available_count = total_codes - redeemed_count
        total_users = len(self.users)
        banned_users_count = len(self.banned_users)
        redemption_rate = f"{(redeemed_count / total_codes * 100):.1f}%" if total_codes > 0 else "0.0%"

        stats_text = f"""
📊 **BOT STATISTICS**

👥 **Users:** {total_users}
🚫 **Banned Users:** {banned_users_count}
🎫 **Total Codes:** {total_codes}
✅ **Redeemed:** {redeemed_count}
🎁 **Available:** {available_count}
📈 **Redemption Rate:** {redemption_rate}

🕐 **Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        await update.message.reply_text(stats_text, parse_mode="Markdown")

    async def listcodes_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        if not self.codes:
            await update.message.reply_text("📋 **No codes available.**")
            return

        codes_text = "📋 **ALL CODES:**\n\n"
        for code in self.codes:
            status = "✅ Redeemed" if code in self.redeemed_codes else "🎁 Available"
            prize = self.prizes.get(code, "🎁 No prize set")
            codes_text += f"**{code}** - {prize} ({status})\n"

        await update.message.reply_text(codes_text, parse_mode="Markdown")

    async def addcode_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a code!\n\n"
                "**Usage:** `/addcode <code>`\n"
                "**Example:** `/addcode GIFT123`",
                parse_mode="Markdown",
            )
            return

        code = context.args[0].upper()

        if code in self.codes:
            await update.message.reply_text(f"❌ Code `{code}` already exists!")
            return

        self.codes[code] = True
        self.save_data()

        await update.message.reply_text(
            f"✅ **Code added successfully!**\n\n"
            f"📝 **Code:** `{code}`\n"
            f"💡 **Tip:** Use `/addprize {code} <prize>` to set a prize for this code.",
            parse_mode="Markdown",
        )

    async def addprize_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Please provide both code and prize!\n\n"
                "**Usage:** `/addprize <code> <prize>`\n"
                "**Example:** `/addprize GIFT123 $50 Amazon Gift Card`",
                parse_mode="Markdown",
            )
            return

        code = context.args[0].upper()
        prize = " ".join(context.args[1:])

        if code not in self.codes:
            await update.message.reply_text(f"❌ Code `{code}` doesn't exist! Use `/addcode {code}` first.")
            return

        self.prizes[code] = prize
        self.save_data()

        await update.message.reply_text(
            f"✅ **Prize set successfully!**\n\n"
            f"📝 **Code:** `{code}`\n"
            f"🎁 **Prize:** {prize}",
            parse_mode="Markdown",
        )

    async def delcode_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a code to delete!\n\n"
                "**Usage:** `/delcode <code>`\n"
                "**Example:** `/delcode GIFT123`",
                parse_mode="Markdown",
            )
            return

        code = context.args[0].upper()

        if code not in self.codes:
            await update.message.reply_text(f"❌ Code `{code}` doesn't exist!")
            return

        # Remove code and any related data
        del self.codes[code]
        if code in self.prizes:
            del self.prizes[code]
        if code in self.redeemed_codes:
            del self.redeemed_codes[code]

        self.save_data()

        await update.message.reply_text(
            f"✅ **Code deleted successfully!**\n\n"
            f"🗑️ **Deleted:** `{code}`",
            parse_mode="Markdown",
        )

    async def gencode_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Please provide number and prefix!\n\n"
                "**Usage:** `/gencode <number> <prefix>`\n"
                "**Example:** `/gencode 5 GIFT`",
                parse_mode="Markdown",
            )
            return

        try:
            num = int(context.args[0])
            prefix = context.args[1].upper()
        except ValueError:
            await update.message.reply_text("❌ Number must be a valid integer!")
            return

        if num <= 0:
            await update.message.reply_text("❌ Number must be greater than zero!")
            return

        if num > 50:
            await update.message.reply_text("❌ Maximum 50 codes can be generated at once!")
            return

        generated_codes: List[str] = []
        for _ in range(num):
            suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"{prefix}{suffix}"

            while code in self.codes:
                suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                code = f"{prefix}{suffix}"

            self.codes[code] = True
            generated_codes.append(code)

        self.save_data()

        codes_text = "✅ **Generated Codes:**\n\n"
        for code in generated_codes:
            codes_text += f"`{code}`\n"

        codes_text += f"\n📊 **Total:** {len(generated_codes)} codes generated"

        await update.message.reply_text(codes_text, parse_mode="Markdown")

    async def broadcast_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a message to broadcast!\n\n"
                "**Usage:** `/broadcast <message>`\n"
                "**Example:** `/broadcast New codes available!`",
                parse_mode="Markdown",
            )
            return

        message = " ".join(context.args)
        broadcast_message = f"📢 **BROADCAST MESSAGE**\n\n{message}\n\n— ZIHAN GIVEAWAY Bot"

        success_count = 0
        fail_count = 0

        for user_id in list(self.users):
            if user_id in self.banned_users:
                continue
            try:
                await context.bot.send_message(
                    chat_id=user_id, text=broadcast_message, parse_mode="Markdown"
                )
                success_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                fail_count += 1
                logger.error(f"Failed to send broadcast to {user_id}: {e}")

        await update.message.reply_text(
            f"📊 **Broadcast Results:**\n\n"
            f"✅ **Sent:** {success_count}\n"
            f"❌ **Failed:** {fail_count}\n"
            f"📱 **Total Users:** {len(self.users)}",
            parse_mode="Markdown",
        )

    async def ban_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID to ban!\n\n"
                "**Usage:** `/ban <user_id>`\n"
                "**Example:** `/ban 123456789`",
                parse_mode="Markdown",
            )
            return

        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ User ID must be a number!")
            return

        if user_id == self.admin_id:
            await update.message.reply_text("❌ You cannot ban yourself!")
            return

        self.banned_users.add(user_id)
        self.save_data()

        await update.message.reply_text(
            f"✅ **User banned successfully!**\n\n"
            f"🚫 **Banned User ID:** {user_id}",
            parse_mode="Markdown",
        )

    async def unban_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID to unban!\n\n"
                "**Usage:** `/unban <user_id>`\n"
                "**Example:** `/unban 123456789`",
                parse_mode="Markdown",
            )
            return

        try:
            user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ User ID must be a number!")
            return

        if user_id not in self.banned_users:
            await update.message.reply_text(f"❌ User {user_id} is not banned!")
            return

        self.banned_users.discard(user_id)
        self.save_data()

        await update.message.reply_text(
            f"✅ **User unbanned successfully!**\n\n"
            f"✅ **Unbanned User ID:** {user_id}",
            parse_mode="Markdown",
        )

    async def resetgiveaway_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        self.redeemed_codes.clear()
        self.save_data()

        await update.message.reply_text(
            "✅ **Giveaway reset successfully!**\n\n"
            "🔄 All codes are now available for redemption again.\n"
            "🏆 Leaderboard has been cleared.\n\n"
            "🎉 Ready for a new giveaway!",
            parse_mode="Markdown",
        )

    async def stopbot_command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return

        await update.message.reply_text("🛑 **Bot is shutting down...**")
        logger.info("Bot shutdown initiated by admin")
        os._exit(0)
 
