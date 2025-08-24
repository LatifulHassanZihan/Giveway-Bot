import asyncio
import json
import logging
import os
import random
import string
from datetime import datetime
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GiveawayBot:
    def __init__(self, token: str, admin_id: int):
        self.token = token
        self.admin_id = admin_id
        self.data_file = "bot_data.json"
        self.load_data()
        
    def load_data(self):
        """Load bot data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            self.codes = data.get('codes', {})
            self.redeemed_codes = data.get('redeemed_codes', {})
            self.users = data.get('users', set())
            self.banned_users = data.get('banned_users', set())
            self.prizes = data.get('prizes', {})
        except FileNotFoundError:
            self.codes = {}
            self.redeemed_codes = {}
            self.users = set()
            self.banned_users = set()
            self.prizes = {}
            self.save_data()
    
    def save_data(self):
        """Save bot data to JSON file"""
        data = {
            'codes': self.codes,
            'redeemed_codes': self.redeemed_codes,
            'users': list(self.users),
            'banned_users': list(self.banned_users),
            'prizes': self.prizes
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        if user_id in self.banned_users:
            await update.message.reply_text("❌ You are banned from using this bot.")
            return
            
        self.users.add(user_id)
        self.save_data()
        
        keyboard = [
            [InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem_help")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
            [InlineKeyboardButton("ℹ️ Bot Info", callback_data="info")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
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
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def redeem_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /redeem command"""
        user = update.effective_user
        user_id = user.id
        
        if user_id in self.banned_users:
            await update.message.reply_text("❌ You are banned from using this bot.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a code!\n\n"
                "**Usage:** `/redeem <code>`\n"
                "**Example:** `/redeem GIFT123`",
                parse_mode='Markdown'
            )
            return
        
        code = context.args[0].upper()
        
        # Check if code exists
        if code not in self.codes:
            await update.message.reply_text("❌ **Invalid code!** The code you entered doesn't exist.")
            return
        
        # Check if code is already redeemed
        if code in self.redeemed_codes:
            redeemer_info = self.redeemed_codes[code]
            await update.message.reply_text(
                f"❌ **Code already redeemed!**\n\n"
                f"👤 **Redeemed by:** {redeemer_info['username']}\n"
                f"🕐 **Date:** {redeemer_info['date']}\n"
                f"🆔 **User ID:** {redeemer_info['user_id']}"
            )
            return
        
        # Redeem the code
        prize = self.prizes.get(code, "🎁 Mystery Prize")
        redemption_info = {
            'user_id': user_id,
            'username': f"@{user.username}" if user.username else user.first_name,
            'first_name': user.first_name,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'prize': prize
        }
        
        self.redeemed_codes[code] = redemption_info
        self.save_data()
        
        # Send success message to user
        await update.message.reply_text(
            f"🎉 **Congratulations!** 🎉\n\n"
            f"✅ **Code:** `{code}`\n"
            f"🎁 **Prize:** {prize}\n"
            f"👤 **Winner:** {user.first_name}\n"
            f"🕐 **Redeemed:** {redemption_info['date']}\n\n"
            f"**Take a Screenshot and send to @alwayszihan and wait a few**\n"
            f"🎊 Enjoy your prize!",
            parse_mode='Markdown'
        )
        
        # Notify admin
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
                chat_id=self.admin_id,
                text=admin_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command"""
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
        await update.message.reply_text(info_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
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
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /leaderboard command"""
        if not self.redeemed_codes:
            await update.message.reply_text("🏆 **Leaderboard is empty!**\n\nNo codes have been redeemed yet.")
            return
        
        # Count redemptions per user
        user_stats = {}
        for code, info in self.redeemed_codes.items():
            user_id = info['user_id']
            username = info['username']
            if user_id not in user_stats:
                user_stats[user_id] = {'username': username, 'count': 0, 'prizes': []}
            user_stats[user_id]['count'] += 1
            user_stats[user_id]['prizes'].append(info['prize'])
        
        # Sort by count
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        leaderboard_text = "🏆 **LEADERBOARD** 🏆\n\n"
        emojis = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        
        for i, (user_id, stats) in enumerate(sorted_users[:10]):
            emoji = emojis[i] if i < len(emojis) else "🎯"
            leaderboard_text += f"{emoji} **{stats['username']}** - {stats['count']} codes\n"
        
        await update.message.reply_text(leaderboard_text, parse_mode='Markdown')
    
    # Admin Commands
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == self.admin_id
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        total_codes = len(self.codes)
        redeemed_count = len(self.redeemed_codes)
        available_count = total_codes - redeemed_count
        total_users = len(self.users)
        banned_users_count = len(self.banned_users)
        
        stats_text = f"""
📊 **BOT STATISTICS**

👥 **Users:** {total_users}
🚫 **Banned Users:** {banned_users_count}
🎫 **Total Codes:** {total_codes}
✅ **Redeemed:** {redeemed_count}
🎁 **Available:** {available_count}
📈 **Redemption Rate:** {(redeemed_count/total_codes*100):.1f}% (if total_codes > 0)

🕐 **Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def listcodes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /listcodes command (Admin only)"""
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
        
        await update.message.reply_text(codes_text, parse_mode='Markdown')
    
    async def addcode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addcode command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a code!\n\n"
                "**Usage:** `/addcode <code>`\n"
                "**Example:** `/addcode GIFT123`",
                parse_mode='Markdown'
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
            parse_mode='Markdown'
        )
    
    async def addprize_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addprize command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Please provide both code and prize!\n\n"
                "**Usage:** `/addprize <code> <prize>`\n"
                "**Example:** `/addprize GIFT123 $50 Amazon Gift Card`",
                parse_mode='Markdown'
            )
            return
        
        code = context.args[0].upper()
        prize = ' '.join(context.args[1:])
        
        if code not in self.codes:
            await update.message.reply_text(f"❌ Code `{code}` doesn't exist! Use `/addcode {code}` first.")
            return
        
        self.prizes[code] = prize
        self.save_data()
        
        await update.message.reply_text(
            f"✅ **Prize set successfully!**\n\n"
            f"📝 **Code:** `{code}`\n"
            f"🎁 **Prize:** {prize}",
            parse_mode='Markdown'
        )
    
    async def delcode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /delcode command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a code to delete!\n\n"
                "**Usage:** `/delcode <code>`\n"
                "**Example:** `/delcode GIFT123`",
                parse_mode='Markdown'
            )
            return
        
        code = context.args[0].upper()
        
        if code not in self.codes:
            await update.message.reply_text(f"❌ Code `{code}` doesn't exist!")
            return
        
        # Remove code and its prize
        del self.codes[code]
        if code in self.prizes:
            del self.prizes[code]
        if code in self.redeemed_codes:
            del self.redeemed_codes[code]
        
        self.save_data()
        
        await update.message.reply_text(
            f"✅ **Code deleted successfully!**\n\n"
            f"🗑️ **Deleted:** `{code}`",
            parse_mode='Markdown'
        )
    
    
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
      async def gencode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gencode command (Admin only)"""
    if not await self.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ This command is for admins only.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Please provide number and prefix!\n\n"
            "**Usage:** `/gencode <number> <prefix>`\n"
            "**Example:** `/gencode 5 GIFT`",
            parse_mode='Markdown'
        )
        return

    # ✅ Properly indented try/except
    try:
        num = int(context.args[0])
        prefix = context.args[1].upper()
    except ValueError:
        await update.message.reply_text("❌ Number must be a valid integer!")
        return

    if num > 50:
        await update.message.reply_text("❌ Maximum 50 codes can be generated at once!")
        return
    
    generated_codes = []
    for _ in range(num):
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"{prefix}{suffix}"
        
        # Ensure code is unique
        while code in self.codes:
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"{prefix}{suffix}"
        
        self.codes[code] = True
        generated_codes.append(code)
    
    self.save_data()
    
    codes_text = "✅ **Generated Codes:**\n\n"
    for code in generated_codes:
        codes_text += f"`{code}`\n"
    
    codes_text += f"\n📊 **Total:** {len(generated_codes)} codes generated"
    
    await update.message.reply_text(codes_text, parse_mode='Markdown')


async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command (Admin only)"""
    if not await self.is_admin(update.effective_user.id):
        await update.message.reply_text("❌ This command is for admins only.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a message to broadcast!\n\n"
            "**Usage:** `/broadcast <message>`\n"
            "**Example:** `/broadcast New codes available!`",
            parse_mode='Markdown'
        )
        retu
        rn
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a message to broadcast!\n\n"
                "**Usage:** `/broadcast <message>`\n"
                "**Example:** `/broadcast New codes available!`",
                parse_mode='Markdown'
            )
            return
        
        message = ' '.join(context.args)
        broadcast_message = f"📢 **BROADCAST MESSAGE**\n\n{message}\n\n— ZIHAN GIVEAWAY Bot"
        
        success_count = 0
        fail_count = 0
        
        for user_id in self.users:
            if user_id not in self.banned_users:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=broadcast_message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Failed to send broadcast to {user_id}: {e}")
        
        await update.message.reply_text(
            f"📊 **Broadcast Results:**\n\n"
            f"✅ **Sent:** {success_count}\n"
            f"❌ **Failed:** {fail_count}\n"
            f"📱 **Total Users:** {len(self.users)}",
            parse_mode='Markdown'
        )
    
    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ban command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID to ban!\n\n"
                "**Usage:** `/ban <user_id>`\n"
                "**Example:** `/ban 123456789`",
                parse_mode='Markdown'
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
            parse_mode='Markdown'
        )
    
    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unban command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID to unban!\n\n"
                "**Usage:** `/unban <user_id>`\n"
                "**Example:** `/unban 123456789`",
                parse_mode='Markdown'
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
            parse_mode='Markdown'
        )
    
    async def resetgiveaway_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /resetgiveaway command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        # Clear all redeemed codes but keep the codes themselves
        self.redeemed_codes.clear()
        self.save_data()
        
        await update.message.reply_text(
            "✅ **Giveaway reset successfully!**\n\n"
            "🔄 All codes are now available for redemption again.\n"
            "🏆 Leaderboard has been cleared.\n\n"
            "🎉 Ready for a new giveaway!",
            parse_mode='Markdown'
        )
    
    async def stopbot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stopbot command (Admin only)"""
        if not await self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        await update.message.reply_text("🛑 **Bot is shutting down...**")
        logger.info("Bot shutdown initiated by admin")
        # Note: In a real implementation, you would handle graceful shutdown here
        os._exit(0)

def main():
    """Main function to run the bot"""
    # Replace with your bot token and admin ID
    BOT_TOKEN = "8490064023:AAFVXBx26FdJxlI-aJWPxdmOvMpWFw3qXxU"  # Get this from @BotFather
    ADMIN_ID = 6446086262
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token!")
        return
    
    # Create bot instance
    bot = GiveawayBot(BOT_TOKEN, ADMIN_ID)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("redeem", bot.redeem_command))
    application.add_handler(CommandHandler("info", bot.info_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("leaderboard", bot.leaderboard_command))
    
    # Admin commands
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("listcodes", bot.listcodes_command))
    application.add_handler(CommandHandler("addcode", bot.addcode_command))
    application.add_handler(CommandHandler("addprize", bot.addprize_command))
    application.add_handler(CommandHandler("delcode", bot.delcode_command))
    application.add_handler(CommandHandler("gencode", bot.gencode_command))
    application.add_handler(CommandHandler("broadcast", bot.broadcast_command))
    application.add_handler(CommandHandler("ban", bot.ban_command))
    application.add_handler(CommandHandler("unban", bot.unban_command))
    application.add_handler(CommandHandler("resetgiveaway", bot.resetgiveaway_command))
    application.add_handler(CommandHandler("stopbot", bot.stopbot_command))
    
    # Start the bot
    print("🤖 ZIHAN GIVEAWAY Bot is starting...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    application.run_polling()

if __name__ == "__main__":
    main()
