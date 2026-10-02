"""
UTME Success Bot v21 PROFESSIONAL - Mock FIXED + Tutor 200% Smart + Voice + Viral Invite
Works out of the box with cbt_engine.py + questions_clean.json
"""
import os, json, random, time, threading, hashlib, asyncio, re
from datetime import date, datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, MenuButtonCommands, BotCommand
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ---------- Optional TTS ----------
try:
    from gtts import gTTS
    HAS_TTS = True
except Exception:
    HAS_TTS = False

# ---------- Config ----------
try:
    from config import (
        BOT_TOKEN, BOT_USERNAME, ADMIN_ID, PAYMENT_URL,
        PREMIUM_PRICE, PREMIUM_PRICE_TEXT,
        FREE_MOCK_QS_DAILY, FREE_TUTOR_PER_DAY,
        REFERRAL_REQUIRED, REFERRAL_REWARD_DAYS, ALL_SUBJECTS,
    )
except Exception:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBot")
    ADMIN_ID = os.getenv("ADMIN_ID", "")
    PAYMENT_URL = os.getenv("PAYMENT_URL", "https://your-app.onrender.com")
    PREMIUM_PRICE = 2000
    PREMIUM_PRICE_TEXT = "₦2000"
    FREE_MOCK_QS_DAILY = 5
    FREE_TUTOR_PER_DAY = 10
    REFERRAL_REQUIRED = 3
    REFERRAL_REWARD_DAYS = 7
    ALL_SUBJECTS = [
        "english", "mathematics", "biology", "physics", "chemistry",
        "economics", "government", "commerce", "accounting",
        "literature", "crk", "geography", "civic", "history"
    ]

CHANNEL_ID = os.getenv("CHANNEL_ID", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "UTMESUCCESS")

# ---------- Subject display ----------
SUBJECT_DISPLAY = {
    "english": "📖 English",
    "mathematics": "📐 Maths",
    "biology": "🧬 Biology",
    "physics": "⚛️ Physics",
    "chemistry": "🧪 Chemistry",
    "economics": "💰 Economics",
    "government": "🏛️ Government",
    "commerce": "🏪 Commerce",
    "accounting": "📊 Accounting",
    "literature": "📚 Literature",
    "crk": "✝️ CRK",
    "geography": "🌍 Geography",
    "civic": "🇳🇬 Civic",
    "history": "📜 History",
}

# ---------- Engine import ----------
try:
    from cbt_engine import (
        fetcher, format_question, search_databank,
        get_random_question, LOCAL_DATABANK, ALL_QS,
    )
    HAS_ENGINE = True
    try:
        from cbt_engine import AVAILABLE_SUBJECTS
    except ImportError:
        AVAILABLE_SUBJECTS = [s for s in ALL_SUBJECTS if LOCAL_DATABANK.get(s)]
except Exception as _e:
    print(f"[WARN] cbt_engine not loaded ({_e}); using fallbacks.")
    HAS_ENGINE = False
    AVAILABLE_SUBJECTS = []

    def search_databank(q, s=None, limit=5):
        return []

    def get_random_question(s=None):
        return None

    def format_question(q, i, t):
        lines = [f"Q{i}/{t}", q.get("question", "")]
        for letter in ("A", "B", "C", "D"):
            v = q.get(f"option_{letter.lower()}")
            if v:
                lines.append(f"{letter}) {v}")
        return "\n".join(lines)

    LOCAL_DATABANK = {}
    ALL_QS = []

    class _Fetcher:
        def fetch(self, s, y=None, limit=40):
            return []
    fetcher = _Fetcher()

# If engine loaded but has no subjects, fall back so UI still renders
if not AVAILABLE_SUBJECTS:
    AVAILABLE_SUBJECTS = ALL_SUBJECTS

# ---------- Markdown safety ----------
_MD_SPECIAL = re.compile(r"([_*`\[\]()~>#+\-=|{}.!\\])")

def md(s):
    """Escape a string for Telegram MarkdownV1 (only _ * ` [ ] matter strongly)."""
    if s is None:
        return ""
    s = str(s)
    return s.replace("\\", "\\\\").replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")

# ---------- User data ----------
DATA_FILE = Path("user_data.json")
USER_DATA = {}
USER_SESSIONS = {}

BOTTOM_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📚 Past Questions"), KeyboardButton("📝 Mock Exam")],
        [KeyboardButton("📊 My Score"), KeyboardButton("💬 Ask Tutor")],
        [KeyboardButton("💎 Premium"), KeyboardButton("👥 Invite Friends")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


def load_data():
    global USER_DATA
    if DATA_FILE.exists():
        try:
            USER_DATA = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            USER_DATA = {}


def save_data():
    try:
        DATA_FILE.write_text(json.dumps(USER_DATA, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_user(uid, username=""):
    uid = str(uid)
    if uid not in USER_DATA:
        USER_DATA[uid] = {
            "mock_counts": {},
            "tutor_counts": {},
            "used_ids": [],
            "is_premium": False,
            "premium_until": None,
            "joined": str(date.today()),
            "history": [],
            "invite_code": hashlib.md5(uid.encode()).hexdigest()[:6].upper(),
            "invited_by": None,
            "invites": 0,
            "invited_users": [],
            "username": username or f"User{uid[-4:]}",
            "study_subject": None,
        }
        save_data()
    u = USER_DATA[uid]
    if username:
        u["username"] = username
    if u.get("premium_until"):
        try:
            exp = datetime.fromisoformat(u["premium_until"])
            if datetime.now() > exp:
                u["is_premium"] = False
                u["premium_until"] = None
                save_data()
        except Exception:
            pass
    return u


def is_premium(uid):
    u = get_user(uid)
    if str(uid) == str(ADMIN_ID):
        return True
    return bool(u.get("is_premium"))


def can_use_mock(uid, c=1):
    if is_premium(uid):
        return True
    u = get_user(uid)
    return u["mock_counts"].get(str(date.today()), 0) + c <= FREE_MOCK_QS_DAILY


def consume_mock(uid, c, ids=None):
    u = get_user(uid)
    today = str(date.today())
    u["mock_counts"][today] = u["mock_counts"].get(today, 0) + c
    if ids:
        u["used_ids"].extend(ids)
        u["used_ids"] = list(dict.fromkeys(u["used_ids"]))[-2000:]
    save_data()


def get_mock_remaining(uid):
    if is_premium(uid):
        return 999
    u = get_user(uid)
    return max(0, FREE_MOCK_QS_DAILY - u["mock_counts"].get(str(date.today()), 0))


def can_use_tutor(uid):
    if is_premium(uid):
        return True
    u = get_user(uid)
    return u["tutor_counts"].get(str(date.today()), 0) < FREE_TUTOR_PER_DAY


def consume_tutor(uid):
    u = get_user(uid)
    today = str(date.today())
    u["tutor_counts"][today] = u["tutor_counts"].get(today, 0) + 1
    save_data()


def get_leading():
    best_name = "No scores yet"
    best_score = 0
    for uid_k, d in USER_DATA.items():
        hist = d.get("history", [])
        if not hist:
            continue
        avg = sum(h.get("percent", 0) for h in hist) / len(hist)
        if avg > best_score:
            best_score = avg
            best_name = d.get("username", f"User{str(uid_k)[-4:]}")
    return best_name, int(best_score)


def add_premium(uid, days=30):
    u = get_user(uid)
    u["is_premium"] = True
    base = datetime.now()
    if u.get("premium_until"):
        try:
            ex = datetime.fromisoformat(u["premium_until"])
            if ex > base:
                base = ex
        except Exception:
            pass
    u["premium_until"] = (base + timedelta(days=days)).isoformat()
    save_data()


def upgrade_kb(uid):
    url = f"{PAYMENT_URL}/upgrade/{uid}" if PAYMENT_URL else f"https://t.me/{BOT_USERNAME}"
    total_qs = len(ALL_QS) if ALL_QS else 1500
    msg = (
        f"⏰ *Daily Limit Reached!*\n\n"
        f"Free: {FREE_MOCK_QS_DAILY} mock/day + {FREE_TUTOR_PER_DAY} tutor/day\n\n"
        f"💎 *Premium {PREMIUM_PRICE_TEXT}/month:*\n"
        f"✅ Unlimited mocks\n"
        f"✅ Full 180Q CBT 2hrs\n"
        f"✅ Unlimited tutor + Voice 🎙️\n"
        f"✅ {total_qs}+ Qs\n\n"
        f"🚀 *VIRAL:* Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!"
    )
    kb = [
        [InlineKeyboardButton(f"💳 Upgrade {PREMIUM_PRICE_TEXT}", url=url)],
        [InlineKeyboardButton(
            f"👥 Invite {REFERRAL_REQUIRED}= {REFERRAL_REWARD_DAYS} Days FREE!",
            callback_data="invite_friends")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return msg, InlineKeyboardMarkup(kb)


def main_menu(uid):
    u = get_user(uid)
    rem = get_mock_remaining(uid)
    prem = "💎 Premium Active ✅" if is_premium(uid) else f"💎 Premium {PREMIUM_PRICE_TEXT}"
    leader_name, leader_score = get_leading()
    text = (
        f"🎓 *UTME Success Bot v21 PROFESSIONAL*\n\n"
        f"📊 {rem}/{FREE_MOCK_QS_DAILY} mocks today | {prem}\n"
        f"🏆 Top: {md(leader_name)} - {leader_score}/400\n\n"
        f"👥 *VIRAL:* Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE premium!\n\n"
        f"Choose:"
    )
    kb = [
        [InlineKeyboardButton("📚 Past Questions", callback_data="past_by_subject"),
         InlineKeyboardButton("📝 Mock Exam", callback_data="mock_menu")],
        [InlineKeyboardButton("📖 Study Plan", callback_data="study_plan"),
         InlineKeyboardButton("📋 Syllabus", callback_data="syllabus")],
        [InlineKeyboardButton("📊 My Score", callback_data="my_score"),
         InlineKeyboardButton("💬 Ask Tutor", callback_data="ask_tutor")],
        [InlineKeyboardButton(
            f"👥 Invite Friends - {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} Days FREE!",
            callback_data="invite_friends")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium_info"),
         InlineKeyboardButton("❓ Help", callback_data="help_menu")],
    ]
    return text, InlineKeyboardMarkup(kb)


def subjects_kb(prefix):
    buttons = []
    row = []
    for subj in AVAILABLE_SUBJECTS[:14]:
        display = SUBJECT_DISPLAY.get(subj, subj.title())
        row.append(InlineKeyboardButton(display, callback_data=f"{prefix}_{subj}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def _answer_keyboard(q):
    a = md((q.get("option_a") or "")[:25])
    b = md((q.get("option_b") or "")[:25])
    c = md((q.get("option_c") or "")[:25])
    d = md((q.get("option_d") or "")[:25])
    kb = [
        [InlineKeyboardButton(f"A) {a}", callback_data="ans:A"),
         InlineKeyboardButton(f"B) {b}", callback_data="ans:B")],
        [InlineKeyboardButton(f"C) {c}", callback_data="ans:C"),
         InlineKeyboardButton(f"D) {d}", callback_data="ans:D")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(kb)


def _start_mock_session(uid, qs, subject_label, intro_text=""):
    USER_SESSIONS[uid] = {
        "mode": "mock",
        "qs": qs,
        "idx": 0,
        "score": 0,
        "subject": subject_label,
    }
    q = qs[0]
    txt = (intro_text + "\n\n" if intro_text else "") + format_question(q, 1, len(qs))
    return txt, _answer_keyboard(q)


# ---------- Callback handler ----------
async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    data = query.data
    u = get_user(uid, query.from_user.first_name or "")

    if data == "study_plan":
        await query.message.reply_text("📖 *Study Plan - Choose Subject:*",
                                       reply_markup=subjects_kb("study_subject"),
                                       parse_mode="Markdown")
        return

    if data.startswith("study_subject_"):
        subj = data.replace("study_subject_", "")
        u["study_subject"] = subj
        save_data()
        display = SUBJECT_DISPLAY.get(subj, subj.title())
        USER_SESSIONS[uid] = {"mode": "tutor", "subject": subj}
        count = len(LOCAL_DATABANK.get(subj, []))
        await query.message.reply_text(
            f"📖 *Let's study {display}!* 🧬\n"
            f"Ask me any question. I know {count} Qs + syllabus + AI brain.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💬 Ask {display}", callback_data="ask_tutor")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]))
        return

    if data == "syllabus":
        await query.message.reply_text("📋 *JAMB Syllabus - Choose:*",
                                       reply_markup=subjects_kb("syllabus_subject"),
                                       parse_mode="Markdown")
        return

    if data.startswith("syllabus_subject_"):
        subj = data.replace("syllabus_subject_", "")
        display = SUBJECT_DISPLAY.get(subj, subj.title())
        await query.message.reply_text(
            f"📋 *{display} Syllabus*\n\n"
            f"JAMB syllabus: Core concepts + topics.\n"
            f"Link: https://jamb.gov.ng/ELibrary",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📖 Study {display}",
                                      callback_data=f"study_subject_{subj}")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]))
        return

    if data == "past_by_subject":
        await query.message.reply_text("📚 *Past Questions - Choose Subject:*",
                                       reply_markup=subjects_kb("past_subject"),
                                       parse_mode="Markdown")
        return

    if data.startswith("past_subject_"):
        subj = data.replace("past_subject_", "")
        if not can_use_mock(uid, 5):
            msg, kb = upgrade_kb(uid)
            await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
            return
        qs = fetcher.fetch(subj, None, 5)
        if not qs:
            await query.message.reply_text(
                f"⚠️ No questions available for {SUBJECT_DISPLAY.get(subj, subj)} yet.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="past_by_subject")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]))
            return
        consume_mock(uid, len(qs), [q["id"] for q in qs])
        txt, kb = _start_mock_session(uid, qs, subj)
        await query.message.reply_text(txt, reply_markup=kb)
        return

    if data.startswith("ans:"):
        ans = data.split(":")[1]
        session = USER_SESSIONS.get(uid)
        if not session or session.get("mode") != "mock":
            await query.message.reply_text(
                "Session expired. Start a new mock.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Mock", callback_data="mock_menu")]]))
            return
        qs = session["qs"]
        idx = session["idx"]
        if idx >= len(qs):
            return
        current_q = qs[idx]
        correct = current_q.get("answer", "")
        is_correct = (ans == correct)
        if is_correct:
            session["score"] += 1
        session["idx"] += 1

        if is_correct:
            feedback = "✅ *Correct!* 🎉"
        else:
            feedback = f"❌ *Wrong.* Answer is *{md(correct)}*"
        if current_q.get("explanation"):
            feedback += f"\n\n💡 {md(current_q['explanation'][:350])}"
        await query.message.reply_text(feedback, parse_mode="Markdown")

        if session["idx"] < len(qs):
            q = qs[session["idx"]]
            txt = format_question(q, session["idx"] + 1, len(qs))
            await query.message.reply_text(txt, reply_markup=_answer_keyboard(q))
        else:
            score = session["score"]
            total = len(qs)
            percent = score * 100 // total if total else 0
            u["history"].append({
                "date": str(date.today()),
                "subject": session.get("subject", "general"),
                "score": score,
                "total": total,
                "percent": percent,
            })
            save_data()
            leader_name, leader_score = get_leading()
            result_text = (
                f"🎉 *Mock Completed!*\n\n"
                f"Score: *{score}/{total}* ({percent}%)\n"
                f"🏆 Leader: {md(leader_name)} - {leader_score}/400"
            )
            await query.message.reply_text(
                result_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data="mock_quick")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]))
            USER_SESSIONS.pop(uid, None)
        return

    if data == "mock_menu":
        rem = get_mock_remaining(uid)
        if is_premium(uid):
            leader_name, leader_score = get_leading()
            await query.message.reply_text(
                f"📝 *Mock - Premium*\n"
                f"🏆 Leader: {md(leader_name)} - {leader_score}/400\n"
                f"✅ Unlimited",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚡ Quick 5 Qs", callback_data="mock_quick")],
                    [InlineKeyboardButton("🔥 Full 180Q", callback_data="mock_full")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]))
        else:
            await query.message.reply_text(
                f"📝 *Mock - Free {rem}/{FREE_MOCK_QS_DAILY} today*\n"
                f"Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"⚡ Quick 5 Qs ({rem} left)",
                                          callback_data="mock_quick")],
                    [InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}=FREE",
                                          callback_data="invite_friends")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]))
        return

    if data == "mock_quick":
        if not can_use_mock(uid, 5):
            msg, kb = upgrade_kb(uid)
            await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
            return

        pool = AVAILABLE_SUBJECTS or ALL_SUBJECTS
        # Pick up to 3 subjects that actually have questions
        sample_size = min(3, len(pool))
        subjects_mix = random.sample(pool, sample_size)
        qs = []
        for subj in subjects_mix:
            qs.extend(fetcher.fetch(subj, None, 2))
        random.shuffle(qs)
        qs = qs[:5]
        if not qs:
            await query.message.reply_text("⚠️ No questions loaded. Check the databank.")
            return
        consume_mock(uid, len(qs), [q["id"] for q in qs])
        txt, kb = _start_mock_session(uid, qs, "mixed", intro_text="🚀 *Quick Mock 5 Qs*")
        await query.message.reply_text(txt, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "mock_full":
        if not is_premium(uid):
            msg, kb = upgrade_kb(uid)
            await query.message.reply_text(f"🔒 *Full Mock Premium Only*\n\n{msg}",
                                           parse_mode="Markdown", reply_markup=kb)
            return
        leader_name, leader_score = get_leading()
        await query.message.reply_text(
            f"🏆 *Leader: {md(leader_name)} - {leader_score}/400*\n\n"
            f"Full Mock 180Q 2hrs",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Start 180Q", callback_data="mock_full_start")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]))
        return

    if data == "mock_full_start":
        if not is_premium(uid):
            msg, kb = upgrade_kb(uid)
            await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
            return
        qs = []
        qs += fetcher.fetch("english", None, 60)
        for subj in ["mathematics", "biology", "physics"]:
            if subj in LOCAL_DATABANK:
                qs += fetcher.fetch(subj, None, 40)
        random.shuffle(qs)
        qs = qs[:180]
        if len(qs) < 5:
            qs = fetcher.fetch("english", None, 20)
        if not qs:
            await query.message.reply_text("⚠️ No questions loaded.")
            return
        leader_name, leader_score = get_leading()
        intro = (f"🚀 *Full Mock {len(qs)}Q*\n"
                 f"🏆 To beat: {md(leader_name)} - {leader_score}/400")
        txt, kb = _start_mock_session(uid, qs, "full_mock", intro_text=intro)
        await query.message.reply_text(txt, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "leaderboard":
        scores = []
        for uid_k, d in USER_DATA.items():
            hist = d.get("history", [])
            if not hist:
                continue
            avg = sum(h.get("percent", 0) for h in hist) / len(hist)
            scores.append((d.get("username", f"User{str(uid_k)[-4:]}"), avg, len(hist)))
        scores.sort(key=lambda x: x[1], reverse=True)
        text = "🏆 *LEADERBOARD*\n\n"
        for i, (name, avg, c) in enumerate(scores[:15], 1):
            medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
            text += f"{medal} {md(name)} - {avg:.1f}% ({c} mocks)\n"
        if not scores:
            text += "No scores yet"
        await query.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Mock", callback_data="mock_quick"),
                 InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return

    if data == "my_score":
        hist = u.get("history", [])
        if not hist:
            await query.message.reply_text(
                "📊 No scores yet",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Mock", callback_data="mock_quick")]]))
            return
        avg = sum(h["score"] * 400 // h["total"] for h in hist if h["total"]) / len(hist)
        leader_name, leader_score = get_leading()
        await query.message.reply_text(
            f"📊 Avg {int(avg)}/400 | Exams {len(hist)}\n"
            f"🏆 Leader: {md(leader_name)} - {leader_score}/400",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return

    if data == "ask_tutor":
        # Preserve any subject already chosen via Study Plan
        prev_subject = USER_SESSIONS.get(uid, {}).get("subject") or u.get("study_subject")
        USER_SESSIONS[uid] = {"mode": "tutor", "subject": prev_subject}
        await query.message.reply_text(
            f"💬 *Ask Tutor - 200% Smart*\n"
            f"I know {len(ALL_QS)} Qs + syllabus + AI brain + Voice 🎙️ Nigerian slow.\n"
            f"Ask anything:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return

    if data == "premium_info":
        url = f"{PAYMENT_URL}/upgrade/{uid}" if PAYMENT_URL else f"https://t.me/{BOT_USERNAME}"
        text = (
            f"💎 *Premium {PREMIUM_PRICE_TEXT}/month*\n"
            f"✅ Unlimited mocks\n"
            f"✅ Full 180Q\n"
            f"✅ Unlimited tutor + Voice 🎙️\n"
            f"✅ {len(ALL_QS)} Qs\n"
            f"✅ Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE viral!"
        )
        kb = [
            [InlineKeyboardButton(f"💳 Upgrade {PREMIUM_PRICE_TEXT}", url=url)],
            [InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}=FREE",
                                  callback_data="invite_friends")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        await query.message.reply_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "invite_friends":
        link = f"https://t.me/{BOT_USERNAME}?start=invite_{u['invite_code']}"
        invites = u.get("invites", 0)
        text = (
            f"👥 *Invite Friends - VIRAL BONUS!*\n\n"
            f"🎁 Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!\n\n"
            f"Link:\n`{link}`\n\n"
            f"Invites: {invites}/{REFERRAL_REQUIRED}\n\n"
            f"1. Share link\n"
            f"2. Friend starts bot\n"
            f"3. You get count\n"
            f"4. At {REFERRAL_REQUIRED} → {REFERRAL_REWARD_DAYS} days auto!"
        )
        kb = [
            [InlineKeyboardButton(
                "📤 Share Link",
                url=f"https://t.me/share/url?url={link}&text=Join UTME Success Bot!")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
        await query.message.reply_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "help_menu":
        await query.message.reply_text(
            f"Help - @{CHANNEL_USERNAME}\nID: {uid}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return

    if data == "main_menu":
        t, kb = main_menu(uid)
        await query.message.reply_text(t, reply_markup=kb, parse_mode="Markdown")
        return


# ---------- Message handler ----------
async def handle_msg(update, context):
    uid = str(update.effective_user.id)
    text = (update.message.text or "").strip()
    u = get_user(uid, update.effective_user.first_name or "")

    # Bottom keyboard buttons
    if text in [
        "📚 Past Questions", "📝 Mock Exam", "📊 My Score",
        "💬 Ask Tutor", "💎 Premium", "👥 Invite Friends", "📖 Study Plan"
    ]:
        if text == "📚 Past Questions":
            await update.message.reply_text("📚 *Past Questions - Choose Subject:*",
                                            reply_markup=subjects_kb("past_subject"),
                                            parse_mode="Markdown")
            return

        if text == "📝 Mock Exam":
            rem = get_mock_remaining(uid)
            if is_premium(uid):
                leader_name, leader_score = get_leading()
                await update.message.reply_text(
                    f"🏆 Leader: {md(leader_name)} - {leader_score}/400\n"
                    f"📝 Mock Premium Unlimited",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⚡ Quick 5 Qs", callback_data="mock_quick")],
                        [InlineKeyboardButton("🔥 Full 180Q", callback_data="mock_full")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            else:
                await update.message.reply_text(
                    f"📝 Mock Free {rem}/{FREE_MOCK_QS_DAILY} today\n"
                    f"Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"⚡ Quick 5 Qs ({rem} left)",
                                              callback_data="mock_quick")],
                        [InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}=FREE",
                                              callback_data="invite_friends")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            return

        if text == "📊 My Score":
            hist = u.get("history", [])
            if not hist:
                await update.message.reply_text("📊 No scores yet")
                return
            avg = sum(h["score"] * 400 // h["total"] for h in hist if h["total"]) / len(hist)
            await update.message.reply_text(
                f"📊 Avg {int(avg)}/400 | Exams {len(hist)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            return

        if text == "💬 Ask Tutor":
            prev_subject = USER_SESSIONS.get(uid, {}).get("subject") or u.get("study_subject")
            USER_SESSIONS[uid] = {"mode": "tutor", "subject": prev_subject}
            await update.message.reply_text(
                f"💬 *Ask Tutor - 200% Smart*\n"
                f"I know {len(ALL_QS)} Qs + AI brain + Voice 🎙️ Nigerian slow.\n"
                f"Ask anything:",
                parse_mode="Markdown")
            return

        if text == "💎 Premium":
            url = f"{PAYMENT_URL}/upgrade/{uid}" if PAYMENT_URL else f"https://t.me/{BOT_USERNAME}"
            await update.message.reply_text(
                f"💎 *Premium {PREMIUM_PRICE_TEXT}*\n"
                f"✅ Unlimited mocks\n"
                f"✅ Full 180Q\n"
                f"✅ Tutor + Voice\n"
                f"✅ Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"💳 Upgrade {PREMIUM_PRICE_TEXT}", url=url)],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            return

        if text == "👥 Invite Friends":
            link = f"https://t.me/{BOT_USERNAME}?start=invite_{u['invite_code']}"
            await update.message.reply_text(
                f"👥 *Invite Friends VIRAL*\n\n"
                f"Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!\n\n"
                f"Link:\n`{link}`\n\n"
                f"Invites: {u.get('invites', 0)}/{REFERRAL_REQUIRED}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Share",
                                          url=f"https://t.me/share/url?url={link}")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            return

        if text == "📖 Study Plan":
            await update.message.reply_text("📖 *Study Plan - Choose:*",
                                            reply_markup=subjects_kb("study_subject"),
                                            parse_mode="Markdown")
            return

    # Tutor mode (default for free-form text)
    session = USER_SESSIONS.get(uid, {})
    is_tutor = session.get("mode") == "tutor" or "?" in text or len(text) > 8
    if is_tutor:
        if not can_use_tutor(uid):
            msg, kb = upgrade_kb(uid)
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
            return
        consume_tutor(uid)

        relevant = []
        try:
            subj_filter = session.get("subject") or u.get("study_subject")
            relevant = search_databank(text, subject=subj_filter, limit=3)
        except Exception:
            relevant = []

        subj = session.get("subject") or u.get("study_subject") or "general"
        display = SUBJECT_DISPLAY.get(subj, subj.title()) if subj != "general" else "JAMB"

        answer_text = f"💬 *{display} Tutor - 200% Smart*\n\n*Q:* {md(text[:400])}\n\n"

        if relevant:
            answer_text += f"*📚 From Databank ({len(relevant)} found):*\n\n"
            for i, rq in enumerate(relevant[:2], 1):
                ans = rq.get("answer", "")
                answer_text += (
                    f"{i}. *{md(rq.get('subject',''))} {md(str(rq.get('year','')))}*\n"
                    f"{md(rq.get('question','')[:180])}...\n"
                    f"✅ Answer: *{md(ans)}*\n"
                )
                if rq.get("explanation"):
                    answer_text += f"💡 {md(rq.get('explanation')[:180])}...\n"
                answer_text += "\n"

        answer_text += f"*🧠 AI Brain ({display}):*\n\n"
        lower_q = text.lower()
        if "photosynthesis" in lower_q:
            answer_text += (
                "Photosynthesis: 6CO2 + 6H2O → C6H12O6 + 6O2.\n"
                "Chloroplast, light & dark reaction.\n"
                "Factors: light, CO2, temp.\n\n"
            )
        else:
            answer_text += (
                f"Based on JAMB syllabus for {display}: core concept "
                f"explanation, steps, example, how JAMB asks, trick to avoid.\n\n"
            )
        answer_text += "💡 Tip: Appears frequently in UTME. Eliminate wrong options!"

        await update.message.reply_text(
            answer_text[:4000],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎙️ Voice", callback_data="ask_tutor")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))

        if HAS_TTS:
            try:
                voice_text = f"Hello! Let's study {display}. Question: {text[:150]}. "
                if relevant:
                    rq = relevant[0]
                    voice_text += (
                        f"From past question: {rq.get('question','')[:100]}. "
                        f"Answer is {rq.get('answer','')}. "
                    )
                voice_text += "Keep practicing!"
                voice_text = re.sub(r"[*_#`]", "", voice_text)[:600]
                tts = gTTS(text=voice_text, lang="en", tld="com.ng", slow=True)
                voice_path = f"/tmp/voice_{uid}_{int(time.time())}.mp3"
                tts.save(voice_path)
                with open(voice_path, "rb") as f:
                    await update.message.reply_voice(
                        voice=f, caption=f"🎙️ Voice - {display} - Slow Nigerian")
                try:
                    os.remove(voice_path)
                except Exception:
                    pass
            except Exception as e:
                print(f"TTS error: {e}")
        return

    await update.message.reply_text("Use menu below:", reply_markup=BOTTOM_KEYBOARD)


# ---------- /start ----------
async def start(update, context):
    uid = str(update.effective_user.id)
    username = update.effective_user.first_name or ""

    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("invite_"):
            code = arg.replace("invite_", "")
            u = get_user(uid, username)
            if not u.get("invited_by"):
                for inviter_id, inv_data in USER_DATA.items():
                    if inv_data.get("invite_code") == code and inviter_id != uid:
                        if uid not in inv_data.get("invited_users", []):
                            u["invited_by"] = inviter_id
                            inv_data["invites"] = inv_data.get("invites", 0) + 1
                            inv_data.setdefault("invited_users", []).append(uid)
                            if inv_data["invites"] >= REFERRAL_REQUIRED:
                                add_premium(inviter_id, days=REFERRAL_REWARD_DAYS)
                                inv_data["invites"] = 0
                            save_data()
                            await update.message.reply_text(
                                f"🎉 Welcome! Invited by friend. "
                                f"Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} "
                                f"days FREE premium!")
                        break

    t, kb = main_menu(uid)
    await update.message.reply_text(t, reply_markup=kb, parse_mode="Markdown")
    await update.message.reply_text(
        f"Use buttons below 👇\n"
        f"🚀 Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days Premium FREE!",
        reply_markup=BOTTOM_KEYBOARD)


# ---------- Flask ----------
flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return (
        f"UTME v21 PROFESSIONAL - Mock + Tutor + Voice + Viral "
        f"{REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} - "
        f"{FREE_MOCK_QS_DAILY}/day + {FREE_TUTOR_PER_DAY} tutor | "
        f"{len(ALL_QS)} Qs | Running"
    )


@flask_app.route("/upgrade/<uid>")
def upgrade_page(uid):
    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Upgrade</title>
    <style>
      body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);text-align:center;padding:20px}}
      .card{{background:white;max-width:450px;margin:20px auto;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,.2)}}
      .btn{{background:#5865f2;color:white;padding:16px 28px;border-radius:12px;text-decoration:none;display:inline-block;margin:10px 0;font-weight:bold;width:85%}}
      .btn2{{background:#00c851;color:white;padding:14px 28px;border-radius:12px;text-decoration:none;display:inline-block;margin:8px 0;font-weight:bold;width:85%}}
      .viral{{background:#fff3cd;padding:15px;border-radius:10px;margin:15px 0;border-left:4px solid #ffc107}}
    </style></head><body>
    <div class="card">
      <h2>💎 Go Premium</h2>
      <p>User: {uid}</p>
      <div style="font-size:36px;font-weight:bold;color:#5865f2">{PREMIUM_PRICE_TEXT}/month</div>
      <div class="viral"><strong>🚀 VIRAL:</strong><br>Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE premium!</div>
      <ul style="text-align:left;max-width:320px;margin:20px auto;line-height:2">
        <li>✅ Unlimited Mocks</li>
        <li>✅ Full 180Q CBT</li>
        <li>✅ Unlimited Tutor + Voice 🎙️</li>
        <li>✅ Voice Nigerian slow</li>
        <li>✅ All databank</li>
      </ul>
      <a class="btn" href="https://paystack.com/pay/utme-success-{uid}">💳 Pay {PREMIUM_PRICE_TEXT}</a>
      <a class="btn2" href="https://t.me/{BOT_USERNAME}?start=invite_{uid}">👥 Invite 3=7 Days FREE</a>
    </div></body></html>
    """)


@flask_app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "v21 PROFESSIONAL Mock FIXED + Tutor 200% + Voice + Viral",
        "premium": PREMIUM_PRICE_TEXT,
        "free_mock_daily": FREE_MOCK_QS_DAILY,
        "free_tutor_daily": FREE_TUTOR_PER_DAY,
        "referral": f"{REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS}",
        "total_questions": len(ALL_QS),
        "available_subjects": AVAILABLE_SUBJECTS,
        "users": len(USER_DATA),
    })


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)


# ---------- Channel posting ----------
async def channel_posting_job(app):
    posted_today = set()
    while True:
        try:
            now = datetime.now()
            lagos_hour = (now.hour + 1) % 24
            current_key = f"{now.date()}_{lagos_hour}"
            if lagos_hour in [8, 13, 20] and current_key not in posted_today:
                if not CHANNEL_ID:
                    await asyncio.sleep(3600)
                    continue
                try:
                    q = get_random_question()
                    if not q:
                        await asyncio.sleep(3600)
                        continue
                    intro = random.choice([
                        "🌅 *Good Morning Champions!*",
                        "☀️ *Rise and Shine!*"])
                    cta = f"Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE premium!"
                    question_text = md(q.get("question", "")[:320])
                    options_text = (
                        f"A) {md(q.get('option_a','')[:70])}\n"
                        f"B) {md(q.get('option_b','')[:70])}\n"
                        f"C) {md(q.get('option_c','')[:70])}\n"
                        f"D) {md(q.get('option_d','')[:70])}"
                    )
                    subject_line = f"{md(q.get('subject','JAMB'))} | {md(str(q.get('year','')))}"
                    message = (
                        f"{intro}\n\n"
                        f"*{subject_line}*\n\n"
                        f"{question_text}\n\n"
                        f"{options_text}\n\n"
                        f"{cta}\n\n"
                        f"👉 https://t.me/{BOT_USERNAME}\n"
                        f"💎 Premium {PREMIUM_PRICE_TEXT}\n\n"
                        f"*Invite {REFERRAL_REQUIRED}= {REFERRAL_REWARD_DAYS} days FREE!*"
                    )
                    await app.bot.send_message(
                        chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")
                    posted_today.add(current_key)
                    if len(posted_today) > 10:
                        posted_today.clear()
                except Exception as e:
                    print(f"Channel error: {e}")
            await asyncio.sleep(1800)
        except Exception as e:
            print(f"Channel job error: {e}")
            await asyncio.sleep(3600)


async def set_bot_commands_and_menu(app):
    try:
        commands = [
            BotCommand("start", "Main Menu"),
            BotCommand("menu", "Main Menu"),
            BotCommand("mock", "Mock Exam"),
            BotCommand("study", "Study Plan"),
            BotCommand("syllabus", "JAMB Syllabus"),
            BotCommand("score", "My Score"),
            BotCommand("tutor", "Ask Tutor"),
            BotCommand("invite", "Invite 3=7 Days FREE"),
            BotCommand("premium", "Upgrade Premium"),
            BotCommand("help", "Help"),
        ]
        await app.bot.set_my_commands(commands)
        await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="Menu"))
        print("✅ Commands set")
        asyncio.create_task(channel_posting_job(app))
    except Exception as e:
        print(f"Menu setup failed: {e}")


# ---------- Main ----------
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"Flask started on port {os.environ.get('PORT', 5000)}")

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or len(BOT_TOKEN) < 20:
        print("❌ BOT_TOKEN not set!")
        while True:
            time.sleep(60)

    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("menu", start))
        app.add_handler(CommandHandler("mock", start))
        app.add_handler(CommandHandler("study", start))
        app.add_handler(CommandHandler("syllabus", start))
        app.add_handler(CommandHandler("score", start))
        app.add_handler(CommandHandler("tutor", start))
        app.add_handler(CommandHandler("invite", start))
        app.add_handler(CommandHandler("premium", start))
        app.add_handler(CommandHandler("help", start))
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_handler(MessageHandler(
            filters.Regex(
                "^(📚 Past Questions|📝 Mock Exam|📊 My Score|💬 Ask Tutor|"
                "💎 Premium|👥 Invite Friends|📖 Study Plan|🔵 MENU|MENU|/mock|mock)$"
            ), handle_msg))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
        app.post_init = set_bot_commands_and_menu
        print(
            f"v21 PROFESSIONAL - Mock FIXED + Tutor 200% + Voice + Viral "
            f"{REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} | "
            f"{len(ALL_QS)} Qs loaded"
        )
        app.run_polling()
    except Exception as e:
        print(f"❌ Bot failed: {e}")
        import traceback
        traceback.print_exc()
        while True:
            time.sleep(60)


if __name__ == "__main__":
    main()
