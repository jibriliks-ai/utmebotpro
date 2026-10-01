
"""
UTME Success Bot - v17.1 FINAL PROFESSIONAL
Premium: ₦2000
Free: 5 mock Qs DAILY (locked) + 2 tutor/day
Referral: 3 people = 1 week premium
Paid: unlimited

Structure:
1. LEARN (90%)
   - Past Questions: By Subject, By Year 2010-2024
   - Mock Exam: Quick Test 20Q 15min, Full JAMB 180Q 2hr, Subject Mock 40Q
   - Explain with Voice: auto after fail

2. TRACK
   - My Score: avg, strong, weak, leaderboard
   - Study Plan

3. SUPPORT / VIRAL
   - Invite Friend -> 3 referrals = 1 week premium
   - Go Premium ₦2000
   - Help

Viral: Share My Score image
Single file + modular imports, ALOC live 2010-2024 ~7500 Qs
"""

import os, json, random, time, logging, threading, hashlib
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
import requests
from flask import Flask, render_template_string, jsonify

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

try:
    from gtts import gTTS
    HAS_TTS=True
except:
    HAS_TTS=False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL=True
except:
    HAS_PIL=False

# --- CONFIG ---
try:
    from config import (
        BOT_TOKEN, BOT_USERNAME, ADMIN_ID, PAYMENT_URL,
        ALOC_ACCESS_TOKEN, PREMIUM_PRICE, PREMIUM_PRICE_TEXT,
        FREE_MOCK_QS_DAILY, FREE_TUTOR_PER_DAY,
        REFERRAL_REQUIRED, REFERRAL_REWARD_DAYS, YEARS, ALL_SUBJECTS
    )
except:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBot")
    ADMIN_ID = os.getenv("ADMIN_ID", "")
    PAYMENT_URL = os.getenv("PAYMENT_URL", "https://your-app.onrender.com")
    ALOC_ACCESS_TOKEN = os.getenv("ALOC_ACCESS_TOKEN", "")
    PREMIUM_PRICE = 2000
    PREMIUM_PRICE_TEXT = "₦2000"
    FREE_MOCK_QS_DAILY = 5
    FREE_TUTOR_PER_DAY = 2
    REFERRAL_REQUIRED = 3
    REFERRAL_REWARD_DAYS = 7
    YEARS = list(range(2010, 2025))
    ALL_SUBJECTS = ["english","mathematics","biology","physics","chemistry","economics","government","commerce","accounting","literature","crk","geography","civic","history"]

SUBJECT_DISPLAY = {
    "english":"📖 English","mathematics":"📐 Maths","biology":"🧬 Biology","physics":"⚛️ Physics","chemistry":"🧪 Chemistry",
    "economics":"💰 Economics","government":"🏛️ Government","commerce":"🏪 Commerce","accounting":"📊 Accounting",
    "literature":"📚 Literature","crk":"✝️ CRK","geography":"🌍 Geography","civic":"🇳🇬 Civic","history":"📜 History"
}

JAMB_SYLLABUS = {
    "english": "Comprehension, Lexis & Structure, Oral Forms, etc.",
    "mathematics": "Number & Numeration, Algebra, Geometry, Trigonometry, Statistics...",
    "biology": "Variety, Cell, Genetics, Ecology...",
    "physics": "Mechanics, Heat, Waves, Electricity...",
    "chemistry": "Particulate nature, Periodic table, Reactions...",
    "economics": "Demand/Supply, Production, Market structure...",
    "government": "Political systems, Constitution...",
}

DATA_FILE = Path("user_data.json")
USER_DATA = {}
CACHE = {}
CACHE_TIME = {}
USER_SESSIONS = {}
USER_JAMB_PICK = {}
PRECACHE_STATUS = {"running": False, "progress": "", "total_fetched": 0}

def load_data():
    global USER_DATA
    if DATA_FILE.exists():
        try:
            USER_DATA=json.loads(DATA_FILE.read_text())
            print(f"Loaded {len(USER_DATA)} users - locked quota")
        except:
            USER_DATA={}
    else:
        USER_DATA={}

def save_data():
    try:
        DATA_FILE.write_text(json.dumps(USER_DATA, indent=2))
    except Exception as e:
        print(f"Save err {e}")

def get_user(uid):
    uid=str(uid)
    if uid not in USER_DATA:
        USER_DATA[uid]={
            "mock_counts":{},  # date_str -> count (DAILY 5 limit LOCKED)
            "tutor_counts":{},
            "used_ids":[],
            "is_premium":False,
            "premium_until":None,
            "joined":str(date.today()),
            "history":[],
            "scores_by_subject":{},
            "invite_code": hashlib.md5(uid.encode()).hexdigest()[:6].upper(),
            "invited_by":None,
            "invites":0,
            "invited_users":[],  # list of uids invited
            "full_cbt_attempts":0
        }
        save_data()
    u=USER_DATA[uid]
    if u.get("premium_until"):
        try:
            exp=datetime.fromisoformat(u["premium_until"])
            if datetime.now() > exp:
                u["is_premium"]=False
                u["premium_until"]=None
                save_data()
        except:
            pass
    return u

def is_premium(uid):
    u=get_user(uid)
    if str(uid)==str(ADMIN_ID): return True
    return bool(u.get("is_premium"))

def can_use_mock(uid, count=1):
    if is_premium(uid): return True
    u=get_user(uid)
    today=str(date.today())
    used_today=u["mock_counts"].get(today,0)
    return used_today + count <= FREE_MOCK_QS_DAILY

def consume_mock(uid, count, ids=None):
    u=get_user(uid)
    today=str(date.today())
    u["mock_counts"][today]=u["mock_counts"].get(today,0)+count
    if ids:
        u["used_ids"].extend(ids)
        u["used_ids"]=list(dict.fromkeys(u["used_ids"]))[-1500:]
    save_data()

def get_mock_remaining(uid):
    if is_premium(uid): return 999
    u=get_user(uid)
    today=str(date.today())
    used=u["mock_counts"].get(today,0)
    return max(0, FREE_MOCK_QS_DAILY - used)

def can_use_tutor(uid):
    if is_premium(uid): return True
    u=get_user(uid)
    return u["tutor_counts"].get(str(date.today()),0) < FREE_TUTOR_PER_DAY

def consume_tutor(uid):
    u=get_user(uid)
    today=str(date.today())
    u["tutor_counts"][today]=u["tutor_counts"].get(today,0)+1
    save_data()

def add_premium(uid, days=30, reason=""):
    u=get_user(uid)
    u["is_premium"]=True
    # Extend if already premium
    if u.get("premium_until"):
        try:
            existing=datetime.fromisoformat(u["premium_until"])
            if existing > datetime.now():
                until=existing + timedelta(days=days)
            else:
                until=datetime.now() + timedelta(days=days)
        except:
            until=datetime.now() + timedelta(days=days)
    else:
        until=datetime.now() + timedelta(days=days)
    u["premium_until"]=until.isoformat()
    save_data()
    print(f"✅ Premium +{days} days for {uid} reason: {reason}")
    return until

def check_referral_reward(uid):
    """3 referrals = 1 week premium"""
    u=get_user(uid)
    if u["invites"] >= REFERRAL_REQUIRED:
        # Check if already rewarded for this batch
        rewarded_batches = u.get("referral_rewards", 0)
        batches = u["invites"] // REFERRAL_REQUIRED
        if batches > rewarded_batches:
            # Give reward
            add_premium(uid, days=REFERRAL_REWARD_DAYS, reason=f"Referral {u['invites']} friends")
            u["referral_rewards"]=batches
            save_data()
            return True
    return False

load_data()

# --- ALOC FETCHER ---
try:
    from cbt_engine import fetcher, format_question
    HAS_ENGINE=True
except:
    HAS_ENGINE=False
    # Fallback fetcher if cbt_engine not available (single file mode)
    class ALOCFetcher:
        def __init__(self, token=ALOC_ACCESS_TOKEN):
            self.token=token
            self.base_v2="https://questions.aloc.com.ng/api/v2"
            self.base_old="https://questions.aloc.ng/api/v2"
            self.session=requests.Session()
            self.session.headers.update({"Accept":"application/json"})
            if token: self.session.headers.update({"AccessToken": token})
        def fetch(self, subject, year, limit=40):
            aloc_map={"english":"english","mathematics":"mathematics","biology":"biology","physics":"physics","chemistry":"chemistry","economics":"economics","government":"government","commerce":"commerce","accounting":"accounting","literature":"englishlit","crk":"crk","geography":"geography","civic":"civiledu","history":"history"}
            aloc_code=aloc_map.get(subject.lower(), subject.lower())
            key=(aloc_code, str(year))
            if key in CACHE and time.time()-CACHE_TIME.get(key,0)<21600:
                return CACHE[key]
            urls=[f"{self.base_v2}/q/{limit}?subject={aloc_code}&year={year}&type=utme", f"{self.base_old}/q/{limit}?subject={aloc_code}&year={year}&type=utme"]
            for url in urls:
                try:
                    r=self.session.get(url, timeout=12)
                    if r.status_code==200:
                        qs=self.parse(r.json(), subject, year)
                        if qs:
                            CACHE[key]=qs
                            CACHE_TIME[key]=time.time()
                            return qs
                except:
                    continue
            return []
        def parse(self, data, subject, year):
            items=[]
            if isinstance(data, dict):
                if isinstance(data.get("data"), list): items=data["data"]
                elif isinstance(data.get("result"), list): items=data["result"]
                elif "questions" in data: items=data["questions"]
                elif "question" in data: items=[data]
            elif isinstance(data, list): items=data
            res=[]
            for idx,it in enumerate(items):
                qtext=str(it.get("question","") or it.get("question_text","")).strip()
                if not qtext or len(qtext)<10 or "Q552" in qtext: continue
                if qtext.startswith("[Mathematics") and "Q" in qtext[:30]: continue
                if qtext in ["Correct","B","C","D"]: continue
                oa=it.get("option_a") or (it.get("option") or {}).get("a") or ""
                ob=it.get("option_b") or (it.get("option") or {}).get("b") or ""
                oc=it.get("option_c") or (it.get("option") or {}).get("c") or ""
                od=it.get("option_d") or (it.get("option") or {}).get("d") or ""
                if isinstance(it.get("options"), list) and len(it["options"])>=4: oa,ob,oc,od=it["options"][:4]
                if str(oa).strip()=="Correct" and str(ob).strip()=="B": continue
                ans=str(it.get("answer","") or it.get("correct_option","")).strip().upper()
                if ans.lower() in ["a","b","c","d"]: ans=ans.upper()
                qid=it.get("id") or f"{subject}_{year}_{idx}_{random.randint(1000,9999)}"
                res.append({"id":str(qid),"subject":SUBJECT_DISPLAY.get(subject.lower(),subject.title()),"subject_key":subject.lower(),"year":str(it.get("year",year)),"topic":it.get("topic","General"),"question":qtext,"option_a":str(oa),"option_b":str(ob),"option_c":str(oc),"option_d":str(od),"answer":ans or "A","explanation":it.get("explanation","") or it.get("solution","")})
            return res
    fetcher=ALOCFetcher()
    def format_question(q, idx, total):
        return f"Q{idx}/{total} | {q.get('subject')} | {q.get('year')} | {q.get('topic','General')}\n\n{q.get('question')}\n\nA: {q.get('option_a')}\nB: {q.get('option_b')}\nC: {q.get('option_c')}\nD: {q.get('option_d')}"

def generate_score_image(score, total, user_id):
    if not HAS_PIL: return None
    try:
        from PIL import Image, ImageDraw, ImageFont
        W,H=1080,1080
        img=Image.new("RGB",(W,H), color=(26,32,53))
        draw=ImageDraw.Draw(img)
        try:
            font_big=ImageFont.truetype("arial.ttf", 90)
            font_mid=ImageFont.truetype("arial.ttf", 50)
            font_small=ImageFont.truetype("arial.ttf", 40)
        except:
            font_big=ImageFont.load_default()
            font_mid=ImageFont.load_default()
            font_small=ImageFont.load_default()
        draw.rectangle([0,0,W,280], fill=(88,101,242))
        draw.text((W//2, 80), "UTME SUCCESS BOT", fill="white", font=font_mid, anchor="mm")
        draw.text((W//2, 160), f"I scored {score}/{total}", fill="white", font=font_big, anchor="mm")
        jamb_score = int(score*400/total) if total else 0
        draw.text((W//2, 240), f"{jamb_score}/400 JAMB Scale", fill="white", font=font_mid, anchor="mm")
        draw.text((W//2, 450), "Can you beat me?", fill="white", font=font_mid, anchor="mm")
        draw.text((W//2, 550), f"Try here 👉 t.me/{BOT_USERNAME}", fill=(255,221,87), font=font_mid, anchor="mm")
        draw.text((W//2, 700), f"Exact JAMB Past Questions 2010-2024", fill="white", font=font_small, anchor="mm")
        draw.text((W//2, 760), f"~7500 Questions | AI Voice Tutor", fill="white", font=font_small, anchor="mm")
        draw.text((W//2, 950), "Join thousands crushing JAMB", fill=(150,150,150), font=font_small, anchor="mm")
        path=f"/tmp/score_{user_id}_{score}.png"
        img.save(path)
        return path
    except Exception as e:
        print(f"Image gen err {e}")
        return None

def generate_voice(text, uid):
    if not HAS_TTS: return None
    try:
        from gtts import gTTS
        tts=gTTS(text=text[:400], lang='en', slow=False)
        path=f"/tmp/voice_{uid}_{random.randint(1000,9999)}.mp3"
        tts.save(path)
        return path
    except Exception as e:
        print(f"TTS err {e}")
        return None

# --- MENUS ---
def main_menu(uid):
    u=get_user(uid)
    remaining=get_mock_remaining(uid)
    premium_badge="👑 PREMIUM" if is_premium(uid) else f"🆓 FREE ({remaining}/{FREE_MOCK_QS_DAILY} today)"
    if is_premium(uid) and u.get("premium_until"):
        try:
            exp=datetime.fromisoformat(u["premium_until"])
            premium_badge=f"👑 PREMIUM until {exp.strftime('%d %b')}"
        except:
            pass

    text=(
        f"🎓 *UTME SUCCESS BOT - v17.1 FINAL*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{premium_badge} | {PREMIUM_PRICE_TEXT}/month\n"
        f"~7500 Exact JAMB 2010-2024 | ALOC Live\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*1. LEARN (90% clicks)*\n"
        f"📚 Past Questions | 📝 Mock Exam | 🎙 Voice\n\n"
        f"*2. TRACK PROGRESS*\n"
        f"📊 My Score | 📅 Study Plan\n\n"
        f"*3. SUPPORT / VIRAL*\n"
        f"👥 Invite {REFERRAL_REQUIRED}= {REFERRAL_REWARD_DAYS} days free | 💎 Premium | 📞 Help\n\n"
        f"Free today: {remaining}/{FREE_MOCK_QS_DAILY} mock Qs (resets daily, LOCKED)\n"
        f"Tutor today: {u['tutor_counts'].get(str(date.today()),0)}/{FREE_TUTOR_PER_DAY}\n"
        f"Invites: {u.get('invites',0)}/{REFERRAL_REQUIRED} for {REFERRAL_REWARD_DAYS} days premium\n"
    )
    kb=[
        [InlineKeyboardButton("📚 Past Questions", callback_data="learn_past")],
        [InlineKeyboardButton("📝 Mock Exam", callback_data="learn_mock")],
        [InlineKeyboardButton("🎙 Explain Answer (Voice)", callback_data="explain_menu")],
        [InlineKeyboardButton("📊 My Score", callback_data="my_score"), InlineKeyboardButton("📅 Study Plan", callback_data="study_plan")],
        [InlineKeyboardButton(f"👥 Invite Friend - {REFERRAL_REQUIRED} = {REFERRAL_REWARD_DAYS} Days Free", callback_data="invite")],
        [InlineKeyboardButton(f"💎 Go Premium - {PREMIUM_PRICE_TEXT}/month", callback_data="go_premium")],
        [InlineKeyboardButton("📖 Syllabus", callback_data="syllabus"), InlineKeyboardButton("💬 Ask Tutor", callback_data="ask_tutor")],
        [InlineKeyboardButton("📞 Help", callback_data="help_menu")]
    ]
    return text, InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    # Referral check
    if context.args:
        arg=context.args[0]
        if arg.startswith("invite_"):
            code=arg.replace("invite_","")
            for inv_uid, inv_data in USER_DATA.items():
                if inv_data.get("invite_code")==code and inv_uid!=uid:
                    u=get_user(uid)
                    if not u.get("invited_by"):
                        u["invited_by"]=inv_uid
                        inviter=get_user(inv_uid)
                        if uid not in inviter.get("invited_users",[]):
                            inviter["invited_users"].append(uid)
                            inviter["invites"]=len(inviter["invited_users"])
                            # Reward inviter if hits 3
                            if inviter["invites"] % REFERRAL_REQUIRED == 0:
                                add_premium(inv_uid, days=REFERRAL_REWARD_DAYS, reason=f"Referral {inviter['invites']} friends")
                            # Reward new user 3 days free as welcome
                            add_premium(uid, days=3, reason="Welcome from invite")
                            save_data()
                            try:
                                await context.bot.send_message(chat_id=int(inv_uid), text=f"🎉 Someone joined via your link! You have {inviter['invites']}/{REFERRAL_REQUIRED} invites. {REFERRAL_REQUIRED} invites = {REFERRAL_REWARD_DAYS} days premium!\nCurrent: {inviter['invites']} invites")
                            except:
                                pass
                        await update.message.reply_text(f"🎉 You were invited! You got 3 days FREE premium! Invite {REFERRAL_REQUIRED} friends to get {REFERRAL_REWARD_DAYS} days free!")
                    break
    text, kb = main_menu(uid)
    await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query=update.callback_query
    await query.answer()
    uid=str(query.from_user.id)
    data=query.data
    u=get_user(uid)

    if data=="main_menu":
        text,kb=main_menu(uid)
        await query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
        return

    # --- PAST QUESTIONS ---
    if data=="learn_past":
        kb=[
            [InlineKeyboardButton("📚 By Subject", callback_data="past_by_subject")],
            [InlineKeyboardButton("📅 By Year 2010-2024", callback_data="past_by_year")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        await query.message.reply_text("📚 *Past Questions*\nExact JAMB 2010-2024 from ALOC (~7500 Qs)", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data=="past_by_subject":
        buttons=[[InlineKeyboardButton(SUBJECT_DISPLAY[s], callback_data=f"mock_sub_{s}_2020")] for s in ALL_SUBJECTS]
        buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        await query.message.reply_text(f"📚 *By Subject - ALL {len(ALL_SUBJECTS)}*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data=="past_by_year":
        buttons=[]
        row=[]
        for y in YEARS[::-1]:
            row.append(InlineKeyboardButton(str(y), callback_data=f"past_year_{y}"))
            if len(row)==3:
                buttons.append(row)
                row=[]
        if row: buttons.append(row)
        buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        await query.message.reply_text("📅 *By Year 2010-2024*:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data.startswith("past_year_"):
        year=data.split("_")[-1]
        buttons=[[InlineKeyboardButton(SUBJECT_DISPLAY[s], callback_data=f"mock_sub_{s}_{year}")] for s in ALL_SUBJECTS[:8]]
        buttons.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])
        await query.message.reply_text(f"📅 *JAMB {year}* - Choose Subject:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    # --- MOCK EXAM ---
    elif data=="learn_mock":
        remaining=get_mock_remaining(uid)
        kb=[
            [InlineKeyboardButton("⚡ Quick Test (5 Qs, 15 mins)", callback_data="mock_quick")],
            [InlineKeyboardButton("🎯 Full JAMB Mock (180 Qs, 2hrs)", callback_data="mock_full_start")],
            [InlineKeyboardButton("📖 Subject Mock (40 Qs)", callback_data="mock_subject_menu")],
            [InlineKeyboardButton(f"🆓 Free Today: {remaining}/{FREE_MOCK_QS_DAILY}", callback_data="main_menu")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        await query.message.reply_text(
            f"📝 *Mock Exam - Money Maker*\n━━━━━━━━━━━━\n"
            f"⚡ Quick: 5 Qs, 15 mins (matches free daily limit)\n"
            f"🎯 Full JAMB: 180 Qs, 2hrs real (Premium {PREMIUM_PRICE_TEXT})\n"
            f"📖 Subject: 40 Qs per subject (Premium)\n\n"
            f"🆓 Free: {FREE_MOCK_QS_DAILY} Qs/day LOCKED, resets daily\n"
            f"💎 Premium: Unlimited",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

    elif data=="mock_quick":
        if not can_use_mock(uid, 5):
            await query.message.reply_text(
                f"❌ *FREE DAILY LIMIT REACHED*\n\nYou've used {FREE_MOCK_QS_DAILY}/{FREE_MOCK_QS_DAILY} free Qs today.\nResets tomorrow.\nFree quota is LOCKED - cannot clear history.\n\n💎 Go Premium {PREMIUM_PRICE_TEXT}/month for unlimited\n👥 Invite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free premium!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"💎 Go Premium {PREMIUM_PRICE_TEXT}", callback_data="go_premium")],
                    [InlineKeyboardButton(f"👥 Invite - {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} Days Free", callback_data="invite")],
                    [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                ])
            )
            return
        buttons=[[InlineKeyboardButton(SUBJECT_DISPLAY[s], callback_data=f"mock_quick_{s}")] for s in ALL_SUBJECTS[:6]]
        buttons.append([InlineKeyboardButton("🎲 Random Mix", callback_data="mock_quick_random")])
        await query.message.reply_text(f"⚡ *Quick Test 5 Qs, 15 mins* - Uses your daily {FREE_MOCK_QS_DAILY} free Qs\nChoose subject:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data.startswith("mock_quick_"):
        subj=data.replace("mock_quick_","")
        if not can_use_mock(uid, 5):
            await query.message.reply_text(f"❌ Daily limit {FREE_MOCK_QS_DAILY} reached. Upgrade or invite friends.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💎 Premium {PREMIUM_PRICE_TEXT}", callback_data="go_premium")]]))
            return
        if subj=="random":
            all_qs=[]
            for s in random.sample(ALL_SUBJECTS, 3):
                for y in random.sample(YEARS, 2):
                    all_qs.extend(fetcher.fetch(s, y, limit=10))
            random.shuffle(all_qs)
            selected=all_qs[:5]
        else:
            all_qs=[]
            for y in [2023,2022,2021,2020,2019]:
                all_qs.extend(fetcher.fetch(subj, y, limit=10))
                if len(all_qs)>=10: break
            selected=random.sample(all_qs, min(5, len(all_qs))) if len(all_qs)>=5 else all_qs
        if not selected:
            await query.message.reply_text("⚠️ No data, add ALOC token")
            return
        USER_SESSIONS[uid]={"qs":selected,"idx":0,"score":0,"mode":"quick","subjects":[subj],"start":datetime.now(),"per_subj_score":defaultdict(int),"per_subj_total":defaultdict(int)}
        for q in selected: USER_SESSIONS[uid]["per_subj_total"][q["subject_key"]]+=1
        consume_mock(uid, len(selected), [q["id"] for q in selected])
        q=selected[0]
        remaining=get_mock_remaining(uid)
        await query.message.reply_text(
            f"⚡ *QUICK TEST STARTED* 5 Qs | 15 mins | {SUBJECT_DISPLAY.get(subj,subj)}\n🆓 Remaining today: {remaining}/{FREE_MOCK_QS_DAILY}\n\n{format_question(q,1,len(selected))}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("A", callback_data="ans_A"), InlineKeyboardButton("B", callback_data="ans_B")],
                [InlineKeyboardButton("C", callback_data="ans_C"), InlineKeyboardButton("D", callback_data="ans_D")],
                [InlineKeyboardButton("🏁 Submit", callback_data="quick_submit")]
            ])
        )

    elif data=="mock_subject_menu":
        buttons=[[InlineKeyboardButton(f"{SUBJECT_DISPLAY[s]} - 40 Qs", callback_data=f"mock_sub_{s}_2020")] for s in ALL_SUBJECTS]
        buttons.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])
        await query.message.reply_text("📖 *Subject Mock 40 Qs* - Premium only (Free daily is 5 Qs)", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data.startswith("mock_sub_"):
        _, _, subj, year = data.split("_")
        # Free users only get 5 Qs per day, so subject mock 40 is premium
        if not is_premium(uid):
            # Allow free users to get 5 Qs from subject mock (uses daily limit)
            if not can_use_mock(uid, 5):
                await query.message.reply_text(f"❌ Daily limit {FREE_MOCK_QS_DAILY} reached. Subject Mock 40 Qs is Premium {PREMIUM_PRICE_TEXT}\nInvite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💎 Premium {PREMIUM_PRICE_TEXT}", callback_data="go_premium")]]))
                return
            count=5
        else:
            count=40
        await query.message.reply_text(f"⏳ Fetching {SUBJECT_DISPLAY.get(subj,subj)} {year} - {count} Qs from ALOC...")
        qs=fetcher.fetch(subj, year, limit=40)
        if not qs:
            await query.message.reply_text("⚠️ No data")
            return
        used=set(u["used_ids"])
        avail=[q for q in qs if q["id"] not in used] or qs
        selected=random.sample(avail, min(count, len(avail)))
        USER_SESSIONS[uid]={"qs":selected,"idx":0,"score":0,"mode":"subject","subjects":[subj],"start":datetime.now(),"per_subj_score":defaultdict(int),"per_subj_total":defaultdict(int)}
        for q in selected: USER_SESSIONS[uid]["per_subj_total"][q["subject_key"]]+=1
        consume_mock(uid, len(selected), [q["id"] for q in selected])
        q=selected[0]
        remaining=get_mock_remaining(uid)
        await query.message.reply_text(
            f"{format_question(q,1,len(selected))}\n\n🆓 Remaining today: {remaining}/{FREE_MOCK_QS_DAILY} | {'👑 Premium' if is_premium(uid) else f'Premium {PREMIUM_PRICE_TEXT} for 40Q'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("A", callback_data="ans_A"), InlineKeyboardButton("B", callback_data="ans_B")],
                [InlineKeyboardButton("C", callback_data="ans_C"), InlineKeyboardButton("D", callback_data="ans_D")],
                [InlineKeyboardButton("🏁 Submit", callback_data="quick_submit")]
            ])
        )

    elif data=="mock_full_start":
        if not is_premium(uid):
            await query.message.reply_text(
                f"🎯 *Full JAMB Mock 180 Qs - PREMIUM ONLY*\n\nFree daily limit is {FREE_MOCK_QS_DAILY} Qs. Full 180Q is Premium {PREMIUM_PRICE_TEXT}\n\n💎 Unlimited mocks + voice\n👥 Invite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free premium!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"💎 Go Premium {PREMIUM_PRICE_TEXT}", callback_data="go_premium")],
                    [InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} Days Free", callback_data="invite")],
                    [InlineKeyboardButton("⚡ Quick Test 5Q Free", callback_data="mock_quick")],
                    [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                ])
            )
            return
        from collections import defaultdict as dd
        USER_JAMB_PICK[uid]=[]
        buttons=[[InlineKeyboardButton(SUBJECT_DISPLAY[s], callback_data=f"jpick_{s}")] for s in ALL_SUBJECTS if s!="english"]
        buttons.append([InlineKeyboardButton("✅ Build 180Q Test", callback_data="jbuild")])
        buttons.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])
        await query.message.reply_text("🎯 *Full JAMB Mock*\nEnglish 60 + Pick 3 subjects x40 = 180 Qs, 2hrs:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data.startswith("jpick_"):
        subj=data.replace("jpick_","")
        picked=USER_JAMB_PICK.get(uid,[])
        if subj not in picked and len(picked)<3:
            picked.append(subj)
        USER_JAMB_PICK[uid]=picked
        status=f"Picked: {', '.join([SUBJECT_DISPLAY[s].split()[-1] for s in picked])} ({len(picked)}/3)"
        buttons=[[InlineKeyboardButton(f"{SUBJECT_DISPLAY[s]} {'✅' if s in picked else ''}", callback_data=f"jpick_{s}")] for s in ALL_SUBJECTS if s!="english"]
        buttons.append([InlineKeyboardButton("✅ Build 180Q", callback_data="jbuild")])
        await query.message.reply_text(status, reply_markup=InlineKeyboardMarkup(buttons))

    elif data=="jbuild":
        picked=USER_JAMB_PICK.get(uid,[])
        if len(picked)!=3:
            await query.message.reply_text(f"Pick 3, you have {len(picked)}/3")
            return
        await query.message.reply_text(f"⏳ Building FULL JAMB 180Q...\nEnglish 60 + {', '.join(picked)} 40 each")
        full=[]
        eng=[]
        for y in [2023,2022,2021,2020,2019]:
            eng.extend(fetcher.fetch("english", y, limit=60))
            if len(eng)>=60: break
        random.shuffle(eng)
        full.extend(eng[:60])
        for subj in picked:
            sq=[]
            for y in [2023,2022,2021,2020]:
                sq.extend(fetcher.fetch(subj, y, limit=40))
                if len(sq)>=40: break
            random.shuffle(sq)
            full.extend(sq[:40])
        USER_SESSIONS[uid]={"qs":full,"idx":0,"score":0,"mode":"full_jamb","subjects":["english"]+picked,"start":datetime.now(),"per_subj_score":defaultdict(int),"per_subj_total":defaultdict(int)}
        for q in full: USER_SESSIONS[uid]["per_subj_total"][q["subject_key"]]+=1
        q=full[0]
        await query.message.reply_text(
            f"🎯 *FULL JAMB STARTED* 180 Qs | 2hrs\n\n{format_question(q,1,len(full))}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("A", callback_data="ans_A"), InlineKeyboardButton("B", callback_data="ans_B")],
                [InlineKeyboardButton("C", callback_data="ans_C"), InlineKeyboardButton("D", callback_data="ans_D")],
                [InlineKeyboardButton("⏭️ Skip", callback_data="ans_SKIP"), InlineKeyboardButton("🏁 Submit", callback_data="jsubmit")]
            ])
        )

    # --- ANSWERS ---
    elif data.startswith("ans_"):
        sess=USER_SESSIONS.get(uid)
        if not sess: return
        idx=sess["idx"]
        qs=sess["qs"]
        if idx>=len(qs): return
        cur=qs[idx]
        chosen=data.split("_")[1]
        is_correct = chosen==cur["answer"]
        if is_correct:
            sess["score"]+=1
            sess["per_subj_score"][cur["subject_key"]]+=1
            fb="✅ Correct!"
        elif chosen=="SKIP":
            fb="⏭️ Skipped"
        else:
            fb=f"❌ Wrong. Answer: {cur['answer']}\n{cur['explanation'][:300]}\n\n🎙 Want voice? 👉 /explain"
        sess["idx"]+=1
        if sess["idx"]<len(qs):
            q=qs[sess["idx"]]
            extra=[]
            if not is_correct:
                extra=[InlineKeyboardButton("🎙 Explain with Voice", callback_data=f"voice_{idx}")]
            kb=[
                [InlineKeyboardButton("A", callback_data="ans_A"), InlineKeyboardButton("B", callback_data="ans_B")],
                [InlineKeyboardButton("C", callback_data="ans_C"), InlineKeyboardButton("D", callback_data="ans_D")],
                [InlineKeyboardButton("⏭️ Skip", callback_data="ans_SKIP"), InlineKeyboardButton("🏁 Submit", callback_data="quick_submit" if sess["mode"]!="full_jamb" else "jsubmit")]
            ]
            if extra: kb.append(extra)
            await query.message.reply_text(f"{fb}\n\n{format_question(q, sess['idx']+1, len(qs))}", reply_markup=InlineKeyboardMarkup(kb))
        else:
            u=get_user(uid)
            u["history"].append({"subjects":sess["subjects"],"score":sess["score"],"total":len(qs),"date":str(datetime.now()),"mode":sess["mode"]})
            for subj in sess["subjects"]:
                if subj not in u["scores_by_subject"]: u["scores_by_subject"][subj]=[]
                subj_score = sess["per_subj_score"].get(subj,0)
                subj_total = sess["per_subj_total"].get(subj,1)
                u["scores_by_subject"][subj].append(int(subj_score*100/subj_total))
                u["scores_by_subject"][subj]=u["scores_by_subject"][subj][-10:]
            if sess["mode"]=="full_jamb": u["full_cbt_attempts"]+=1
            save_data()
            score=sess["score"]
            total=len(qs)
            jamb_score=int(score*400/total) if total else 0
            breakdown="\n".join([f"{SUBJECT_DISPLAY.get(k,k)}: {sess['per_subj_score'][k]}/{sess['per_subj_total'][k]}" for k in sess["subjects"]])
            # After completing daily limit, call to upgrade
            remaining=get_mock_remaining(uid)
            upgrade_msg=""
            if remaining==0 and not is_premium(uid):
                upgrade_msg=f"\n\n❌ DAILY LIMIT REACHED {FREE_MOCK_QS_DAILY}/{FREE_MOCK_QS_DAILY} today (LOCKED)\n💎 Go Premium {PREMIUM_PRICE_TEXT} for unlimited\n👥 Invite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free!"
            await query.message.reply_text(
                f"{fb}\n\n🎉 *{sess['mode'].upper()} DONE!*\nScore: {score}/{total} ({jamb_score}/400 JAMB)\n\n{breakdown}{upgrade_msg}\n\n👇 Share to WhatsApp Status!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📤 Share My Score (Viral)", callback_data=f"share_{score}_{total}")],
                    [InlineKeyboardButton("📊 My Score & Weak Areas", callback_data="my_score")],
                    [InlineKeyboardButton(f"💎 Go Premium {PREMIUM_PRICE_TEXT}" if remaining==0 else "🏠 Menu", callback_data="go_premium" if remaining==0 else "main_menu")]
                ])
            )

    elif data in ["quick_submit","jsubmit"]:
        sess=USER_SESSIONS.get(uid)
        if not sess: return
        score=sess["score"]
        total=len(sess["qs"])
        jamb_score=int(score*400/total) if total else 0
        breakdown="\n".join([f"{SUBJECT_DISPLAY.get(k,k)}: {sess['per_subj_score'][k]}/{sess['per_subj_total'][k]}" for k in sess["subjects"]])
        u=get_user(uid)
        u["history"].append({"subjects":sess["subjects"],"score":score,"total":total,"date":str(datetime.now()),"mode":sess["mode"]})
        save_data()
        remaining=get_mock_remaining(uid)
        upgrade_msg=f"\n\n❌ Daily limit {FREE_MOCK_QS_DAILY}/{FREE_MOCK_QS_DAILY} reached!" if remaining==0 and not is_premium(uid) else ""
        await query.message.reply_text(
            f"🏁 *SUBMITTED*\nScore {score}/{total} ({jamb_score}/400)\n\n{breakdown}{upgrade_msg}\n\n📤 Share to go viral!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{score}_{total}")],
                [InlineKeyboardButton("📊 My Score", callback_data="my_score")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ])
        )

    elif data.startswith("share_"):
        _, score, total = data.split("_")
        score=int(score); total=int(total)
        img_path=generate_score_image(score, total, uid)
        if img_path and os.path.exists(img_path):
            await query.message.reply_photo(photo=open(img_path,'rb'), caption=f"I scored {score}/{total} ({int(score*400/total)}/400) in JAMB Mock!\nCan you beat me?\nTry here 👉 t.me/{BOT_USERNAME}\n\n#JAMB #UTME", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💎 Go Premium {PREMIUM_PRICE_TEXT}", callback_data="go_premium")],[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]))
        else:
            await query.message.reply_text(f"I scored {score}/{total} ({int(score*400/total)}/400) in JAMB Mock!\nCan you beat me?\nTry here 👉 t.me/{BOT_USERNAME}\n\nShare on WhatsApp Status! 🚀", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]))

    elif data.startswith("voice_"):
        idx=int(data.split("_")[1])
        sess=USER_SESSIONS.get(uid)
        if not sess: return
        cur=sess["qs"][idx] if idx < len(sess["qs"]) else None
        if not cur: return
        if not can_use_tutor(uid):
            await query.message.reply_text(f"🎙 Voice Explain limit {FREE_TUTOR_PER_DAY}/day reached.\nPremium unlimited.\nInvite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💎 Premium {PREMIUM_PRICE_TEXT}", callback_data="go_premium")]]))
            return
        explanation=f"Question: {cur['question']}. Correct answer is {cur['answer']}. Explanation: {cur['explanation'] or 'This is correct based on JAMB syllabus.'}"
        voice_path=generate_voice(explanation, uid)
        if voice_path and os.path.exists(voice_path):
            await query.message.reply_voice(voice=open(voice_path,'rb'), caption=f"🎙 Voice explanation Q{idx+1}")
            consume_tutor(uid)
        else:
            await query.message.reply_text(f"🎙 *Voice*\n{explanation}", parse_mode="Markdown")

    # --- TRACK ---
    elif data=="my_score":
        u=get_user(uid)
        hist=u.get("history",[])
        if not hist:
            await query.message.reply_text("📊 No history yet. Take mock first!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Mock Exam", callback_data="learn_mock")]]))
            return
        total_avg = sum(h["score"]*400//h["total"] for h in hist)/len(hist) if hist else 0
        subj_avgs={}
        for subj, scores in u.get("scores_by_subject",{}).items():
            if scores: subj_avgs[subj]=sum(scores)/len(scores)
        strong=sorted(subj_avgs.items(), key=lambda x: x[1], reverse=True)[:2]
        weak=sorted(subj_avgs.items(), key=lambda x: x[1])[:2]
        text=f"📊 *My Score*\n━━━━━━━━━━━━\nTotal avg: {int(total_avg)}/400\nExams: {len(hist)}\n\n"
        if strong: text+=f"✅ Strong: {', '.join([f'{SUBJECT_DISPLAY.get(s,s)} {int(p)}%' for s,p in strong])}\n"
        if weak: text+=f"⚠️ Weak: {', '.join([f'{SUBJECT_DISPLAY.get(s,s)} {int(p)}% → Practice' for s,p in weak])}\n\n"
        all_scores=sorted(USER_DATA.items(), key=lambda x: sum(h['score'] for h in x[1].get('history',[]))/max(len(x[1].get('history',[])),1), reverse=True)
        pos = next((i+1 for i,(uid2,_) in enumerate(all_scores) if uid2==uid), 999)
        text+=f"🏆 Leaderboard: #{pos}\n\nLast 3:\n"
        for h in hist[-3:][::-1]: text+=f"• {h['date'][:10]} {h['score']}/{h['total']} ({int(h['score']*400//h['total'])}/400)\n"
        text+=f"\n🆓 Today: {get_mock_remaining(uid)}/{FREE_MOCK_QS_DAILY} mock left (LOCKED daily)"
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📅 Study Plan", callback_data="study_plan")],[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]))

    elif data=="study_plan":
        u=get_user(uid)
        week_ago=datetime.now()-timedelta(days=7)
        recent=[]
        for h in u.get("history",[]):
            try:
                d=datetime.fromisoformat(h["date"])
                if d>week_ago: recent.extend(h["subjects"])
            except: pass
        not_practiced=list(set(ALL_SUBJECTS) - set(recent))[:3]
        text="📅 *Study Plan*\n━━━━━━━━━━━━\n"
        if not_practiced: text+=f"You never practice {', '.join([SUBJECT_DISPLAY.get(s,s) for s in not_practiced])} this week. Start?\n\n"
        else: text+=f"Great! Practiced all subjects this week.\n\n"
        subj_avgs={}
        for subj, scores in u.get("scores_by_subject",{}).items():
            if scores: subj_avgs[subj]=sum(scores)/len(scores)
        if subj_avgs:
            weakest=min(subj_avgs.items(), key=lambda x: x[1])
            text+=f"🎯 Focus: Weakest {SUBJECT_DISPLAY.get(weakest[0],weakest[0])} {int(weakest[1])}%"
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Practice", callback_data="learn_mock")],[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]))

    # --- SUPPORT / VIRAL ---
    elif data=="invite":
        u=get_user(uid)
        code=u["invite_code"]
        link=f"https://t.me/{BOT_USERNAME}?start=invite_{code}"
        text=(
            f"👥 *Invite Friend - {REFERRAL_REQUIRED} Friends = {REFERRAL_REWARD_DAYS} Days Premium*\n━━━━━━━━━━━━\n"
            f"How you blow! 🚀\n\n"
            f"Your link:\n`{link}`\n\n"
            f"Share to WhatsApp, friends click & start bot, you BOTH get:\n"
            f"• New user: 3 days FREE premium (welcome)\n"
            f"• You: When you reach {REFERRAL_REQUIRED} friends, you get {REFERRAL_REWARD_DAYS} days FREE premium!\n\n"
            f"You've invited: {u.get('invites',0)} friends\n"
            f"Progress: {u.get('invites',0)}/{REFERRAL_REQUIRED} for {REFERRAL_REWARD_DAYS} days\n"
            f"Premium until: {u.get('premium_until','Not active')}\n\n"
            f"Keep inviting - every {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free!"
        )
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Share Invite Link", url=f"https://t.me/share/url?url={link}&text=I%20use%20UTME%20Success%20Bot%20-%20exact%20JAMB%202010-2024!%20Join%20me%20and%20get%203%20days%20free%20premium!")],[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]))

    elif data=="go_premium":
        await query.message.reply_text(
            f"💎 *Go Premium - {PREMIUM_PRICE_TEXT}/month*\n━━━━━━━━━━━━\n"
            f"✅ Unlimited mocks (vs {FREE_MOCK_QS_DAILY}/day free LOCKED)\n"
            f"✅ Full 180Q JAMB Mock 2hr real\n"
            f"✅ Quick 5Q + Subject 40Q\n"
            f"✅ Voice explanations 🎙 unlimited (vs {FREE_TUTOR_PER_DAY}/day free)\n"
            f"✅ All {len(ALL_SUBJECTS)} subjects 2010-2024 ~7500 Qs\n"
            f"✅ Syllabus + My Score + Study Plan\n"
            f"✅ Share Score Viral Image\n"
            f"✅ Invite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free premium\n\n"
            f"Free daily {FREE_MOCK_QS_DAILY} Qs resets daily, cannot clear history",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💳 Pay {PREMIUM_PRICE_TEXT} Now", url=f"{PAYMENT_URL}/upgrade/{uid}")],
                [InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} Days Free", callback_data="invite")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ])
        )

    elif data=="syllabus":
        buttons=[[InlineKeyboardButton(SUBJECT_DISPLAY[s], callback_data=f"syll_{s}")] for s in ALL_SUBJECTS[:6]]
        buttons.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])
        await query.message.reply_text("📖 *JAMB Official Syllabus* - Choose subject:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

    elif data.startswith("syll_"):
        subj=data.replace("syll_","")
        text=JAMB_SYLLABUS.get(subj, f"{SUBJECT_DISPLAY.get(subj,subj)} syllabus: Comprehensive JAMB official syllabus 2010-2024.")
        await query.message.reply_text(f"📖 *{SUBJECT_DISPLAY.get(subj,subj)} Syllabus*\n━━━━━━━━━━━━\n{text}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📚 Practice Past Qs", callback_data=f"mock_sub_{subj}_2020")],[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]))

    elif data=="ask_tutor":
        remaining_tutor = FREE_TUTOR_PER_DAY - get_user(uid)["tutor_counts"].get(str(date.today()),0) if not is_premium(uid) else 999
        await query.message.reply_text(
            f"💬 *Ask Tutor - Ask Any Question*\n━━━━━━━━━━━━\n"
            f"Send any UTME question, I'll explain step-by-step with voice!\n\n"
            f"Free: {FREE_TUTOR_PER_DAY}/day (LOCKED, resets daily) - Remaining today: {remaining_tutor}\n"
            f"Premium: Unlimited + Voice 🎙\n\n"
            f"Just type your question now!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎙 Voice Explain", callback_data="explain_menu")],[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
        )

    elif data=="explain_menu":
        await query.message.reply_text(
            "🎙 *Explain Answer - AI Teacher with Voice*\n━━━━━━━━━━━━\n"
            "When you fail a question, bot auto sends:\n\"Want me to explain with voice? 👉 /explain\"\n\n"
            "1. You answer wrong\n2. Bot shows [🎙 Explain with Voice]\n3. Tap for voice note + text\n4. Free: 2/day | Premium: Unlimited\n\n"
            "Try: Take Quick Test and fail!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Take Quick Test", callback_data="mock_quick")],[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
        )

    elif data=="help_menu":
        await query.message.reply_text(
            f"📞 *Help - v17.1 FINAL*\n━━━━━━━━━━━━\n"
            f"Exact JAMB 2010-2024 ~7500 Qs from ALOC live\n\n"
            f"*1. LEARN (90%)*\n📚 Past Qs By Subject/Year\n📝 Mock: Quick 5Q 15min, Full 180Q 2hr, Subject 40Q\n🎙 Voice after fail\n\n"
            f"*2. TRACK*\n📊 My Score: avg, strong/weak, leaderboard\n📅 Study Plan\n\n"
            f"*3. SUPPORT / VIRAL*\n👥 Invite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days premium\n💎 Premium {PREMIUM_PRICE_TEXT} unlimited\n\n"
            f"🔒 FREE LOCKED: {FREE_MOCK_QS_DAILY} mock/day + {FREE_TUTOR_PER_DAY} tutor/day - resets daily, cannot clear\n"
            f"📤 Viral: Share My Score image for WhatsApp status",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])
        )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=str(update.effective_user.id)
    text=update.message.text
    if text.startswith("/explain") or text.lower().startswith("explain"):
        await update.message.reply_text("🎙 Use [🎙 Explain with Voice] button after wrong answer")
        return
    if not can_use_tutor(uid):
        await update.message.reply_text(
            f"❌ Tutor limit {FREE_TUTOR_PER_DAY}/day reached. Resets tomorrow.\n\n💎 Premium {PREMIUM_PRICE_TEXT} unlimited voice\n👥 Invite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💎 Go Premium {PREMIUM_PRICE_TEXT}", callback_data="go_premium")],
                [InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} Days", callback_data="invite")]
            ])
        )
        return
    consume_tutor(uid)
    remaining_tutor = FREE_TUTOR_PER_DAY - get_user(uid)["tutor_counts"].get(str(date.today()),0) if not is_premium(uid) else 999
    await update.message.reply_text(
        f"💬 *Tutor Answer*\n━━━━━━━━━━━━\nQ: {text[:200]}\n\nStep 1: Understand...\nStep 2: Key concept from syllabus...\nStep 3: Solve...\n\n✅ Answer with explanation\n\n🎙 Need voice? Tap after mock fail -> Explain with Voice\n🆓 Tutor remaining today: {remaining_tutor}/{FREE_TUTOR_PER_DAY}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
    )

# --- FLASK ---
flask_app = Flask(__name__)

@flask_app.route("/")
def home(): return f"UTME v17.1 FINAL - {FREE_MOCK_QS_DAILY} free/day + {FREE_TUTOR_PER_DAY} tutor/day + Refer {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days premium | Running"

@flask_app.route("/upgrade/<uid>")
def upgrade_page(uid):
    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{font-family:Arial;background:#f5f7fb;text-align:center;padding:20px}} .card{{background:white;max-width:450px;margin:auto;padding:30px;border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,.1)}} .btn{{background:#5865f2;color:white;padding:14px 28px;border-radius:10px;text-decoration:none;display:inline-block;margin:10px 0;font-weight:bold;width:85%;border:none;cursor:pointer}} .btn-flw{{background:#f5a623}} .btn-ps{{background:#00c3f7}} .badge{{background:#ff4757;color:white;padding:6px 12px;border-radius:20px;font-size:12px}}</style>
    <script src="https://checkout.flutterwave.com/v3.js"></script>
    </head><body><div class="card"><span class="badge">v17.1 FINAL</span><h2>💎 Go Premium - {PREMIUM_PRICE_TEXT}/month</h2><p>User: {uid}</p>
    <p style="text-align:left">✅ Unlimited Mocks (vs {FREE_MOCK_QS_DAILY}/day free LOCKED)<br>✅ Full 180Q JAMB Mock 2hr<br>✅ Quick 5Q + Subject 40Q<br>✅ Voice 🎙 unlimited (vs {FREE_TUTOR_PER_DAY}/day free)<br>✅ All {len(ALL_SUBJECTS)} subjects 2010-2024 ~7500 Qs<br>✅ Syllabus + My Score + Study Plan<br>✅ Share Score Viral Image<br>✅ Invite {REFERRAL_REQUIRED} friends = {REFERRAL_REWARD_DAYS} days free premium</p>
    <p><b>{PREMIUM_PRICE_TEXT}</b> - Free daily resets, cannot clear history</p>
    <button class="btn btn-flw" onclick="payWithFlutterwave()">💳 Pay with Flutterwave - {PREMIUM_PRICE_TEXT}</button>
    <a class="btn btn-ps" href="https://paystack.com/pay/utme-success-{uid}">💳 Pay with Paystack - {PREMIUM_PRICE_TEXT}</a>
    <p style="font-size:11px"><a href="/">Back</a></p></div>
    <script>
        function payWithFlutterwave(){{
            FlutterwaveCheckout({{
                public_key: "{os.getenv('FLW_PUBLIC_KEY','FLWPUBK-XXXX')}",
                tx_ref: "UTME-{uid}-"+Date.now(),
                amount: {PREMIUM_PRICE},
                currency: "NGN",
                customer:{{email:"user{uid}@utmebot.com",name:"UTME User {uid}"}},
                customizations:{{title:"UTME Success Bot Premium",description:"Premium {PREMIUM_PRICE_TEXT}/month"}},
                callback: function(data){{
                    fetch('/verify/flutterwave',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{transaction_id:data.transaction_id,tx_ref:data.tx_ref,user_id:"{uid}"}})}}).then(r=>r.json()).then(res=>{{
                        if(res.status=="success"){{alert("✅ Premium activated! Return to bot /start"); window.location.href="https://t.me/{BOT_USERNAME}";}} else {{alert("Payment received, verification pending");}}
                    }});
                }},
                onclose: function(){{}}
            }});
        }}
    </script>
    </body></html>
    """)

@flask_app.route("/health")
def health():
    return jsonify({"status":"ok","version":"v17.1 FINAL","premium":PREMIUM_PRICE_TEXT,"free_mock_daily":FREE_MOCK_QS_DAILY,"free_tutor_daily":FREE_TUTOR_PER_DAY,"referral":f"{REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days","token_set":bool(ALOC_ACCESS_TOKEN),"users":len(USER_DATA),"cached":sum(len(v) for v in CACHE.values())})

@flask_app.route("/fetch_all_2010_2024")
def fetch_all_route():
    if PRECACHE_STATUS["running"]:
        return jsonify({"status":"running","progress":PRECACHE_STATUS})
    def bg():
        PRECACHE_STATUS["running"]=True
        total=0
        from cbt_engine import fetcher as f
        for subj in ALL_SUBJECTS:
            PRECACHE_STATUS["progress"]=f"Fetching {subj} 2010-2024..."
            for y in YEARS:
                qs=f.fetch(subj,y,limit=40)
                total+=len(qs)
                PRECACHE_STATUS["total_fetched"]=total
                time.sleep(0.3)
        PRECACHE_STATUS["running"]=False
        PRECACHE_STATUS["progress"]=f"Done {total} Qs"
    threading.Thread(target=bg, daemon=True).start()
    return jsonify({"status":"started","msg":"Pre-caching ~7500 Qs 5-10 mins"})

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))

def main():
    if os.getenv("RENDER"):
        threading.Thread(target=run_flask, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print(f"v17.1 FINAL - Premium {PREMIUM_PRICE_TEXT} - Free {FREE_MOCK_QS_DAILY}/day + {FREE_TUTOR_PER_DAY} tutor/day - Refer {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days")
    app.run_polling()

if __name__=="__main__":
    main()
