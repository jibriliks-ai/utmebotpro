import logging
from datetime import time
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import BOT_TOKEN, SUBJECTS, UPGRADE_URL, SUPPORT_HANDLE, SYLLABUS_BRIEF, JAMB_SYLLABUS_BASE, PLANS
from tutor import ask_tutor
from database import get_leaderboard_top, check_limit, increment_usage, get_user_data, save_user_data
from channel_poster import generate_channel_message, post_to_channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade_link(user_id: int) -> str:
    return f"{UPGRADE_URL}?telegram_id={user_id}"

def main_menu_keyboard(user_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Study Plan", callback_data="study_plan"), InlineKeyboardButton("📝 Mock Exam", callback_data="mock")],
        [InlineKeyboardButton("📖 Syllabus", callback_data="syllabus"), InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("🎓 Ask Tutor", callback_data="ask_tutor"), InlineKeyboardButton(f"💎 Upgrade ₦{PLANS['monthly']['amount']}", url=upgrade_link(user_id))],
        [InlineKeyboardButton("🆘 Help", callback_data="help")]
    ])

def in_chat_menu_keyboard(user_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Study Plan", callback_data="study_plan"), InlineKeyboardButton("📝 Mock", callback_data="mock")],
        [InlineKeyboardButton("📖 Syllabus", callback_data="syllabus"), InlineKeyboardButton("🎓 Ask Tutor", callback_data="ask_tutor")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"), InlineKeyboardButton("💎 Upgrade", url=upgrade_link(user_id))],
        [InlineKeyboardButton("🆘 Help", callback_data="help")]
    ])

def subjects_keyboard(prefix: str):
    buttons = [[InlineKeyboardButton(s, callback_data=f"{prefix}_{s}")] for s in SUBJECTS]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)

def bottom_tabs():
    return ReplyKeyboardMarkup([["🎓 Ask Tutor", "📝 Mock"], ["📚 Study Plan", "📖 Syllabus"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user_data(user.id)
    welcome = (
        f"Welcome {user.first_name}! 👋\n\n"
        f"I'm *UTME Success Bot* — your personal JAMB tutor, available 24/7.\n\n"
        f"🎯 Score 300+ with:\n• Smart practice + instant explanations\n• Full mock exams\n• Ask Tutor — 200% smart\n\n"
        f"What would you like to do today?"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=main_menu_keyboard(user.id))
    await update.message.reply_text("Use buttons below:", reply_markup=bottom_tabs())

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user_data = get_user_data(user_id)

    if data == "study_plan":
        await query.edit_message_text("📚 *Study Plan*\n\nSelect subject:", parse_mode="Markdown", reply_markup=subjects_keyboard("study"))
    elif data.startswith("study_"):
        subject = data.replace("study_", "")
        context.user_data["current_subject"] = subject
        context.user_data["mode"] = "tutor"
        await query.message.reply_text(f"Let's study {subject}! 📖\n\nAsk me any question? I'm ready!", reply_markup=in_chat_menu_keyboard(user_id))
    elif data == "syllabus":
        await query.edit_message_text("📖 *JAMB Syllabus*\n\nSelect subject:", parse_mode="Markdown", reply_markup=subjects_keyboard("syll"))
    elif data.startswith("syll_"):
        subject = data.replace("syll_", "")
        brief = SYLLABUS_BRIEF.get(subject, "Core JAMB topics.")
        text = f"📖 *{subject} - JAMB Syllabus (Brief)*\n\n{brief}\n\n🔗 *Official:* {JAMB_SYLLABUS_BASE}\n\nAsk tutor to explain any topic."
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=subjects_keyboard("syll"))
    elif data == "ask_tutor":
        context.user_data["mode"] = "tutor"
        await query.message.reply_text("🎓 *Tutor Mode Active!*\n\nTell me subject and question.\nExample: `Biology - What is osmosis?`", parse_mode="Markdown", reply_markup=in_chat_menu_keyboard(user_id))
    elif data == "mock":
        top = get_leaderboard_top()
        banner = f"👑 *Top Scorer: {top['name']} - {top['score']} pts*\n━━━━━━━━━━━━━━━\n\n" if top else ""
        is_premium = user_data.get("is_premium", False)
        if is_premium:
            await query.message.reply_text(f"{banner}🔥 *Full Mock (Premium)*\nUnlimited access.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Start Full Mock", callback_data="start_full_mock")]]))
        else:
            if user_data.get("mock_count",0) >= 1:
                await handle_limit_reached(query.message, user_id)
                return
            await query.message.reply_text(f"{banner}📝 *Free Mock* (1 daily)", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Start Mock", callback_data="start_mock")]]))
    elif data == "leaderboard":
        top = get_leaderboard_top()
        txt = f"🏆 *LEADERBOARD*\n━━━━━━━━━━━━━━━\n\n👑 Leading: {top['name']} - {top['score']} pts" if top else "🏆 Leaderboard empty — be first!"
        await query.message.reply_text(txt, parse_mode="Markdown", reply_markup=in_chat_menu_keyboard(user_id))
    elif data == "help":
        await query.message.reply_text(f"Get help from our support team - {SUPPORT_HANDLE}", reply_markup=in_chat_menu_keyboard(user_id))
    elif data == "back_main":
        await query.edit_message_text("Choose an option:", reply_markup=main_menu_keyboard(user_id))
    elif data in ["start_mock", "start_full_mock"]:
        await query.message.reply_text("🚀 Mock starting...")

async def handle_limit_reached(message, user_id: int):
    user_data = get_user_data(user_id)
    attempts = user_data.get("over_limit_attempts",0)
    if attempts >=2:
        await message.reply_text("🚫 *Daily limit reached.*\n\nUpgrade to continue.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade to Premium - ₦2000", url=upgrade_link(user_id))]]))
    else:
        user_data["over_limit_attempts"] = attempts+1
        save_user_data(user_id, user_data)
        benefits = (
            "🚫 *You've reached your free daily limit!*\n\n"
            "💎 *Upgrade to Premium & Unlock:*\n"
            "✅ Unlimited Ask Tutor (200% smart)\n"
            "✅ Full Mock Exams daily + leaderboard\n"
            "✅ 20,000+ past questions explained\n"
            "✅ Voice notes - Nigerian accent\n\n"
            f"💰 *Monthly ₦{PLANS['monthly']['amount']} | 6 Months ₦{PLANS['six_months']['amount']} (Save 50%)*\n\n"
        )
        await message.reply_text(benefits, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"💎 Monthly ₦{PLANS['monthly']['amount']} - Flutterwave", url=upgrade_link(user_id))],
            [InlineKeyboardButton(f"🔥 6 Months ₦{PLANS['six_months']['amount']} - Best Value", url=upgrade_link(user_id))]
        ]))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text in ["🎓 Ask Tutor", "📝 Mock", "📚 Study Plan", "📖 Syllabus"]:
        mapping = {"🎓 Ask Tutor":"ask_tutor", "📝 Mock":"mock", "📚 Study Plan":"study_plan", "📖 Syllabus":"syllabus"}
        action = mapping[text]
        if action=="study_plan":
            await update.message.reply_text("📚 Select subject:", reply_markup=subjects_keyboard("study"))
        elif action=="syllabus":
            await update.message.reply_text("📖 Select subject:", reply_markup=subjects_keyboard("syll"))
        elif action=="ask_tutor":
            context.user_data["mode"]="tutor"
            await update.message.reply_text("🎓 Tutor Mode - Ask me anything!", reply_markup=in_chat_menu_keyboard(user_id))
        elif action=="mock":
            top=get_leaderboard_top()
            banner=f"👑 Top Scorer: {top['name']} - {top['score']} pts\n\n" if top else ""
            await update.message.reply_text(f"{banner}Tap below:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Mock Exam", callback_data="mock")]]))
        return

    if context.user_data.get("mode")=="tutor" or context.user_data.get("current_subject"):
        can_use,_=check_limit(user_id)
        if not can_use:
            await handle_limit_reached(update.message, user_id)
            return
        subject=context.user_data.get("current_subject","General")
        await update.message.chat.send_action(action="typing")
        answer=await ask_tutor(text, subject, user_id)
        increment_usage(user_id)
        await update.message.reply_text(answer, parse_mode="Markdown", reply_markup=in_chat_menu_keyboard(user_id))
    else:
        await update.message.reply_text("Select an option:", reply_markup=main_menu_keyboard(user_id))

async def scheduled_channel_post(context: ContextTypes.DEFAULT_TYPE):
    try:
        msg=generate_channel_message()
        await post_to_channel(context.bot, msg)
    except Exception as e:
        print(f"Channel post error: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    tz = pytz.timezone("Africa/Lagos")
    jq = app.job_queue
    jq.run_daily(scheduled_channel_post, time=time(hour=8, minute=0, tzinfo=tz), name="morning")
    jq.run_daily(scheduled_channel_post, time=time(hour=13, minute=0, tzinfo=tz), name="afternoon")
    jq.run_daily(scheduled_channel_post, time=time(hour=20, minute=0, tzinfo=tz), name="evening")
    print("UTMEbot running...")
    app.run_polling()

if __name__=="__main__":
    main()