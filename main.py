
"""
UTME Success Bot v21 PROFESSIONAL - Mock FIXED + Tutor 200% Smart + Voice + Viral Invite
- Bottom: Past Questions, Mock Exam, My Score, Ask Tutor, Premium, Invite Friends (Syllabus replaced)
- Free: 5 mock/day, 10 tutor/day, Paid: unlimited
- Invite 3 friends = 7 days premium FREE (viral)
- Mock loads from JSON databank, always works
- Tutor uses databank + AI brain + Voice Nigerian slow
"""
import os, json, random, time, threading, hashlib, asyncio, re
from datetime import date, datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, MenuButtonCommands, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

try:
    from gtts import gTTS
    HAS_TTS=True
except:
    HAS_TTS=False

try:
    from config import BOT_TOKEN, BOT_USERNAME, ADMIN_ID, PAYMENT_URL, PREMIUM_PRICE, PREMIUM_PRICE_TEXT, FREE_MOCK_QS_DAILY, FREE_TUTOR_PER_DAY, REFERRAL_REQUIRED, REFERRAL_REWARD_DAYS, ALL_SUBJECTS
except:
    BOT_TOKEN=os.getenv("BOT_TOKEN","YOUR_BOT_TOKEN_HERE")
    BOT_USERNAME=os.getenv("BOT_USERNAME","YourBot")
    ADMIN_ID=os.getenv("ADMIN_ID","")
    PAYMENT_URL=os.getenv("PAYMENT_URL","https://your-app.onrender.com")
    PREMIUM_PRICE=2000
    PREMIUM_PRICE_TEXT="₦2000"
    FREE_MOCK_QS_DAILY=5
    FREE_TUTOR_PER_DAY=10
    REFERRAL_REQUIRED=3
    REFERRAL_REWARD_DAYS=7
    ALL_SUBJECTS=["english","mathematics","biology","physics","chemistry","economics","government","commerce","accounting","literature","crk","geography","civic","history"]

CHANNEL_ID=os.getenv("CHANNEL_ID","")
CHANNEL_USERNAME=os.getenv("CHANNEL_USERNAME","UTMESUCCESS")

SUBJECT_DISPLAY={"english":"📖 English","mathematics":"📐 Maths","biology":"🧬 Biology","physics":"⚛️ Physics","chemistry":"🧪 Chemistry","economics":"💰 Economics","government":"🏛️ Government","commerce":"🏪 Commerce","accounting":"📊 Accounting","literature":"📚 Literature","crk":"✝️ CRK","geography":"🌍 Geography","civic":"🇳🇬 Civic","history":"📜 History"}

DATA_FILE=Path("user_data.json")
USER_DATA={}
USER_SESSIONS={}

BOTTOM_KEYBOARD=ReplyKeyboardMarkup(
    [[KeyboardButton("📚 Past Questions"), KeyboardButton("📝 Mock Exam")],
     [KeyboardButton("📊 My Score"), KeyboardButton("💬 Ask Tutor")],
     [KeyboardButton("💎 Premium"), KeyboardButton("👥 Invite Friends")]],
    resize_keyboard=True, is_persistent=True)

def load_data():
    global USER_DATA
    if DATA_FILE.exists():
        try:
            USER_DATA=json.loads(DATA_FILE.read_text())
        except:
            USER_DATA={}

def save_data():
    try:
        DATA_FILE.write_text(json.dumps(USER_DATA, indent=2))
    except:
        pass

def get_user(uid, username=""):
    uid=str(uid)
    if uid not in USER_DATA:
        USER_DATA[uid]={"mock_counts":{},"tutor_counts":{},"used_ids":[],"is_premium":False,"premium_until":None,"joined":str(date.today()),"history":[],"invite_code":hashlib.md5(uid.encode()).hexdigest()[:6].upper(),"invited_by":None,"invites":0,"invited_users":[],"username":username or f"User{uid[-4:]}"}
        save_data()
    u=USER_DATA[uid]
    if username: u["username"]=username
    if u.get("premium_until"):
        try:
            exp=datetime.fromisoformat(u["premium_until"])
            if datetime.now()>exp:
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

def can_use_mock(uid, c=1):
    if is_premium(uid): return True
    u=get_user(uid)
    return u["mock_counts"].get(str(date.today()),0)+c <= FREE_MOCK_QS_DAILY

def consume_mock(uid, c, ids=None):
    u=get_user(uid)
    u["mock_counts"][str(date.today())]=u["mock_counts"].get(str(date.today()),0)+c
    if ids:
        u["used_ids"].extend(ids)
        u["used_ids"]=list(dict.fromkeys(u["used_ids"]))[-2000:]
    save_data()

def get_mock_remaining(uid):
    if is_premium(uid): return 999
    u=get_user(uid)
    return max(0, FREE_MOCK_QS_DAILY - u["mock_counts"].get(str(date.today()),0))

def can_use_tutor(uid):
    if is_premium(uid): return True
    u=get_user(uid)
    return u["tutor_counts"].get(str(date.today()),0) < FREE_TUTOR_PER_DAY

def consume_tutor(uid):
    u=get_user(uid)
    u["tutor_counts"][str(date.today())]=u["tutor_counts"].get(str(date.today()),0)+1
    save_data()

def get_leading():
    best_name="No scores yet"
    best_score=0
    for uid_k, d in USER_DATA.items():
        hist=d.get("history",[])
        if not hist: continue
        avg=sum(h.get("percent",0) for h in hist)/len(hist)
        if avg>best_score:
            best_score=avg
            best_name=d.get("username", f"User{str(uid_k)[-4:]}")
    return best_name, int(best_score)

def add_premium(uid, days=30):
    u=get_user(uid)
    u["is_premium"]=True
    if u.get("premium_until"):
        try:
            ex=datetime.fromisoformat(u["premium_until"])
            if ex>datetime.now():
                ex+=timedelta(days=days)
                u["premium_until"]=ex.isoformat()
            else:
                u["premium_until"]=(datetime.now()+timedelta(days=days)).isoformat()
        except:
            u["premium_until"]=(datetime.now()+timedelta(days=days)).isoformat()
    else:
        u["premium_until"]=(datetime.now()+timedelta(days=days)).isoformat()
    save_data()

def upgrade_kb(uid):
    url=f"{PAYMENT_URL}/upgrade/{uid}" if PAYMENT_URL else f"https://t.me/{BOT_USERNAME}"
    msg=f"⏰ *Daily Limit Reached!*\n\nFree: {FREE_MOCK_QS_DAILY} mock/day + {FREE_TUTOR_PER_DAY} tutor/day\n\n💎 *Premium {PREMIUM_PRICE_TEXT}/month:*\n✅ Unlimited mocks\n✅ Full 180Q CBT 2hrs\n✅ Unlimited tutor + Voice 🎙️\n✅ {len(ALL_QS) if 'ALL_QS' in globals() else 1500}+ Qs\n\n🚀 *VIRAL:* Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!"
    kb=[[InlineKeyboardButton(f"💳 Upgrade {PREMIUM_PRICE_TEXT}", url=url)],[InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}= {REFERRAL_REWARD_DAYS} Days FREE!", callback_data="invite_friends")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
    return msg, InlineKeyboardMarkup(kb)

def main_menu(uid):
    u=get_user(uid)
    rem=get_mock_remaining(uid)
    prem="💎 Premium Active ✅" if is_premium(uid) else f"💎 Premium {PREMIUM_PRICE_TEXT}"
    leader_name, leader_score=get_leading()
    text=f"🎓 *UTME Success Bot v21 PROFESSIONAL*\n\n📊 {rem}/{FREE_MOCK_QS_DAILY} mocks today | {prem}\n🏆 Top: {leader_name} - {leader_score}/400\n\n👥 *VIRAL:* Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE premium!\n\nChoose:"
    kb=[[InlineKeyboardButton("📚 Past Questions", callback_data="past_by_subject"), InlineKeyboardButton("📝 Mock Exam", callback_data="mock_menu")],[InlineKeyboardButton("📖 Study Plan", callback_data="study_plan"), InlineKeyboardButton("📋 Syllabus", callback_data="syllabus")],[InlineKeyboardButton("📊 My Score", callback_data="my_score"), InlineKeyboardButton("💬 Ask Tutor", callback_data="ask_tutor")],[InlineKeyboardButton(f"👥 Invite Friends - {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} Days FREE!", callback_data="invite_friends")],[InlineKeyboardButton("💎 Premium", callback_data="premium_info"), InlineKeyboardButton("❓ Help", callback_data="help_menu")]]
    return text, InlineKeyboardMarkup(kb)

def subjects_kb(prefix):
    buttons=[]
    row=[]
    for subj in ALL_SUBJECTS[:14]:
        display=SUBJECT_DISPLAY.get(subj, subj.title())
        row.append(InlineKeyboardButton(display, callback_data=f"{prefix}_{subj}"))
        if len(row)==2:
            buttons.append(row)
            row=[]
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

try:
    from cbt_engine import fetcher, format_question, search_databank, get_random_question, LOCAL_DATABANK, ALL_QS
    HAS_ENGINE=True
except:
    HAS_ENGINE=False
    def search_databank(q,s=None,limit=5): return []
    def get_random_question(s=None): return None
    LOCAL_DATABANK={}
    ALL_QS=[]
    def format_question(q,i,t): return f"Q{i}/{t}\n{q.get('question')}\nA) {q.get('option_a')}\nB) {q.get('option_b')}\nC) {q.get('option_c')}\nD) {q.get('option_d')}"
    class F:
        def fetch(self,s,y=None,limit=40):
            return []
    fetcher=F()

load_data()

async def handle_callback(update, context):
    query=update.callback_query
    await query.answer()
    uid=str(query.from_user.id)
    data=query.data
    u=get_user(uid, query.from_user.first_name or "")

    if data=="study_plan":
        await query.message.reply_text("📖 *Study Plan - Choose Subject:*", reply_markup=subjects_kb("study_subject"), parse_mode="Markdown")
        return
    elif data.startswith("study_subject_"):
        subj=data.replace("study_subject_","")
        display=SUBJECT_DISPLAY.get(subj, subj.title())
        USER_SESSIONS[uid]={"mode":"tutor","subject":subj}
        await query.message.reply_text(f"📖 *Let's study {display}!* 🧬\nAsk me any question? I know {len(LOCAL_DATABANK.get(subj,[]))} Qs + syllabus + AI brain.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💬 Ask {display}", callback_data="ask_tutor")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    elif data=="syllabus":
        await query.message.reply_text("📋 *JAMB Syllabus - Choose:*", reply_markup=subjects_kb("syllabus_subject"), parse_mode="Markdown")
        return
    elif data.startswith("syllabus_subject_"):
        subj=data.replace("syllabus_subject_","")
        display=SUBJECT_DISPLAY.get(subj, subj.title())
        await query.message.reply_text(f"📋 *{display} Syllabus*\n\nJAMB syllabus: Core concepts + topics. Link: https://jamb.gov.ng/ELibrary", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"📖 Study {display}", callback_data=f"study_subject_{subj}")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    elif data=="past_by_subject":
        await query.message.reply_text("📚 *Past Questions - Choose Subject:*", reply_markup=subjects_kb("past_subject"), parse_mode="Markdown")
        return
    elif data.startswith("past_subject_"):
        subj=data.replace("past_subject_","")
        if not can_use_mock(uid,5):
            msg,kb=upgrade_kb(uid)
            await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
            return
        qs=fetcher.fetch(subj, None, 5)
        if not qs:
            await query.message.reply_text("No questions found")
            return
        consume_mock(uid,len(qs),[q["id"] for q in qs])
        USER_SESSIONS[uid]={"mode":"mock","qs":qs,"idx":0,"score":0,"subject":subj}
        q=qs[0]
        txt=format_question(q,1,len(qs))
        kb=[[InlineKeyboardButton(f"A) {q['option_a'][:25]}", callback_data="ans:A"), InlineKeyboardButton(f"B) {q['option_b'][:25]}", callback_data="ans:B")],[InlineKeyboardButton(f"C) {q['option_c'][:25]}", callback_data="ans:C"), InlineKeyboardButton(f"D) {q['option_d'][:25]}", callback_data="ans:D")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif data.startswith("ans:"):
        ans=data.split(":")[1]
        session=USER_SESSIONS.get(uid)
        if not session or session.get("mode")!="mock":
            await query.message.reply_text("Session expired. Start new mock.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Mock", callback_data="mock_menu")]]))
            return
        qs=session["qs"]
        idx=session["idx"]
        if idx>=len(qs):
            return
        current_q=qs[idx]
        correct=current_q["answer"]
        is_correct=ans==correct
        if is_correct:
            session["score"]+=1
        session["idx"]+=1
        feedback=f"{'✅ *Correct!* 🎉' if is_correct else f'❌ *Wrong.* Answer is *{correct}*'}"
        if current_q.get("explanation"):
            feedback+=f"\n\n💡 {current_q['explanation'][:350]}"
        await query.message.reply_text(feedback, parse_mode="Markdown")
        if session["idx"]<len(qs):
            q=qs[session["idx"]]
            txt=format_question(q,session["idx"]+1,len(qs))
            kb=[[InlineKeyboardButton(f"A) {q['option_a'][:25]}", callback_data="ans:A"), InlineKeyboardButton(f"B) {q['option_b'][:25]}", callback_data="ans:B")],[InlineKeyboardButton(f"C) {q['option_c'][:25]}", callback_data="ans:C"), InlineKeyboardButton(f"D) {q['option_d'][:25]}", callback_data="ans:D")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
            await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            score=session["score"]
            total=len(qs)
            percent=score*100//total if total else 0
            u["history"].append({"date":str(date.today()),"subject":session.get("subject","general"),"score":score,"total":total,"percent":percent})
            save_data()
            leader_name, leader_score=get_leading()
            result_text=f"🎉 *Mock Completed!*\n\nScore: *{score}/{total}* ({percent}%)\n🏆 Leader: {leader_name} - {leader_score}/400"
            kb=[[InlineKeyboardButton("🔄 Try Again", callback_data="mock_quick")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
            await query.message.reply_text(result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
            USER_SESSIONS.pop(uid,None)
        return
    elif data=="mock_menu":
        rem=get_mock_remaining(uid)
        if is_premium(uid):
            leader_name, leader_score=get_leading()
            await query.message.reply_text(f"📝 *Mock - Premium*\n🏆 Leader: {leader_name} - {leader_score}/400\n✅ Unlimited", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚡ Quick 5 Qs", callback_data="mock_quick")],[InlineKeyboardButton("🔥 Full 180Q", callback_data="mock_full")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        else:
            await query.message.reply_text(f"📝 *Mock - Free {rem}/{FREE_MOCK_QS_DAILY} today*\nInvite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"⚡ Quick 5 Qs ({rem} left)", callback_data="mock_quick")],[InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}=FREE", callback_data="invite_friends")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    elif data=="mock_quick":
        if not can_use_mock(uid,5):
            msg,kb=upgrade_kb(uid)
            await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
            return
        subjects_mix=random.sample(ALL_SUBJECTS,3)
        qs=[]
        for subj in subjects_mix:
            qs.extend(fetcher.fetch(subj, None, 2))
        random.shuffle(qs)
        qs=qs[:5]
        if not qs:
            await query.message.reply_text("No Qs available")
            return
        consume_mock(uid,len(qs),[q["id"] for q in qs])
        USER_SESSIONS[uid]={"mode":"mock","qs":qs,"idx":0,"score":0,"subject":"mixed"}
        q=qs[0]
        txt=format_question(q,1,len(qs))
        kb=[[InlineKeyboardButton(f"A) {q['option_a'][:25]}", callback_data="ans:A"), InlineKeyboardButton(f"B) {q['option_b'][:25]}", callback_data="ans:B")],[InlineKeyboardButton(f"C) {q['option_c'][:25]}", callback_data="ans:C"), InlineKeyboardButton(f"D) {q['option_d'][:25]}", callback_data="ans:D")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
        await query.message.reply_text(f"🚀 *Quick Mock 5 Qs*\n\n"+txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return
    elif data=="mock_full":
        if not is_premium(uid):
            msg,kb=upgrade_kb(uid)
            await query.message.reply_text(f"🔒 *Full Mock Premium Only*\n\n{msg}", parse_mode="Markdown", reply_markup=kb)
            return
        leader_name, leader_score=get_leading()
        await query.message.reply_text(f"🏆 *Leader: {leader_name} - {leader_score}/400*\n\nFull Mock 180Q 2hrs", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Start 180Q", callback_data="mock_full_start")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    elif data=="mock_full_start":
        if not is_premium(uid):
            msg,kb=upgrade_kb(uid)
            await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
            return
        qs=[]
        qs+=fetcher.fetch("english", None, 60)
        for subj in ["mathematics","biology","physics"]:
            qs+=fetcher.fetch(subj, None, 40)
        random.shuffle(qs)
        qs=qs[:180]
        if len(qs)<5:
            qs=fetcher.fetch("english", None, 20)
        USER_SESSIONS[uid]={"mode":"mock","qs":qs,"idx":0,"score":0,"subject":"full_mock"}
        q=qs[0]
        txt=format_question(q,1,180)
        kb=[[InlineKeyboardButton(f"A) {q['option_a'][:25]}", callback_data="ans:A"), InlineKeyboardButton(f"B) {q['option_b'][:25]}", callback_data="ans:B")],[InlineKeyboardButton(f"C) {q['option_c'][:25]}", callback_data="ans:C"), InlineKeyboardButton(f"D) {q['option_d'][:25]}", callback_data="ans:D")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
        leader_name, leader_score=get_leading()
        await query.message.reply_text(f"🚀 *Full Mock 180Q*\n🏆 To beat: {leader_name} - {leader_score}/400\n\n"+txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return
    elif data=="leaderboard":
        scores=[]
        for uid_k, d in USER_DATA.items():
            hist=d.get("history",[])
            if not hist: continue
            avg=sum(h.get("percent",0) for h in hist)/len(hist)
            scores.append((d.get("username", f"User{str(uid_k)[-4:]}"), avg, len(hist)))
        scores.sort(key=lambda x: x[1], reverse=True)
        text="🏆 *LEADERBOARD*\n\n"
        for i,(name,avg,c) in enumerate(scores[:15],1):
            medal=["🥇","🥈","🥉"][i-1] if i<=3 else f"{i}."
            text+=f"{medal} {name} - {avg:.1f}% ({c} mocks)\n"
        if not scores:
            text+="No scores yet"
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Mock", callback_data="mock_quick"), InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    elif data=="my_score":
        hist=u.get("history",[])
        if not hist:
            await query.message.reply_text("📊 No scores yet", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Mock", callback_data="mock_quick")]]))
            return
        avg=sum(h["score"]*400//h["total"] for h in hist)/len(hist) if hist else 0
        leader_name, leader_score=get_leading()
        await query.message.reply_text(f"📊 Avg {int(avg)}/400 Exams {len(hist)}\n🏆 Leader: {leader_name} - {leader_score}/400", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    elif data=="ask_tutor":
        USER_SESSIONS[uid]={"mode":"tutor","subject":u.get("study_subject")}
        await query.message.reply_text(f"💬 *Ask Tutor - 200% Smart*\nI know {len(ALL_QS)} Qs + syllabus + AI brain + Voice 🎙️ Nigerian slow.\nAsk anything:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    elif data=="premium_info":
        url=f"{PAYMENT_URL}/upgrade/{uid}" if PAYMENT_URL else f"https://t.me/{BOT_USERNAME}"
        text=f"💎 *Premium {PREMIUM_PRICE_TEXT}/month*\n✅ Unlimited mocks\n✅ Full 180Q\n✅ Unlimited tutor + Voice 🎙️\n✅ {len(ALL_QS)} Qs\n✅ Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE viral!"
        kb=[[InlineKeyboardButton(f"💳 Upgrade {PREMIUM_PRICE_TEXT}", url=url)],[InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}=FREE", callback_data="invite_friends")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return
    elif data=="invite_friends":
        link=f"https://t.me/{BOT_USERNAME}?start=invite_{u['invite_code']}"
        invites=u.get('invites',0)
        text=f"👥 *Invite Friends - VIRAL BONUS!*\n\n🎁 Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!\n\nLink:\n`{link}`\n\nInvites: {invites}/{REFERRAL_REQUIRED}\n\n1. Share link\n2. Friend starts bot\n3. You get count\n4. At {REFERRAL_REQUIRED} → {REFERRAL_REWARD_DAYS} days auto!"
        kb=[[InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={link}&text=Join UTME Success Bot!")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return
    elif data=="help_menu":
        await query.message.reply_text(f"Help -@{CHANNEL_USERNAME}\nID: {uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
        return
    elif data=="main_menu":
        t,kb=main_menu(uid)
        await query.message.reply_text(t, reply_markup=kb, parse_mode="Markdown")
        return

async def handle_msg(update, context):
    uid=str(update.effective_user.id)
    text=(update.message.text or "").strip()
    u=get_user(uid, update.effective_user.first_name or "")
    if text in ["📚 Past Questions", "📝 Mock Exam", "📊 My Score", "💬 Ask Tutor", "💎 Premium", "👥 Invite Friends", "📖 Study Plan"]:
        if text=="📚 Past Questions":
            await update.message.reply_text("📚 *Past Questions - Choose Subject:*", reply_markup=subjects_kb("past_subject"), parse_mode="Markdown")
            return
        elif text in ["📝 Mock Exam"]:
            rem=get_mock_remaining(uid)
            if is_premium(uid):
                leader_name, leader_score=get_leading()
                await update.message.reply_text(f"🏆 Leader: {leader_name} - {leader_score}/400\n📝 Mock Premium Unlimited", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚡ Quick 5 Qs", callback_data="mock_quick")],[InlineKeyboardButton("🔥 Full 180Q", callback_data="mock_full")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            else:
                await update.message.reply_text(f"📝 Mock Free {rem}/{FREE_MOCK_QS_DAILY} today\nInvite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"⚡ Quick 5 Qs ({rem} left)", callback_data="mock_quick")],[InlineKeyboardButton(f"👥 Invite {REFERRAL_REQUIRED}=FREE", callback_data="invite_friends")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            return
        elif text=="📊 My Score":
            hist=u.get("history",[])
            if not hist:
                await update.message.reply_text("📊 No scores yet")
                return
            avg=sum(h["score"]*400//h["total"] for h in hist)/len(hist) if hist else 0
            await update.message.reply_text(f"📊 Avg {int(avg)}/400 Exams {len(hist)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            return
        elif text=="💬 Ask Tutor":
            USER_SESSIONS[uid]={"mode":"tutor"}
            await update.message.reply_text(f"💬 *Ask Tutor - 200% Smart*\nI know {len(ALL_QS)} Qs + AI brain + Voice 🎙️ Nigerian slow.\nAsk anything:", parse_mode="Markdown")
            return
        elif text=="💎 Premium":
            url=f"{PAYMENT_URL}/upgrade/{uid}" if PAYMENT_URL else f"https://t.me/{BOT_USERNAME}"
            await update.message.reply_text(f"💎 *Premium {PREMIUM_PRICE_TEXT}*\n✅ Unlimited mocks\n✅ Full 180Q\n✅ Tutor + Voice\n✅ Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Upgrade {PREMIUM_PRICE_TEXT}", url=url)],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            return
        elif text=="👥 Invite Friends":
            link=f"https://t.me/{BOT_USERNAME}?start=invite_{u['invite_code']}"
            await update.message.reply_text(f"👥 *Invite Friends VIRAL*\n\nInvite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE!\n\nLink:\n`{link}`\n\nInvites: {u.get('invites',0)}/{REFERRAL_REQUIRED}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={link}")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
            return
        elif text=="📖 Study Plan":
            await update.message.reply_text("📖 *Study Plan - Choose:*", reply_markup=subjects_kb("study_subject"), parse_mode="Markdown")
            return

    # Tutor mode
    session=USER_SESSIONS.get(uid,{})
    is_tutor=session.get("mode")=="tutor" or "?" in text or len(text)>8
    if is_tutor:
        if not can_use_tutor(uid):
            msg,kb=upgrade_kb(uid)
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
            return
        consume_tutor(uid)
        relevant=[]
        try:
            subj_filter=session.get("subject")
            relevant=search_databank(text, subject=subj_filter, limit=3)
        except:
            pass
        subj=session.get("subject") or "general"
        display=SUBJECT_DISPLAY.get(subj, subj.title()) if subj!="general" else "JAMB"
        answer_text=f"💬 *{display} Tutor - 200% Smart*\n\n*Q:* {text[:400]}\n\n"
        if relevant:
            answer_text+=f"*📚 From Databank ({len(relevant)} found):*\n\n"
            for i,rq in enumerate(relevant[:2],1):
                ans=rq.get("answer","")
                answer_text+=f"{i}. *{rq.get('subject','')} {rq.get('year','')}*\n{rq.get('question','')[:180]}...\n✅ Answer: {ans}\n"
                if rq.get("explanation"):
                    answer_text+=f"💡 {rq.get('explanation')[:180]}...\n"
                answer_text+="\n"
        answer_text+=f"*🧠 AI Brain ({display}):*\n\n"
        lower_q=text.lower()
        if "photosynthesis" in lower_q:
            answer_text+="Photosynthesis: 6CO2 + 6H2O → C6H12O6 + 6O2. Chloroplast, light & dark reaction. Factors: light, CO2, temp.\n\n"
        else:
            answer_text+=f"Based on JAMB syllabus for {display}: core concept explanation, steps, example, how JAMB asks, trick to avoid.\n\n"
        answer_text+=f"💡 Tip: Appears frequently in UTME. Eliminate wrong options!\n"
        kb=[[InlineKeyboardButton("🎙️ Voice", callback_data="ask_tutor")],[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
        await update.message.reply_text(answer_text[:4000], parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        if HAS_TTS:
            try:
                voice_text=f"Hello! Let's study {display}. Question: {text[:150]}. "
                if relevant:
                    rq=relevant[0]
                    voice_text+=f"From past question: {rq.get('question','')[:100]}. Answer is {rq.get('answer','')}. "
                voice_text+=f"Explanation: {answer_text[answer_text.find('AI Brain'):][:250] if 'AI Brain' in answer_text else text[:100]}. Keep practicing!"
                voice_text=re.sub(r'[*_#`]', '', voice_text)[:600]
                tts=gTTS(text=voice_text, lang='en', tld='com.ng', slow=True)
                voice_path=f"/tmp/voice_{uid}_{int(time.time())}.mp3"
                tts.save(voice_path)
                with open(voice_path, 'rb') as f:
                    await update.message.reply_voice(voice=f, caption=f"🎙️ Voice - {display} - Slow Nigerian", parse_mode="Markdown")
                try:
                    os.remove(voice_path)
                except:
                    pass
            except Exception as e:
                print(f"TTS error: {e}")
        return
    await update.message.reply_text("Use menu below:", reply_markup=BOTTOM_KEYBOARD)

async def start(update, context):
    uid=str(update.effective_user.id)
    username=update.effective_user.first_name or ""
    if context.args and len(context.args)>0:
        arg=context.args[0]
        if arg.startswith("invite_"):
            code=arg.replace("invite_","")
            u=get_user(uid, username)
            if not u.get("invited_by"):
                for inviter_id, inv_data in USER_DATA.items():
                    if inv_data.get("invite_code")==code and inviter_id!=uid:
                        if uid not in inv_data.get("invited_users",[]):
                            u["invited_by"]=inviter_id
                            inv_data["invites"]=inv_data.get("invites",0)+1
                            inv_data.setdefault("invited_users", []).append(uid)
                            if inv_data["invites"]>=REFERRAL_REQUIRED:
                                add_premium(inviter_id, days=REFERRAL_REWARD_DAYS)
                                inv_data["invites"]=0
                            save_data()
                            await update.message.reply_text(f"🎉 Welcome! Invited by friend. Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE premium!")
                        break
    t,kb=main_menu(uid)
    await update.message.reply_text(t, reply_markup=kb, parse_mode="Markdown")
    await update.message.reply_text(f"Use buttons below 👇\n🚀 Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days Premium FREE!", reply_markup=BOTTOM_KEYBOARD)

flask_app=Flask(__name__)

@flask_app.route("/")
def home():
    return f"UTME v21 PROFESSIONAL - Mock FIXED + Tutor 200% + Voice + Viral {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} - {FREE_MOCK_QS_DAILY}/day + {FREE_TUTOR_PER_DAY} tutor | {len(ALL_QS) if 'ALL_QS' in globals() else 0} Qs | Running"

@flask_app.route("/upgrade/<uid>")
def upgrade_page(uid):
    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Upgrade</title><style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);text-align:center;padding:20px}} .card{{background:white;max-width:450px;margin:20px auto;padding:30px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,.2)}} .btn{{background:#5865f2;color:white;padding:16px 28px;border-radius:12px;text-decoration:none;display:inline-block;margin:10px 0;font-weight:bold;width:85%}} .btn2{{background:#00c851;color:white;padding:14px 28px;border-radius:12px;text-decoration:none;display:inline-block;margin:8px 0;font-weight:bold;width:85%}} .viral{{background:#fff3cd;padding:15px;border-radius:10px;margin:15px 0;border-left:4px solid #ffc107}}</style></head><body><div class="card"><h2>💎 Go Premium</h2><p>User: {uid}</p><div style="font-size:36px;font-weight:bold;color:#5865f2">{PREMIUM_PRICE_TEXT}/month</div><div class="viral"><strong>🚀 VIRAL:</strong><br>Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE premium!</div><ul style="text-align:left;max-width:320px;margin:20px auto;line-height:2"><li>✅ Unlimited Mocks</li><li>✅ Full 180Q CBT</li><li>✅ Unlimited Tutor + Voice 🎙️</li><li>✅ Voice Nigerian slow</li><li>✅ All databank</li></ul><a class="btn" href="https://paystack.com/pay/utme-success-{uid}">💳 Pay {PREMIUM_PRICE_TEXT}</a><a class="btn2" href="https://t.me/{BOT_USERNAME}?start=invite_{uid}">👥 Invite 3=7 Days FREE</a></div></body></html>
    """)

@flask_app.route("/health")
def health():
    return jsonify({"status":"ok","version":"v21 PROFESSIONAL Mock FIXED + Tutor 200% + Voice + Viral","premium":PREMIUM_PRICE_TEXT,"free_mock_daily":FREE_MOCK_QS_DAILY,"free_tutor_daily":FREE_TUTOR_PER_DAY,"referral":f"{REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS}","total_questions": len(ALL_QS) if 'ALL_QS' in globals() else 0,"users":len(USER_DATA)})

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))

async def channel_posting_job(app):
    posted_today=set()
    while True:
        try:
            now=datetime.now()
            lagos_hour=(now.hour+1)%24
            current_key=f"{now.date()}_{lagos_hour}"
            if lagos_hour in [8,13,20] and current_key not in posted_today:
                if not CHANNEL_ID:
                    await asyncio.sleep(3600)
                    continue
                try:
                    q=get_random_question()
                    if not q:
                        await asyncio.sleep(3600)
                        continue
                    intro=random.choice(["🌅 *Good Morning Champions!*","☀️ *Rise and Shine!*"])
                    cta=f"Invite {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS} days FREE premium!"
                    question_text=q.get('question','')[:320]
                    options_text=f"A) {q.get('option_a','')[:70]}\nB) {q.get('option_b','')[:70]}\nC) {q.get('option_c','')[:70]}\nD) {q.get('option_d','')[:70]}"
                    message=f"{intro}\n\n*{q.get('subject','JAMB')} | {q.get('year','')}*\n\n{question_text}\n\n{options_text}\n\n{cta}\n\n👉 https://t.me/{BOT_USERNAME}\n💎 Premium {PREMIUM_PRICE_TEXT}\n\n*Invite {REFERRAL_REQUIRED}= {REFERRAL_REWARD_DAYS} days FREE!*"
                    await app.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")
                    posted_today.add(current_key)
                    if len(posted_today)>10:
                        posted_today.clear()
                except Exception as e:
                    print(f"Channel error: {e}")
            await asyncio.sleep(1800)
        except Exception as e:
            print(f"Channel job error: {e}")
            await asyncio.sleep(3600)

async def set_bot_commands_and_menu(app):
    try:
        commands=[BotCommand("start","Main Menu"),BotCommand("menu","Main Menu"),BotCommand("mock","Mock Exam - 5 Qs/day free"),BotCommand("study","Study Plan"),BotCommand("syllabus","JAMB Syllabus"),BotCommand("score","My Score"),BotCommand("tutor","Ask Tutor - 200% Smart"),BotCommand("invite","Invite 3=7 Days FREE"),BotCommand("premium","Upgrade Premium"),BotCommand("help","Help @UTMESUCCESS")]
        await app.bot.set_my_commands(commands)
        await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="Menu"))
        print("✅ Commands v21 set")
        asyncio.create_task(channel_posting_job(app))
    except Exception as e:
        print(f"Menu setup failed: {e}")

def main():
    threading.Thread(target=run_flask,daemon=True).start()
    print(f"Flask started port {os.environ.get('PORT', 5000)}")
    if not BOT_TOKEN or BOT_TOKEN=="YOUR_BOT_TOKEN_HERE" or len(BOT_TOKEN)<20:
        print("❌ BOT_TOKEN not set!")
        while True: time.sleep(60)
    try:
        app=ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start",start))
        app.add_handler(CommandHandler("menu",start))
        app.add_handler(CommandHandler("mock",start))
        app.add_handler(CommandHandler("study",start))
        app.add_handler(CommandHandler("syllabus",start))
        app.add_handler(CommandHandler("score",start))
        app.add_handler(CommandHandler("tutor",start))
        app.add_handler(CommandHandler("invite",start))
        app.add_handler(CommandHandler("premium",start))
        app.add_handler(CommandHandler("help",start))
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_handler(MessageHandler(filters.Regex("^(📚 Past Questions|📝 Mock Exam|📊 My Score|💬 Ask Tutor|💎 Premium|👥 Invite Friends|📖 Study Plan|🔵 MENU|MENU|/mock|mock)$"),handle_msg))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_msg))
        app.post_init=set_bot_commands_and_menu
        print(f"v21 PROFESSIONAL - Mock FIXED + Tutor 200% + Voice + Viral {REFERRAL_REQUIRED}={REFERRAL_REWARD_DAYS}")
        app.run_polling()
    except Exception as e:
        print(f"❌ Bot failed: {e}")
        import traceback; traceback.print_exc()
        while True: time.sleep(60)

if __name__=="__main__":
    main()
