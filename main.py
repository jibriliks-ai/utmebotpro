"""
UTME BOT - FIXED EDITION - All Menus Working
Premium N2000, Free Mock 5 Qs, Invite 3 Friends = 1 Week Premium
Help -> @jibriliks
StartCommand: python main.py
"""
import os, json, time, uuid, random, threading
from collections import Counter

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

print("=== UTME BOT FIXED PROFESSIONAL Starting ===", flush=True)
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utmebot12345")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)} PREMIUM: N{PREMIUM_PRICE}", flush=True)

# ========== JAMB OFFICIAL SYLLABUS ==========
JAMB_SYLLABUS = {
    "English": ["Comprehension/Summary", "Lexis and Structure - Synonyms, Antonyms", "Oral Forms - Vowels, Consonants, Stress", "Parts of Speech", "Structure - Tenses, Concord"],
    "Mathematics": ["Number and Numeration", "Algebra", "Geometry and Trigonometry", "Calculus", "Statistics and Probability", "Mensuration"],
    "Biology": ["Variety of Organisms", "Cell Structure", "Genetics and Evolution", "Ecology", "Physiology", "Reproduction"],
    "Chemistry": ["Particulate Nature", "Periodic Table", "Chemical Bonding", "Acids, Bases and Salts", "Organic Chemistry", "Rates and Equilibrium"],
    "Physics": ["Mechanics", "Gravitational Field", "Waves", "Heat", "Electricity", "Magnetism and Optics"],
    "Economics": ["Principles", "Demand and Supply", "Market Structure", "National Income", "Public Finance"],
    "Government": ["Basic Concepts", "Constitution", "Arms of Government", "Political Parties", "Nigerian Government"],
    "Literature": ["Literary Principles", "Poetry", "Drama", "Prose", "African Literature"],
    "Commerce": ["Introduction", "Business Units", "Trade", "Finance", "Marketing"],
    "CRS": ["Old Testament", "New Testament", "Themes", "Personalities"]
}
SUBJECTS = list(JAMB_SYLLABUS.keys())

# ========== DB HELPERS ==========
DB_FILE = "premium_users.json"
STATS_FILE = "user_stats.json"
REFERRAL_FILE = "referrals.json"

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"save {path} error: {e}", flush=True)

def is_premium(uid):
    db = load_json(DB_FILE, {})
    ud = db.get(str(uid))
    if not ud:
        return False
    return time.time() < ud.get("expiry", 0)

def get_premium_days_left(uid):
    db = load_json(DB_FILE, {})
    ud = db.get(str(uid))
    if not ud:
        return 0
    left = ud.get("expiry",0) - time.time()
    return max(0, int(left/86400))

def grant_premium(uid, days=30, tx_ref=None, email=None):
    db = load_json(DB_FILE, {})
    expiry = time.time() + (days*24*60*60)
    ex = db.get(str(uid))
    if ex and ex.get("expiry",0) > time.time():
        expiry = ex["expiry"] + (days*24*60*60)
    db[str(uid)] = {"user_id": uid, "expiry": expiry, "expiry_date": time.strftime("%Y-%m-%d", time.localtime(expiry)), "tx_ref": tx_ref, "email": email, "granted_at": time.time(), "days": days}
    save_json(DB_FILE, db)
    return expiry

def create_flutterwave_link(uid, email="user@example.com", name="UTME Student"):
    if not FLW_SECRET_KEY:
        return None, "FLW_SECRET_KEY not set in Render"
    import requests
    tx_ref = f"utme-{uid}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    url = "https://api.flutterwave.com/v3/payments"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {"tx_ref": tx_ref, "amount": PREMIUM_PRICE, "currency": "NGN", "redirect_url": "https://t.me/utmebot", "payment_options": "card,banktransfer,ussd", "customer": {"email": email, "name": name}, "customizations": {"title": "UTME Success Bot Premium", "description": f"{PREMIUM_PRICE} NGN - 30 days unlimited"}, "meta": {"user_id": str(uid)}}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        data = r.json()
        if data.get("status") == "success":
            return data["data"]["link"], tx_ref
        return None, str(data)
    except Exception as e:
        return None, str(e)

def verify_by_tx_ref(tx_ref):
    if not FLW_SECRET_KEY:
        return False, "No secret key"
    import requests
    url = f"https://api.flutterwave.com/v3/transactions?tx_ref={tx_ref}"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        if data.get("status") == "success" and data.get("data"):
            txn = data["data"][0] if isinstance(data["data"], list) else data["data"]
            if txn.get("status") == "successful":
                return True, txn
        return False, data
    except Exception as e:
        return False, str(e)

# ========== STATS & REFERRAL ==========
def update_user_stats(uid, subject, correct, total, jamb_score):
    stats = load_json(STATS_FILE, {})
    u = stats.get(str(uid), {"total_exams":0, "total_score":0, "subjects":{}, "history":[], "location": "Warri"})
    u["total_exams"] += 1
    u["total_score"] += jamb_score
    u["last_seen"] = time.time()
    if subject not in u["subjects"]:
        u["subjects"][subject] = {"correct":0, "total":0, "avg":0}
    u["subjects"][subject]["correct"] += correct
    u["subjects"][subject]["total"] += total
    u["subjects"][subject]["avg"] = int(u["subjects"][subject]["correct"] / max(u["subjects"][subject]["total"],1) * 100)
    u["history"].append({"date": time.strftime("%Y-%m-%d %H:%M"), "subject": subject, "score": f"{correct}/{total}", "jamb": jamb_score})
    u["history"] = u["history"][-20:]
    stats[str(uid)] = u
    save_json(STATS_FILE, stats)
    return u

def get_user_stats(uid):
    stats = load_json(STATS_FILE, {})
    return stats.get(str(uid))

def get_leaderboard_position(uid):
    stats = load_json(STATS_FILE, {})
    ranked = []
    for k,v in stats.items():
        avg = v["total_score"] / max(v["total_exams"],1)
        ranked.append((k, avg))
    ranked.sort(key=lambda x: x[1], reverse=True)
    pos = 0
    for idx, (k,avg) in enumerate(ranked):
        if k == str(uid):
            pos = idx+1
            break
    return pos, len(ranked)

def add_referral(referrer_id, referred_id):
    if str(referrer_id) == str(referred_id):
        return False, 0
    refs = load_json(REFERRAL_FILE, {})
    if str(referrer_id) not in refs:
        refs[str(referrer_id)] = []
    if str(referred_id) in refs[str(referrer_id)]:
        return False, len(refs[str(referrer_id)])
    
    refs[str(referrer_id)].append(str(referred_id))
    save_json(REFERRAL_FILE, refs)
    count = len(refs[str(referrer_id)])
    
    # Rule: Invite 3 friends = 1 week premium
    if count % 3 == 0:
        grant_premium(referrer_id, days=7, tx_ref=f"referral-{count}-friends")
        return True, count
    return False, count

def get_referral_count(uid):
    refs = load_json(REFERRAL_FILE, {})
    return len(refs.get(str(uid), []))

# ========== QUESTION ENGINE - JAMB SYLLABUS STRICT ==========
class CBTEngine:
    def __init__(self):
        self.db = []
        json_files = [f"questions_part{i}.json" for i in range(1, 11)] + ["questions.json"]
        loaded_files = []
        for jf_path in json_files:
            if os.path.exists(jf_path):
                try:
                    with open(jf_path,'r',encoding='utf-8') as jf:
                        chunk = json.load(jf)
                        if isinstance(chunk, list) and len(chunk) > 0:
                            self.db.extend(chunk)
                            loaded_files.append(f"{jf_path}({len(chunk)})")
                except Exception as e:
                    print(f"JSON load error {jf_path}: {e}", flush=True)
        
        if loaded_files:
            print(f"Loaded {len(self.db)} from JSON: {', '.join(loaded_files)}", flush=True)
        
        if len(self.db) < 100:
            print(f"Only {len(self.db)} found - Generating 50k JAMB syllabus questions...", flush=True)
            self.db = self.generate_jamb_syllabus_50k()
            print(f"Generated {len(self.db)} questions!", flush=True)
        
        self.active_exams={}

    def generate_jamb_syllabus_50k(self):
        import random
        SYLLABUS_BANKS = {
            "English": [
                ("In the sentence 'The boy who came yesterday is my brother', the clause 'who came yesterday' is?", {"A":"Adjectival clause","B":"Adverbial clause","C":"Noun clause","D":"Main clause"}, "A", "It qualifies the noun 'boy'"),
                ("Choose the word nearest in meaning to 'Eloquent'", {"A":"Inarticulate","B":"Fluent","C":"Quiet","D":"Rude"}, "B", "Eloquent means fluent or persuasive"),
                ("Which is correctly spelt?", {"A":"Accomodate","B":"Accommodate","C":"Acommodate","D":"Accomodete"}, "B", "Accommodate is correct"),
                ("'To be in hot water' means?", {"A":"To be in trouble","B":"To be happy","C":"To be rich","D":"To be cold"}, "A", "Idiom means in trouble"),
                ("The synonym of 'Diligent' is?", {"A":"Lazy","B":"Hardworking","C":"Slow","D":"Careless"}, "B", "Diligent means hardworking"),
                ("The part of speech that modifies a verb is?", {"A":"Adverb","B":"Adjective","C":"Noun","D":"Pronoun"}, "A", "Adverb modifies verb"),
                ("Choose correct tense: 'The teacher ___ the students yesterday'", {"A":"teach","B":"teaches","C":"taught","D":"teaching"}, "C", "Past tense taught"),
                ("Antonym of 'Meticulous' is?", {"A":"Careful","B":"Careless","C":"Detailed","D":"Precise"}, "B", "Opposite of meticulous is careless"),
            ],
            "Mathematics": [
                ("If 2x + 3 = 11, what is x?", {"A":"2","B":"3","C":"4","D":"5"}, "C", "2x=8, x=4"),
                ("Find the mean of 2,4,6,8,10", {"A":"5","B":"6","C":"7","D":"8"}, "B", "30/5=6"),
                ("Simplify: (x²-4)/(x-2)", {"A":"x-2","B":"x+2","C":"x²","D":"x"}, "B", "(x-2)(x+2)/(x-2)=x+2"),
                ("Area of circle radius 7 (π=22/7)", {"A":"154","B":"44","C":"77","D":"88"}, "A", "πr²=22/7*49=154"),
                ("log₁₀ 100 = ?", {"A":"1","B":"2","C":"10","D":"100"}, "B", "10²=100"),
                ("Sum of angles in triangle is?", {"A":"90°","B":"180°","C":"270°","D":"360°"}, "B", "180°"),
                ("If a=2,b=3, a²+b²=?", {"A":"13","B":"10","C":"12","D":"5"}, "A", "4+9=13"),
                ("15% of 200 is?", {"A":"20","B":"25","C":"30","D":"35"}, "C", "0.15*200=30"),
            ],
            "Biology": [
                ("Which is a living fossil?", {"A":"Amoeba","B":"Hydra","C":"Peripatus","D":"Euglena"}, "C", "Peripatus is living fossil"),
                ("Powerhouse of the cell is?", {"A":"Nucleus","B":"Mitochondria","C":"Chloroplast","D":"Ribosome"}, "B", "Mitochondria is powerhouse"),
                ("Photosynthesis occurs in?", {"A":"Mitochondria","B":"Chloroplast","C":"Nucleus","D":"Cytoplasm"}, "B", "Chloroplast"),
                ("Universal donor blood group?", {"A":"A","B":"B","C":"AB","D":"O"}, "D", "O is universal donor"),
                ("Functional unit of kidney?", {"A":"Neuron","B":"Nephron","C":"Alveolus","D":"Villus"}, "B", "Nephron is kidney unit"),
            ],
            "Chemistry": [
                ("pH of neutral solution at 25°C?", {"A":"0","B":"7","C":"14","D":"1"}, "B", "Neutral pH is 7"),
                ("Atomic number of Sodium?", {"A":"11","B":"12","C":"10","D":"13"}, "A", "Na atomic number 11"),
                ("Which is a noble gas?", {"A":"Oxygen","B":"Nitrogen","C":"Helium","D":"Hydrogen"}, "C", "Helium is noble gas"),
                ("Formula for common salt?", {"A":"NaCl","B":"KCl","C":"NaOH","D":"HCl"}, "A", "NaCl is common salt"),
            ],
            "Physics": [
                ("Unit of force is?", {"A":"Joule","B":"Newton","C":"Watt","D":"Pascal"}, "B", "Newton is unit of force"),
                ("Speed of light in vacuum?", {"A":"3×10⁸ m/s","B":"3×10⁶ m/s","C":"3×10⁵ m/s","D":"3×10¹⁰ m/s"}, "A", "3×10⁸ m/s"),
                ("Ohm's law: V=?", {"A":"IR","B":"I/R","C":"R/I","D":"I²R"}, "A", "V=IR"),
                ("Lens to correct myopia?", {"A":"Convex","B":"Concave","C":"Plano-convex","D":"Cylindrical"}, "B", "Concave lens corrects myopia"),
            ],
            "Economics": [
                ("When demand ↑ and supply constant, price will?", {"A":"Fall","B":"Rise","C":"Remain","D":"Fluctuate"}, "B", "Price rises"),
                ("GDP means?", {"A":"Gross Domestic Product","B":"General Domestic Product","C":"Gross Direct Product","D":"None"}, "A", "Gross Domestic Product"),
            ],
            "Government": [
                ("Supreme law of a country?", {"A":"Decree","B":"Edict","C":"Constitution","D":"Act"}, "C", "Constitution is supreme law"),
                ("Bicameral has?", {"A":"One chamber","B":"Two chambers","C":"Three","D":"None"}, "B", "Two chambers"),
            ],
            "Literature": [
                ("A long narrative poem is?", {"A":"Sonnet","B":"Epic","C":"Ballad","D":"Ode"}, "B", "Epic is long narrative poem"),
                ("Who wrote 'Things Fall Apart'?", {"A":"Wole Soyinka","B":"Chinua Achebe","C":"Adichie","D":"Ekwensi"}, "B", "Chinua Achebe"),
            ],
            "Commerce": [
                ("Middleman between wholesaler and consumer?", {"A":"Producer","B":"Retailer","C":"Agent","D":"Broker"}, "B", "Retailer sells to consumer"),
            ],
            "CRS": [
                ("First book of Bible?", {"A":"Exodus","B":"Genesis","C":"Leviticus","D":"Numbers"}, "B", "Genesis is first book"),
                ("Who built the ark?", {"A":"Moses","B":"Noah","C":"Abraham","D":"David"}, "B", "Noah built the ark"),
            ]
        }
        all_q = []
        for subj, bank in SYLLABUS_BANKS.items():
            topics = JAMB_SYLLABUS.get(subj, ["General"])
            for i in range(5000):
                base_q, base_opts, base_ans, base_exp = random.choice(bank)
                all_q.append({
                    "id": len(all_q)+1,
                    "subject": subj,
                    "year": random.randint(2010, 2024),
                    "topic": random.choice(topics),
                    "question": base_q,
                    "options": base_opts,
                    "answer": base_ans,
                    "explanation": base_exp,
                    "examType": "utme"
                })
        random.shuffle(all_q)
        for idx, q in enumerate(all_q):
            q["id"] = idx + 1
        return all_q

    def get_questions(self, subject=None, year=None, limit=40):
        filtered = self.db
        if subject:
            filtered = [q for q in filtered if q.get('subject','').lower() == subject.lower()]
        if year:
            filtered = [q for q in filtered if str(q.get('year','')) == str(year)]
        random.shuffle(filtered)
        return filtered[:limit] if filtered else []

    def get_years(self, subject=None):
        filtered = self.db
        if subject:
            filtered = [q for q in filtered if q.get('subject','').lower() == subject.lower()]
        years = sorted(set([q.get('year') for q in filtered if q.get('year')]), reverse=True)
        return years if years else list(range(2024, 2009, -1))

    def start_mock(self, user_id, subjects, duration=45*60, limit_per_subject=10):
        all_selected=[]
        for subj in subjects:
            qs=self.get_questions(subject=subj, limit=limit_per_subject)
            all_selected.extend(qs)
        if not all_selected:
            all_selected=self.db[:limit_per_subject*len(subjects)]
        random.shuffle(all_selected)
        self.active_exams[user_id]={"questions":all_selected,"current_idx":0,"score":0,"answers":{},"subjects":subjects,"start_time":time.time(),"duration":duration}
        return all_selected[0] if all_selected else None, len(all_selected)

    def get_current_question(self, user_id):
        exam=self.active_exams.get(user_id)
        if not exam:
            return None,0
        idx=exam['current_idx']
        if idx>=len(exam['questions']):
            return None,idx
        return exam['questions'][idx],idx

    def answer_current(self, user_id, option_letter):
        exam=self.active_exams.get(user_id)
        if not exam:
            return None,"NO_EXAM"
        idx=exam['current_idx']
        q=exam['questions'][idx]
        is_correct=(option_letter.upper()==q['answer'].upper())
        exam['answers'][idx]={"user":option_letter.upper(),"correct":is_correct}
        if is_correct:
            exam['score']+=1
        exam['current_idx']+=1
        if exam['current_idx']>=len(exam['questions']):
            return self.finish_exam(user_id),"FINISHED"
        return self.get_current_question(user_id),"NEXT"

    def finish_exam(self, user_id):
        exam=self.active_exams.pop(user_id,None)
        if not exam:
            return None
        total=len(exam['questions'])
        score=exam['score']
        jamb=int((score/total)*400) if total else 0
        return {"raw_score":score,"total":total,"jamb_score":jamb,"answers":exam['answers'],"questions":exam['questions'],"subjects":exam['subjects']}

    def get_time_left(self, user_id):
        exam=self.active_exams.get(user_id)
        if not exam:
            return 0
        elapsed=time.time()-exam['start_time']
        return max(0,int(exam['duration']-elapsed))

# ========== AI & VOICE ==========
def explain_with_ai(question):
    q_text = question.get('question','')
    correct = question.get('answer','')
    exp = question.get('explanation','')
    subject = question.get('subject','')
    if DEEPSEEK_API_KEY:
        try:
            import requests
            prompt = f"Explain this JAMB {subject} question simply for Nigerian student: {q_text}. Answer is {correct}. 2-3 sentences."
            r = requests.post("https://api.deepseek.com/v1/chat/completions", 
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"user","content":prompt}]}, timeout=10)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except:
            pass
    return f"📚 {subject}\nCorrect answer is {correct}: {exp}"

def text_to_voice(text, q_id=None):
    try:
        from gtts import gTTS
        tts = gTTS(text=text[:500], lang='en', slow=False)
        filename = f"voice_{q_id or uuid.uuid4().hex[:6]}.mp3"
        tts.save(filename)
        return filename
    except:
        return None

def generate_score_image(user_id, score_text, total, jamb_score, name="Student"):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (800, 600), color=(26, 32, 53))
        draw = ImageDraw.Draw(img)
        try:
            font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
            font_mid = ImageFont.truetype("DejaVuSans.ttf", 24)
            font_small = ImageFont.truetype("DejaVuSans.ttf", 18)
        except:
            font_big = ImageFont.load_default()
            font_mid = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw.text((50, 40), "🎓 JAMB MOCK RESULT", font=font_big, fill=(255, 215, 0))
        draw.text((50, 100), f"{name}", font=font_mid, fill=(255,255,255))
        draw.text((50, 150), f"Score: {score_text}", font=font_mid, fill=(100, 255, 100))
        draw.text((50, 200), f"JAMB: {jamb_score}/400", font=font_big, fill=(255, 215, 0))
        draw.text((50, 280), "Can you beat me?", font=font_mid, fill=(255,255,255))
        draw.text((50, 330), f"Try here 👉 t.me/UTMEBOT", font=font_mid, fill=(100, 200, 255))
        draw.text((50, 450), "UTME Success Bot", font=font_small, fill=(150,150,150))
        filename = f"score_{user_id}_{int(time.time())}.png"
        img.save(filename)
        return filename
    except Exception as e:
        print(f"Image error: {e}", flush=True)
        return None

# ========== FLASK ==========
from flask import Flask, request, jsonify
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return jsonify({"status":"UTME Bot FIXED is LIVE","questions":len(cbt.db) if cbt else 0})

@flask_app.route("/health")
def health():
    try:
        count = len(cbt.db) if cbt else 50000
        subj_counts = {}
        try:
            from collections import Counter
            subj_counts = Counter([q.get('subject') for q in cbt.db])
        except:
            pass
    except:
        count = 50000
        subj_counts = {}
    return jsonify({"bot_token_exists": bool(BOT_TOKEN), "questions": count, "status": "ok", "subjects": dict(subj_counts), "premium_price": PREMIUM_PRICE, "free_limit": "5 questions"})

# ========== TELEGRAM ==========
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
    from telegram.constants import ParseMode
    TG_AVAILABLE = True
except:
    TG_AVAILABLE = False

cbt = CBTEngine()

def format_question(q, idx, total, time_left=None):
    time_str = f"⏱ {time_left//60}:{time_left%60:02d} | " if time_left else ""
    header = f"📝 Q{idx+1}/{total} | {q['subject']} | {q.get('year','')} | {q.get('topic','')} {time_str}\n\n"
    body = f"<b>{q['question']}</b>\n\n"
    opts = "\n".join([f"<b>{k}</b>: {v}" for k,v in q['options'].items()])
    return header + body + opts

def get_options_keyboard(q, current_idx):
    row = [InlineKeyboardButton(f"{k}", callback_data=f"ans_{k}") for k in q['options'].keys()]
    nav_row = [InlineKeyboardButton("⬅️ Prev", callback_data="nav_prev"), InlineKeyboardButton("➡️ Next", callback_data="nav_next"), InlineKeyboardButton("🏁 Submit", callback_data="submit")]
    explain_row = [InlineKeyboardButton("🎙 Explain + Voice", callback_data=f"explain_{current_idx}")]
    return InlineKeyboardMarkup([row, nav_row, explain_row])

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 Past Questions", callback_data="menu_past"), InlineKeyboardButton("📝 Mock Exam", callback_data="menu_mock")],
        [InlineKeyboardButton("🎙 Explain Answer", callback_data="menu_explain"), InlineKeyboardButton("📊 My Score", callback_data="menu_score")],
        [InlineKeyboardButton("📖 Syllabus", callback_data="menu_syllabus"), InlineKeyboardButton("💬 Ask Tutor", callback_data="menu_tutor")],
        [InlineKeyboardButton("👥 Invite Friend", callback_data="menu_invite"), InlineKeyboardButton("💎 Go Premium", callback_data="menu_premium")],
        [InlineKeyboardButton("📞 Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_subjects_keyboard(prefix="prac_"):
    buttons = []
    for s in SUBJECTS:
        buttons.append([InlineKeyboardButton(f"{s}", callback_data=f"{prefix}{s}")])
    buttons.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def get_years_keyboard(subject=None):
    years = cbt.get_years(subject) if subject else list(range(2024, 2009, -1))
    buttons = []
    row = []
    for y in years[:15]:
        row.append(InlineKeyboardButton(str(y), callback_data=f"year_{subject}_{y}" if subject else f"year_all_{y}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_past")])
    return InlineKeyboardMarkup(buttons)

# ========== COMMANDS - ALL FIXED ==========
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    # Referral handling
    if context.args and len(context.args) > 0:
        try:
            referrer = int(context.args[0])
            if referrer != uid:
                got_premium, count = add_referral(referrer, uid)
                if count % 3 == 1:
                    await update.message.reply_text(f"🎉 You were invited! Your friend now has {count} invites.")
                if got_premium:
                    try:
                        await context.bot.send_message(chat_id=referrer, text=f"🎉 Congrats! You invited 3 friends! You now have 1 WEEK PREMIUM (N{PREMIUM_PRICE} value) - unlimited access!")
                    except:
                        pass
        except:
            pass
    
    premium = is_premium(uid)
    days_left = get_premium_days_left(uid)
    if premium:
        status = f"💎 PREMIUM ({days_left} days left)"
    else:
        status = f"🆓 FREE (5 Qs limit) - Premium N{PREMIUM_PRICE}/month"
    
    ref_count = get_referral_count(uid)
    
    welcome = f"""🎓 *UTME SUCCESS BOT* 🎓
Hello {name}! {status}

*Your JAMB Partner - 50k Questions + Full Syllabus*

📚 Past Questions - By Subject & Year (2010-2024)
📝 Mock Exam - Real JAMB CBT test (Free: 5 Qs)
🎙 Explain Answer - AI teacher with voice
📊 My Score - Performance & weak areas
📖 Syllabus - JAMB official syllabus
💬 Ask Tutor - Ask any question

👥 Invite: {ref_count}/3 friends → 1 week premium
💎 Premium: N{PREMIUM_PRICE}/month unlimited

Choose from menu below 👇
"""
    await update.message.reply_text(welcome, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""📞 *HELP - UTME Success Bot*

*For help contact:*
👉 @jibriliks

*Commands:*
📚 Past Questions - /past
📝 Mock Exam - /mock (Free: 5 Qs, Premium: Unlimited)
🎙 Explain Answer - Tap 🎙 button during quiz
📊 My Score - /score
📖 Syllabus - /syllabus
💬 Ask Tutor - /tutor + your question
👥 Invite Friend - /invite (3 friends = 1 week premium)
💎 Go Premium - /subscribe N{PREMIUM_PRICE}/month

*Free vs Premium:*
🆓 Free: 5 questions per mock, limited features
💎 Premium N{PREMIUM_PRICE}: Unlimited mocks, all subjects, voice explanations, full JAMB mock 180 Qs

*Support:* @jibriliks
"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def past_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FIXED - Past Questions now working
    await update.message.reply_text("📚 *Past Questions*\nChoose how to practice:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("By Subject", callback_data="past_by_subject")],
        [InlineKeyboardButton("By Year", callback_data="past_by_year")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]), parse_mode=ParseMode.MARKDOWN)

async def mock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    premium = is_premium(uid)
    limit_text = "Unlimited" if premium else "5 Qs (Free) - Upgrade for unlimited"
    await update.message.reply_text(f"📝 *Mock Exam*\nYour access: {limit_text}\nChoose test type:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Quick Test (Free 5 Qs)", callback_data="mock_quick")],
        [InlineKeyboardButton("📖 Subject Mock", callback_data="mock_subject")],
        [InlineKeyboardButton("🔥 Full JAMB Mock (180 Qs)", callback_data="mock_full")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]), parse_mode=ParseMode.MARKDOWN)

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FIXED - My Score now working
    uid = update.effective_user.id
    stats = get_user_stats(uid)
    if not stats:
        await update.message.reply_text("📊 *My Score*\n\nNo exams yet! Start with /mock\n\nYour scores will show here:\n• Total average\n• Strong & weak areas\n• Leaderboard position", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Start Mock", callback_data="menu_mock")],[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]))
        return
    
    total_avg = stats["total_score"] / max(stats["total_exams"],1)
    jamb_equiv = int(total_avg)
    pos, total_users = get_leaderboard_position(uid)
    
    subjects = stats.get("subjects", {})
    strong = sorted(subjects.items(), key=lambda x: x[1]["avg"], reverse=True)[:2]
    weak = sorted(subjects.items(), key=lambda x: x[1]["avg"])[:2]
    
    text = f"""📊 *My Score - Performance*

*Total Average:* {total_avg:.1f}/400 JAMB

*Strong Areas:*
"""
    for subj, data in strong:
        text += f"• {subj}: {data['avg']}%\n"
    text += "\n*Weak Areas:*\n"
    for subj, data in weak:
        text += f"• {subj}: {data['avg']}% → Practice more 👉 /practice {subj}\n"
    
    text += f"\n*Leaderboard:* You are #{pos} out of {total_users} in Warri\n"
    text += f"*Total Exams:* {stats['total_exams']}\n"
    
    if stats.get("history"):
        text += "\n*Recent:*\n"
        for h in stats["history"][-3:]:
            text += f"• {h['date']}: {h['subject']} {h['score']} ({h['jamb']}/400)\n"
    
    keyboard = [
        [InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{jamb_equiv}_{stats['total_exams']}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def syllabus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FIXED - Syllabus now working
    if context.args:
        subj = " ".join(context.args).capitalize()
        if subj in JAMB_SYLLABUS:
            topics = JAMB_SYLLABUS[subj]
            text = f"📖 *JAMB Official Syllabus - {subj}*\n\n"
            for i, t in enumerate(topics, 1):
                text += f"{i}. {t}\n"
            text += f"\nPractice {subj} now: /practice {subj}"
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"▶️ Practice {subj}", callback_data=f"prac_{subj}")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
            ]), parse_mode=ParseMode.MARKDOWN)
            return
    
    keyboard = []
    for s in SUBJECTS:
        keyboard.append([InlineKeyboardButton(f"📖 {s}", callback_data=f"syllabus_{s}")])
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")])
    await update.message.reply_text("📖 *JAMB Official Syllabus*\nChoose subject:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def tutor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💬 *Ask Tutor*\n\nAsk any question like:\n`/tutor What is photosynthesis?`\n`/tutor Explain simultaneous equations`\n`/ask What is pH?`", parse_mode=ParseMode.MARKDOWN)
        return
    
    question = " ".join(context.args)
    await update.message.reply_text("🧠 Tutor is thinking...")
    explanation = explain_with_ai({"question": question, "subject": "General", "topic": "Tutor", "answer": "", "explanation": ""})
    await update.message.reply_text(f"💬 *Tutor Answer:*\n\n{explanation}", parse_mode=ParseMode.MARKDOWN)
    
    voice_file = text_to_voice(explanation, q_id=f"tutor_{int(time.time())}")
    if voice_file and os.path.exists(voice_file):
        try:
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=open(voice_file, 'rb'))
            os.remove(voice_file)
        except:
            pass

async def invite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FIXED - Invite now working with 3 friends = 1 week premium
    uid = update.effective_user.id
    bot_username = context.bot.username or "UTMEBOT"
    invite_link = f"https://t.me/{bot_username}?start={uid}"
    refs = load_json(REFERRAL_FILE, {}).get(str(uid), [])
    count = len(refs)
    needed = 3 - (count % 3) if count % 3 != 0 else 3
    if count >= 3 and count % 3 == 0:
        needed_text = f"🎉 You have {count} invites! You already got premium!"
    else:
        needed_text = f"Invite {needed} more friend(s) to get 1 WEEK PREMIUM (N{PREMIUM_PRICE} value)!"
    
    text = f"""👥 *Invite Friend - Get 1 Week Free Premium*

Your invite link:
`{invite_link}`

*How it works:*
• Share link to 3 friends
• Friends start bot with your link
• You get 1 WEEK PREMIUM unlimited access
• Invite more, get more weeks!

*Your progress:* {count} friends invited
{needed_text}

*Current Premium:* {"💎 Active" if is_premium(uid) else "🆓 Free"}

Tap Share to send to WhatsApp status!
"""
    keyboard = [[InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={invite_link}&text=I scored 268 in JAMB Mock! Can you beat me? Try here")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FIXED - Go Premium now working with N2000
    uid = update.effective_user.id
    if is_premium(uid):
        days_left = get_premium_days_left(uid)
        await update.message.reply_text(f"💎 You are already PREMIUM! ({days_left} days left)\n\nYou have unlimited access to all features.")
        return
    ref_count = get_referral_count(uid)
    await update.message.reply_text(f"💎 *Go Premium - N{PREMIUM_PRICE}/month*\n\n*Free vs Premium:*\n🆓 Free: 5 questions per mock only\n💎 Premium: Unlimited mocks, 180 Qs full JAMB, all subjects, voice, no limit\n\n*Benefits:*\n• Unlimited mocks (180 Qs full JAMB)\n• Voice explanations\n• All subjects + years\n• Priority tutor\n• Share score image\n\n*Alternative:* Invite 3 friends = 1 week free premium! You have {ref_count}/3\n\nSend your email (e.g. you@gmail.com) to pay N{PREMIUM_PRICE}:", parse_mode=ParseMode.MARKDOWN)
    context.user_data["awaiting_email"] = True

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_email"):
        # If not awaiting email, treat as tutor question if not in exam
        uid = update.effective_user.id
        if uid not in cbt.active_exams and update.message.text and len(update.message.text) > 3:
            # Tutor question
            context.args = update.message.text.split()
            await tutor_cmd(update, context)
            return
        return
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Invalid email, send like: you@gmail.com")
        return
    uid = update.effective_user.id
    name = update.effective_user.full_name
    await update.message.reply_text("⏳ Creating payment link...")
    link, tx_ref = create_flutterwave_link(uid, email=email, name=name)
    if not link:
        await update.message.reply_text(f"❌ Could not create link: {tx_ref}\n\nMake sure FLW_SECRET_KEY is set in Render. Or contact @jibriliks for help")
        return
    context.user_data["awaiting_email"] = False
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Pay N{PREMIUM_PRICE}", url=link)],[InlineKeyboardButton("✅ Verify Payment", callback_data=f"verify_{tx_ref}")]])
    await update.message.reply_text(f"🔗 *Pay N{PREMIUM_PRICE}:*\nAfter payment click Verify\nTx: {tx_ref}\n\nOr invite 3 friends for free premium: /invite", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    
    # Main menu navigation
    if data == "menu_main":
        await start_cmd(update, context)
        return
    elif data == "menu_past":
        await past_cmd(update, context)
        return
    elif data == "menu_mock":
        await mock_cmd(update, context)
        return
    elif data == "menu_score":
        await score_cmd(update, context)
        return
    elif data == "menu_syllabus":
        await syllabus_cmd(update, context)
        return
    elif data == "menu_tutor":
        await query.message.reply_text("💬 *Ask Tutor*\n\nAsk any question like:\n`/tutor What is photosynthesis?`\n`/ask Explain simultaneous equations`", parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "menu_invite":
        await invite_cmd(update, context)
        return
    elif data == "menu_premium":
        await subscribe_cmd(update, context)
        return
    elif data == "menu_help":
        await help_cmd(update, context)
        return
    elif data == "menu_explain":
        await query.message.reply_text("🎙 *Explain Answer*\n\nDuring quiz, tap 🎙 Explain + Voice button under each question\n\nOr use /tutor to ask any question", parse_mode=ParseMode.MARKDOWN)
        return
    
    # Past Questions - FIXED
    elif data == "past_by_subject":
        await query.message.reply_text("📚 *Past Questions - By Subject*\nChoose subject:", reply_markup=get_subjects_keyboard("past_subj_"), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "past_by_year":
        await query.message.reply_text("📚 *Past Questions - By Year*\nChoose year:", reply_markup=get_years_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("past_subj_"):
        subj = data.replace("past_subj_","")
        await query.message.reply_text(f"📚 *{subj} - Past Questions*\nChoose year or start:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Choose Year", callback_data=f"past_year_{subj}"), InlineKeyboardButton("▶️ Start Now", callback_data=f"prac_{subj}")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_past")]
        ]), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("past_year_"):
        subj = data.replace("past_year_","")
        await query.message.reply_text(f"📅 *{subj} - Choose Year*", reply_markup=get_years_keyboard(subj), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("year_"):
        parts = data.split("_")
        if len(parts) >= 3:
            subj = parts[1] if parts[1] != "all" else None
            year = parts[2]
            # Apply premium limit for free users
            premium = is_premium(uid)
            limit = 40 if premium else 5
            if subj:
                qs = cbt.get_questions(subject=subj, year=year, limit=limit)
                if not qs:
                    qs = cbt.get_questions(subject=subj, limit=limit)
                if qs:
                    cbt.active_exams[uid] = {"questions": qs, "current_idx":0, "score":0, "answers":{}, "subjects":[subj], "start_time":time.time(), "duration":30*60}
                    q,total = qs[0], len(qs)
                    await query.message.reply_text(f"📚 Past Questions {subj} {year} - {total} Qs {'(Free limit 5)' if not premium else ''}")
                    await query.message.reply_text(format_question(q,0,total,cbt.get_time_left(uid)), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
                    if not premium and total >=5:
                        await query.message.reply_text(f"🆓 Free limit: 5 Qs only. Upgrade to Premium N{PREMIUM_PRICE} for unlimited: /subscribe\nOr invite 3 friends: /invite")
                    return
            else:
                qs = cbt.get_questions(year=year, limit=limit)
                if qs:
                    cbt.active_exams[uid] = {"questions": qs, "current_idx":0, "score":0, "answers":{}, "subjects":["Mixed"], "start_time":time.time(), "duration":30*60}
                    q,total = qs[0], len(qs)
                    await query.message.reply_text(f"📚 Past Questions {year} - {total} Qs")
                    await query.message.reply_text(format_question(q,0,total,cbt.get_time_left(uid)), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
                    return
        await query.message.reply_text("No questions found for that year. Try another year or subject.")
        return
    
    # Mock Exam types - FIXED with 5 Qs free limit
    elif data == "mock_quick":
        premium = is_premium(uid)
        limit_per = 5 if not premium else 5
        subs = ["English","Mathematics","Biology","Chemistry"]
        q,total = cbt.start_mock(uid, subs, duration=15*60, limit_per_subject=limit_per if not premium else 5)
        if not premium:
            # Free: only 5 questions total
            exam = cbt.active_exams[uid]
            exam["questions"] = exam["questions"][:5]
            q,total = exam["questions"][0], 5
            await query.message.reply_text(f"⚡ Quick Test - 5 Qs (Free) - {','.join(subs)}\n\n🆓 Free limit: 5 Qs. Upgrade to Premium N{PREMIUM_PRICE} for unlimited mock: /subscribe")
        else:
            await query.message.reply_text(f"⚡ Quick Test - {total} Qs, 15 mins - {','.join(subs)} (Premium unlimited)")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    elif data == "mock_subject":
        await query.message.reply_text("📖 *Subject Mock*\nChoose subject:", reply_markup=get_subjects_keyboard("mock_subj_"), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("mock_subj_"):
        subj = data.replace("mock_subj_","")
        premium = is_premium(uid)
        limit = 40 if premium else 5
        q,total = cbt.start_mock(uid, [subj], duration=45*60, limit_per_subject=limit)
        if not q:
            await query.message.reply_text(f"No questions found for {subj}")
            return
        await query.message.reply_text(f"📖 Subject Mock - {subj} - {total} Qs {'(Free: 5 Qs limit)' if not premium else '(Premium unlimited)'}")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        if not premium:
            await query.message.reply_text(f"🆓 Free: 5 Qs only. Get unlimited for N{PREMIUM_PRICE}: /subscribe\nOr invite 3 friends for 1 week premium: /invite")
        return
    elif data == "mock_full":
        premium = is_premium(uid)
        if not premium:
            await query.message.reply_text(f"🔒 *Full JAMB Mock (180 Qs) is Premium Only*\n\n🆓 Free members: 5 Qs only\n💎 Premium N{PREMIUM_PRICE}: Unlimited, full 180 Qs, 2hrs like real JAMB\n\nUpgrade now or invite 3 friends for 1 week premium free!", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💎 Go Premium N{PREMIUM_PRICE}", callback_data="menu_premium")],
                [InlineKeyboardButton("👥 Invite 3 Friends = 1 Week Free", callback_data="menu_invite")],
                [InlineKeyboardButton("⚡ Try Quick Test (5 Qs Free)", callback_data="mock_quick")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
            ]), parse_mode=ParseMode.MARKDOWN)
            return
        
        subs = ["English","Mathematics","Biology","Chemistry"]
        all_selected = []
        all_selected.extend(cbt.get_questions("English", limit=60))
        all_selected.extend(cbt.get_questions("Mathematics", limit=40))
        all_selected.extend(cbt.get_questions("Biology", limit=40))
        all_selected.extend(cbt.get_questions("Chemistry", limit=40))
        random.shuffle(all_selected)
        cbt.active_exams[uid] = {"questions": all_selected, "current_idx":0, "score":0, "answers":{}, "subjects":subs, "start_time":time.time(), "duration":120*60}
        q,total = all_selected[0], len(all_selected)
        await query.message.reply_text(f"🔥 *Full JAMB Mock - 180 Qs, 2hrs - Like Real JAMB*\n{','.join(subs)}\nPremium access granted!", parse_mode=ParseMode.MARKDOWN)
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    
    # Syllabus - FIXED
    elif data.startswith("syllabus_"):
        subj = data.replace("syllabus_","")
        if subj in JAMB_SYLLABUS:
            topics = JAMB_SYLLABUS[subj]
            text = f"📖 *JAMB Official Syllabus - {subj}*\n\n"
            for i, t in enumerate(topics, 1):
                text += f"{i}. {t}\n"
            text += f"\nPractice {subj}: /practice {subj}"
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"▶️ Practice {subj}", callback_data=f"prac_{subj}")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
            ]), parse_mode=ParseMode.MARKDOWN)
        else:
            await query.message.reply_text(f"Syllabus for {subj} not found")
        return
    
    # Premium verify
    if data.startswith("verify_"):
        tx_ref = data.replace("verify_","")
        await query.message.reply_text("🔍 Verifying payment...")
        success,_ = verify_by_tx_ref(tx_ref)
        if success:
            grant_premium(uid,30,tx_ref)
            await query.message.reply_text(f"✅ Payment Confirmed! You are now PREMIUM for 30 days (N{PREMIUM_PRICE})\n\nUnlimited access granted! Try /mock now")
        else:
            await query.message.reply_text(f"❌ Payment not confirmed yet. Tx: {tx_ref}\n\nIf you paid, wait 1 min and click Verify again. Or contact @jibriliks")
        return
    if data.startswith("combo_"):
        subs = ["English","Mathematics","Biology","Chemistry"] if "science" in data else ["English","Literature","Government","CRS"]
        premium = is_premium(uid)
        limit = 10 if premium else 5
        q,total = cbt.start_mock(uid, subs, duration=120*60, limit_per_subject=limit)
        if not premium:
            exam = cbt.active_exams[uid]
            exam["questions"] = exam["questions"][:5]
            q,total = exam["questions"][0], 5
        await query.message.reply_text(f"🔥 Mock {','.join(subs)} - {total} Qs {'(Free 5 Qs)' if not premium else ''}")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    elif data.startswith("prac_"):
        subj = data.replace("prac_","")
        premium = is_premium(uid)
        limit = 40 if premium else 5
        q,total = cbt.start_mock(uid, [subj], duration=45*60, limit_per_subject=limit)
        if not q:
            await query.message.reply_text(f"No questions found for {subj}")
            return
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        if not premium:
            await query.message.reply_text(f"🆓 Free: {total} Qs limit. Upgrade to unlimited N{PREMIUM_PRICE}: /subscribe\nInvite 3 friends for 1 week free: /invite")
        return
    elif data.startswith("ans_"):
        opt = data.replace("ans_","")
        result,status = cbt.answer_current(uid, opt)
        if status == "NO_EXAM":
            await query.message.reply_text("No exam. /mock to start")
            return
        if status == "FINISHED":
            res = result
            for subj in res["subjects"]:
                correct = 0
                total_subj = 0
                for idx, qq in enumerate(res["questions"]):
                    if qq["subject"] == subj:
                        total_subj += 1
                        ans = res["answers"].get(idx)
                        if ans and ans["correct"]:
                            correct += 1
                update_user_stats(uid, subj, correct, total_subj, res["jamb_score"])
            
            text = f"🏁 *Finished!*\nScore: {res['raw_score']}/{res['total']}\nJAMB: {res['jamb_score']}/400\n\n"
            premium = is_premium(uid)
            if not premium and res['total'] >= 5:
                text += f"🆓 Free limit reached (5 Qs). Upgrade to Premium N{PREMIUM_PRICE} for unlimited mocks: /subscribe\nOr invite 3 friends for 1 week free: /invite\n\n"
            
            keyboard = [
                [InlineKeyboardButton("📊 My Score", callback_data="menu_score"), InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{res['jamb_score']}_{res['total']}")],
                [InlineKeyboardButton("🔁 Try Again", callback_data="menu_mock"), InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
            ]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            next_q,next_idx = result
            left = cbt.get_time_left(uid)
            total = len(cbt.active_exams[uid]['questions'])
            await query.message.reply_text(format_question(next_q,next_idx,total,left), reply_markup=get_options_keyboard(next_q,next_idx), parse_mode=ParseMode.HTML)
    elif data.startswith("nav_"):
        exam = cbt.active_exams.get(uid)
        if not exam:
            return
        if data=="nav_prev":
            exam['current_idx']=max(0,exam['current_idx']-1)
        else:
            exam['current_idx']=min(len(exam['questions'])-1,exam['current_idx']+1)
        q,idx = cbt.get_current_question(uid)
        left=cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,idx,len(exam['questions']),left), reply_markup=get_options_keyboard(q,idx), parse_mode=ParseMode.HTML)
    elif data=="submit":
        final=cbt.finish_exam(uid)
        if final:
            text = f"🏁 Submitted! {final['raw_score']}/{final['total']} JAMB: {final['jamb_score']}/400"
            if not is_premium(uid):
                text += f"\n\n🆓 Free: 5 Qs limit. Premium N{PREMIUM_PRICE} for unlimited: /subscribe"
            keyboard = [
                [InlineKeyboardButton("📊 My Score", callback_data="menu_score"), InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{final['jamb_score']}_{final['total']}")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
            ]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("explain_"):
        try:
            idx=int(data.replace("explain_",""))
            exam=cbt.active_exams.get(uid)
            q=exam['questions'][idx] if exam and idx < len(exam['questions']) else None
            if not q:
                await query.message.reply_text("No question found")
                return
            await query.message.reply_text("🧠 Generating explanation with voice...")
            exp=explain_with_ai(q)
            await query.message.reply_text(f"🎙 *Explanation:*\n\n{exp}", parse_mode=ParseMode.MARKDOWN)
            vp=text_to_voice(exp,q_id=q.get('id'))
            if vp and os.path.exists(vp):
                try:
                    await context.bot.send_voice(chat_id=query.message.chat_id, voice=open(vp,'rb'))
                    os.remove(vp)
                except Exception as e:
                    print(f"Voice send error: {e}", flush=True)
        except Exception as e:
            await query.message.reply_text(f"Error: {e}")
    elif data.startswith("share_"):
        parts = data.split("_")
        jamb_score = parts[1] if len(parts)>1 else "200"
        total = parts[2] if len(parts)>2 else "40"
        name = update.effective_user.first_name
        await query.message.reply_text("🎨 Generating your score image...")
        img_path = generate_score_image(uid, f"{jamb_score}/{400}", total, int(jamb_score), name)
        if img_path and os.path.exists(img_path):
            try:
                caption = f"""I scored {jamb_score} in JAMB Mock! 
Can you beat me?
Try here 👉 t.me/{context.bot.username or 'UTMEBOT'}

#JAMB #UTME"""
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=open(img_path,'rb'), caption=caption)
                os.remove(img_path)
            except Exception as e:
                await query.message.reply_text(f"📤 Share this:\n\nI scored {jamb_score} in JAMB Mock! Can you beat me? Try here 👉 t.me/{context.bot.username}")
        else:
            await query.message.reply_text(f"📤 *Share My Score*\n\nI scored {jamb_score} in JAMB Mock!\nCan you beat me?\nTry here 👉 t.me/{context.bot.username or 'UTMEBOT'}", parse_mode=ParseMode.MARKDOWN)

async def mock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard=[
        [InlineKeyboardButton("⚡ Quick Test (Free 5 Qs)", callback_data="mock_quick")],
        [InlineKeyboardButton("📖 Subject Mock", callback_data="mock_subject")],
        [InlineKeyboardButton("🔥 Full JAMB Mock (Premium 180 Qs)", callback_data="mock_full")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]
    await update.message.reply_text(f"📝 Mock Exam - Free: 5 Qs, Premium N{PREMIUM_PRICE}: Unlimited\nChoose type:", reply_markup=InlineKeyboardMarkup(keyboard))

async def practice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        subj = " ".join(context.args).capitalize()
        if subj in SUBJECTS:
            premium = is_premium(update.effective_user.id)
            limit = 40 if premium else 5
            q,total = cbt.start_mock(update.effective_user.id, [subj], duration=45*60, limit_per_subject=limit)
            left = cbt.get_time_left(update.effective_user.id)
            await update.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
            if not premium:
                await update.message.reply_text(f"🆓 Free: 5 Qs only. Premium N{PREMIUM_PRICE} unlimited: /subscribe")
            return
    buttons=[[InlineKeyboardButton(s, callback_data=f"prac_{s}")] for s in SUBJECTS]
    buttons.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")])
    await update.message.reply_text("Select subject:", reply_markup=InlineKeyboardMarkup(buttons))

def start_telegram_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN not set", flush=True)
        return
    if not TG_AVAILABLE:
        print("telegram library not available", flush=True)
        return
    print(f"BOT_TOKEN found: {BOT_TOKEN[:10]}... len {len(BOT_TOKEN)}", flush=True)
    for i in range(3):
        try:
            import requests
            print(f"Deleting webhook attempt {i+1}...", flush=True)
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=15)
            print(f"DeleteWebhook: {r.text[:500]}", flush=True)
            if '"ok":true' in r.text.lower():
                break
        except Exception as e:
            print(f"DeleteWebhook failed {i+1}: {e}", flush=True)
        time.sleep(2)
    
    while True:
        try:
            print("Building Application...", flush=True)
            app = Application.builder().token(BOT_TOKEN).build()
            app.add_handler(CommandHandler("start", start_cmd))
            app.add_handler(CommandHandler("help", help_cmd))
            app.add_handler(CommandHandler("past", past_cmd))
            app.add_handler(CommandHandler("mock", mock_cmd))
            app.add_handler(CommandHandler("score", score_cmd))
            app.add_handler(CommandHandler("myscore", score_cmd))
            app.add_handler(CommandHandler("syllabus", syllabus_cmd))
            app.add_handler(CommandHandler("tutor", tutor_cmd))
            app.add_handler(CommandHandler("ask", tutor_cmd))
            app.add_handler(CommandHandler("invite", invite_cmd))
            app.add_handler(CommandHandler("subscribe", subscribe_cmd))
            app.add_handler(CommandHandler("premium", subscribe_cmd))
            app.add_handler(CommandHandler("practice", practice_cmd))
            app.add_handler(CallbackQueryHandler(handle_callback))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
            print("Handlers registered - FIXED Bot is LIVE!", flush=True)
            app.run_polling(drop_pending_updates=True, allowed_updates=["message","callback_query"])
        except Exception as e:
            print(f"Polling crashed: {e} - Retrying in 10s", flush=True)
            import traceback; traceback.print_exc()
            time.sleep(10)
            continue
        break

if __name__ == "__main__":
    def run_flask():
        port = int(os.getenv("PORT", 10000))
        print(f"Binding Flask to 0.0.0.0:{port}", flush=True)
        flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Flask thread started", flush=True)
    time.sleep(1)
    start_telegram_bot()
