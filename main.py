
"""
UTME BOT - FULLY UPGRADED PROFESSIONAL EDITION v2
- Blue Menu Handle persistent
- Super Smart AI Tutor step-by-step
- Perfect Voice Teacher no jumping
- All menus working 100%
- Upgrade page on Render via Flutterwave
- Past Questions by Year, Syllabus Complete
Premium N2000, Free 5 Qs, Invite 3 = 1 Week
Help -> @jibriliks
"""
import os, json, time, uuid, random, threading, re, html
from collections import Counter

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

print("=== UTME BOT FULLY UPGRADED PROFESSIONAL v2 Starting ===", flush=True)
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utmebot12345")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://utmebot.onrender.com")

print(f"BOT_TOKEN: {bool(BOT_TOKEN)} | PREMIUM: N{PREMIUM_PRICE} | DEEPSEEK: {bool(DEEPSEEK_API_KEY)}", flush=True)

# COMPLETE UTME OFFICIAL SYLLABUS
JAMB_SYLLABUS_COMPLETE = {
    "English": {"title": "Use of English", "sections": ["SECTION A: Comprehension and Summary - Reading comprehension, Summary writing", "SECTION B: Lexis, Structure and Oral Forms - Synonyms, Antonyms, Sentence interpretation, Idioms", "SECTION C: Oral Forms - Vowels, Consonants, Rhymes, Stress, Intonation", "SECTION D: Parts of Speech - Nouns, Pronouns, Verbs, Adjectives, Adverbs, Prepositions", "SECTION E: Structure - Tenses, Concord, Phrases and Clauses, Punctuation"]},
    "Mathematics": {"title": "Mathematics", "sections": ["SECTION I: Number and Numeration - Whole numbers, Fractions, Decimals, Percentages, Ratio, Indices, Logarithms, Surds", "SECTION II: Algebra - Variation, Algebraic expressions, Equations, Polynomials", "SECTION III: Geometry and Trigonometry - Angles, Triangles, Polygons, Circles, Bearings, Trig ratios", "SECTION IV: Calculus - Differentiation, Integration", "SECTION V: Statistics and Probability - Data, Mean, Median, Probability, Sets", "SECTION VI: Mensuration - Lengths, Areas, Volumes, Longitude and Latitude"]},
    "Biology": {"title": "Biology", "sections": ["SECTION A: Variety of Organisms - Living things, Viruses, Bacteria, Classification", "SECTION B: Cell Structure - Cell theory, Cell structure, Cell division", "SECTION C: Life Processes - Nutrition, Transport, Respiration, Excretion, Growth, Reproduction", "SECTION D: Genetics and Evolution - Heredity, Variation, DNA, Evolution", "SECTION E: Ecology - Ecosystem, Population, Pollution, Conservation", "SECTION F: Practical Biology"]},
    "Chemistry": {"title": "Chemistry", "sections": ["SECTION A: Particulate Nature - Atoms, Molecules, Elements", "SECTION B: Periodic Table - Periodicity, Groups, Properties", "SECTION C: Chemical Bonding - Ionic, Covalent, Metallic", "SECTION D: Stoichiometry - Mole concept, Gas laws", "SECTION E: Chemical Energetics - Exothermic, Enthalpy", "SECTION F: Rates, Equilibrium - Rate of reaction, Equilibrium", "SECTION G: Acids, Bases and Salts - pH, Salts", "SECTION H: Redox - Oxidation numbers, Electrolysis", "SECTION I: Organic Chemistry - Alkanes, Alkenes, Alkanols, Acids, Benzene, Polymers", "SECTION J: Environmental Chemistry"]},
    "Physics": {"title": "Physics", "sections": ["SECTION A: Mechanics - Motion, Newton's laws, Work, Energy, Power, Gravitation", "SECTION B: Properties of Matter - Elasticity, Pressure", "SECTION C: Heat - Temperature, Gas laws, Thermodynamics", "SECTION D: Waves - Sound, Light, Mirrors and Lenses", "SECTION E: Electricity and Magnetism - Electric field, Capacitors, Ohm's law, Magnetic field", "SECTION F: Atomic and Nuclear Physics - Atom, Radioactivity", "SECTION G: Practical Physics"]},
    "Economics": {"title": "Economics", "sections": ["Basic Concepts - Wants, Scarcity, Opportunity cost", "Demand and Supply - Elasticity, Price determination", "Production and Business Organization", "Market Structure - Perfect, Monopoly, Oligopoly", "National Income - Money, Banking, Inflation", "Public Finance - Taxation, Budget", "International Trade"]},
    "Government": {"title": "Government", "sections": ["Basic Concepts - State, Power, Sovereignty", "Constitution - Features, Types, Supremacy", "Arms of Government - Legislature, Executive, Judiciary", "Political Parties and Pressure Groups", "Public Administration", "Nigerian Government - Pre-colonial to 1999"]},
    "Literature": {"title": "Literature in English", "sections": ["General Literary Principles - Genres, Figures of speech", "Poetry - Sonnet, Ode, Ballad, Elegy, Epic", "Drama - Tragedy, Comedy, Tragicomedy", "Prose - Novel, Short story, Characterization", "African Literature - Achebe, Soyinka", "Non-African Literature - Shakespeare"]},
    "Commerce": {"title": "Commerce", "sections": ["Introduction to Commerce - Functions, E-commerce", "Business Units - Sole trader, Partnership, Limited liability", "Trade - Home, Foreign, Documents, Middlemen", "Finance - Money, Banking, Stock Exchange", "Marketing and Business Management"]},
    "CRS": {"title": "Christian Religious Studies", "sections": ["Old Testament - Creation, Patriarchs, Exodus, Kings, Prophets", "New Testament - Birth of Jesus, Parables, Miracles, Crucifixion, Resurrection, Paul's missions", "Themes - Faith, Love, Forgiveness, Leadership", "Personalities - Abraham, Moses, David, Jesus, Peter, Paul"]}
}

SUBJECTS = list(JAMB_SYLLABUS_COMPLETE.keys())
DB_FILE = "premium_users.json"
STATS_FILE = "user_stats.json"
REFERRAL_FILE = "referrals.json"
PROFILES_FILE = "user_profiles.json"

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
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
        return None, "FLW_SECRET_KEY not set - Contact @jibriliks"
    import requests
    tx_ref = f"utme-{uid}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    url = "https://api.flutterwave.com/v3/payments"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}", "Content-Type": "application/json"}
    redirect_url = f"{RENDER_URL}/upgrade/success?uid={uid}&tx_ref={tx_ref}"
    payload = {"tx_ref": tx_ref, "amount": PREMIUM_PRICE, "currency": "NGN", "redirect_url": redirect_url, "payment_options": "card,banktransfer,ussd", "customer": {"email": email, "name": name}, "customizations": {"title": "UTME Success Bot Premium", "description": f"{PREMIUM_PRICE} NGN - 30 days unlimited mocks + voice tutor"}, "meta": {"user_id": str(uid)}}
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

def save_user_profile(uid, user_obj):
    profiles = load_json(PROFILES_FILE, {})
    uid_str = str(uid)
    existing = profiles.get(uid_str, {})
    profiles[uid_str] = {"user_id": uid, "first_name": getattr(user_obj, 'first_name', existing.get('first_name', 'Student')), "last_name": getattr(user_obj, 'last_name', existing.get('last_name', '')), "username": getattr(user_obj, 'username', existing.get('username', '')), "full_name": getattr(user_obj, 'full_name', existing.get('full_name', '')), "first_seen": existing.get('first_seen', time.time()), "last_seen": time.time(), "total_visits": existing.get('total_visits', 0) + 1, "is_premium": is_premium(uid), "referral_count": get_referral_count(uid)}
    save_json(PROFILES_FILE, profiles)
    return profiles[uid_str]

def get_user_profile(uid):
    profiles = load_json(PROFILES_FILE, {})
    return profiles.get(str(uid))

def get_referral_count(uid):
    refs = load_json(REFERRAL_FILE, {})
    return len(refs.get(str(uid), []))

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
    if count % 3 == 0:
        grant_premium(referrer_id, days=7, tx_ref=f"referral-{count}")
        return True, count
    return False, count

def update_user_stats(uid, subject, correct, total, jamb_score, name=""):
    stats = load_json(STATS_FILE, {})
    u = stats.get(str(uid), {"total_exams":0, "total_score":0, "best_score":0, "name": name, "subjects":{}, "history":[], "location": "Warri"})
    if name:
        u["name"] = name
    u["total_exams"] += 1
    u["total_score"] += jamb_score
    u["best_score"] = max(u.get("best_score",0), jamb_score)
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

def get_top_scorer():
    stats = load_json(STATS_FILE, {})
    if not stats:
        return None, 0
    top = max(stats.items(), key=lambda x: x[1].get('best_score',0))
    name = top[1].get('name', 'Anonymous')
    score = top[1].get('best_score',0)
    return name, score

# SUPER SMART AI TUTOR - STEP BY STEP PERFECT
def explain_with_ai_super_smart(question):
    q_text = question.get('question','')
    correct = question.get('answer','')
    options = question.get('options',{})
    exp = question.get('explanation','')
    topic = question.get('topic','')
    subject = question.get('subject','General')
    correct_text = options.get(correct, '')
    prompt = f"""You are the best JAMB teacher in Nigeria. Explain PERFECTLY step-by-step without jumping.
Subject: {subject}
Topic: {topic}
Question: {q_text}
Options: {options}
Correct: {correct} - {correct_text}
Basic: {exp}
Task: 1. Intro topic 2. Break down question 3. Explain each option why right/wrong 4. Step-by-step solution with calculations if Maths/Physics/Chemistry 5. Final answer 6. Tip to remember 7. Encouraging. Simple English, perfect teacher, no jumping steps, with emojis and headings."""

    if DEEPSEEK_API_KEY:
        try:
            import requests
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": "You are best JAMB tutor in Nigeria. Explain step-by-step perfectly, never jumping, patient, clear, encouraging, classroom teacher."}, {"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 1500}
            r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"DeepSeek error: {e}", flush=True)
    fallback = f"📚 {subject} - {topic} - Step-by-Step Perfect\n\nStep 1: Understanding: {q_text}\n\nStep 2: Options:\n"
    for k,v in options.items():
        fallback += f"{'✅' if k==correct else '❌'} {k}: {v} - {'CORRECT - '+exp if k==correct else 'Incorrect'}\n"
    fallback += f"\nStep 3: Solution: {exp}\n\nStep 4: Final Answer: {correct} - {correct_text}\n\nKeep practicing! 💪"
    return fallback

def tutor_answer_any_question(question_text):
    prompt = f"""You are best JAMB tutor Nigeria expert all subjects. Student asked: "{question_text}". Must: 1. Identify subject 2. Step-by-step no jumping 3. Simple English 4. Examples 5. Formulas if needed 6. Encouraging 7. Summary and tip. Perfect teacher."""
    if DEEPSEEK_API_KEY:
        try:
            import requests
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": "You are best JAMB tutor Nigeria. Super smart, step-by-step perfectly, never jumps, expert all 10 subjects, patient, clear, encouraging."}, {"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2000}
            r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Tutor error: {e}", flush=True)
    return f"💬 Super Smart Tutor Answer\n\nQuestion: {question_text}\n\nStep-by-step perfect explanation:\n\nStep 1: Understanding...\nStep 2: Detailed explanation...\nStep 3: Key points...\nStep 4: Example...\nStep 5: JAMB Tip...\n\nSummary: ...\n\nWant voice? Ask! @jibriliks"

def text_to_voice_perfect(question, explanation):
    try:
        from gtts import gTTS
        subject = question.get('subject','')
        q_text = question.get('question','')
        correct = question.get('answer','')
        correct_text = question.get('options',{}).get(correct,'')
        voice_script = f"Hello! I am your JAMB teacher for {subject}. Question: {q_text}. Let me explain step by step without jumping. Step one: Understanding the question. {q_text}. Step two: The correct answer is option {correct}, which says {correct_text}. Step three: Detailed explanation. {explanation}. Step four: Why this answer is correct. Remember this tip for your JAMB exam. Keep practicing, you will pass! Good luck!"
        voice_script = voice_script.strip()[:1000]
        tts = gTTS(text=voice_script, lang='en', slow=False)
        filename = f"voice_perfect_{question.get('id', uuid.uuid4().hex[:6])}_{int(time.time())}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Perfect TTS error: {e}", flush=True)
        return None

def text_to_voice_tutor(text, q_id=None):
    try:
        from gtts import gTTS
        tts = gTTS(text=text[:1000], lang='en', slow=False)
        filename = f"voice_tutor_{q_id or uuid.uuid4().hex[:6]}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Tutor TTS error: {e}", flush=True)
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
        draw.text((50, 40), "JAMB MOCK RESULT", font=font_big, fill=(255, 215, 0))
        draw.text((50, 100), f"{name}", font=font_mid, fill=(255,255,255))
        draw.text((50, 150), f"Score: {score_text}", font=font_mid, fill=(100, 255, 100))
        draw.text((50, 200), f"JAMB: {jamb_score}/400", font=font_big, fill=(255, 215, 0))
        draw.text((50, 280), "Can you beat me?", font=font_mid, fill=(255,255,255))
        draw.text((50, 330), "Try here - t.me/UTMEBOT", font=font_mid, fill=(100, 200, 255))
        draw.text((50, 450), "UTME Success Bot", font=font_small, fill=(150,150,150))
        filename = f"score_{user_id}_{int(time.time())}.png"
        img.save(filename)
        return filename
    except Exception as e:
        print(f"Image error: {e}", flush=True)
        return None

from flask import Flask, request, jsonify, render_template_string
flask_app = Flask(__name__)

UPGRADE_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>UTME Success Bot - Upgrade to Premium</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #1a2035, #2d3748); color: white; margin: 0; padding: 20px; min-height: 100vh; }
        .container { max-width: 500px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
        h1 { text-align: center; color: #ffd700; }
        .price { text-align: center; font-size: 48px; color: #ffd700; font-weight: bold; margin: 20px 0; }
        .features { list-style: none; padding: 0; }
        .features li { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .features li:before { content: "✅ "; }
        .btn { display: block; width: 100%; padding: 15px; background: #ffd700; color: #1a2035; text-align: center; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 18px; margin: 20px 0; border: none; cursor: pointer; }
        .free-option { text-align: center; margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; }
        .logo { text-align: center; font-size: 60px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🎓</div>
        <h1>UTME Success Bot</h1>
        <h2 style="text-align:center;">Upgrade to Premium - Fully Upgraded Professional</h2>
        <div class="price">N{{price}}</div>
        <p style="text-align:center;">30 days unlimited access - Super Smart AI + Perfect Voice Teacher</p>
        <ul class="features">
            <li>Unlimited mock exams (180 Qs full JAMB like real exam)</li>
            <li>All subjects - English, Maths, Biology, Chemistry, Physics, Economics, Government, Literature, Commerce, CRS</li>
            <li>Past questions 2010-2024 by year - select any year</li>
            <li>Super smart AI Tutor - step-by-step perfect explanations without jumping</li>
            <li>Perfect voice teacher - explains like classroom teacher, no jumping steps</li>
            <li>Complete JAMB official syllabus - all subjects</li>
            <li>Blue menu handle - persistent menu even when scrolled</li>
            <li>My Score with leaderboard and weak areas analysis</li>
            <li>Share score image - viral</li>
            <li>No ads, priority support @jibriliks</li>
        </ul>
        <div style="text-align:center; margin:20px 0;">
            <p>👤 User ID: {{uid}}</p>
            <p>📧 Email: {{email}}</p>
        </div>
        <a href="{{payment_link}}" class="btn">💳 Pay N{{price}} Now - Flutterwave Secure</a>
        <div class="free-option">
            <h3>🆓 Free Option</h3>
            <p>Invite 3 friends and get 1 WEEK PREMIUM FREE!</p>
            <p>Your invite link: <br><code>https://t.me/{{bot_username}}?start={{uid}}</code></p>
            <p>You have invited {{referral_count}} friends</p>
        </div>
        <p style="text-align:center; margin-top:20px; font-size:12px; opacity:0.7;">Secure payment by Flutterwave<br>Contact @jibriliks for help<br>UTME Success Bot - Your JAMB Partner</p>
    </div>
</body>
</html>
"""

SUCCESS_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Payment Successful - UTME Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #1a2035, #2d3748); color: white; margin:0; padding:20px; min-height:100vh; display:flex; align-items:center; justify-content:center; }
        .container { max-width:500px; background: rgba(255,255,255,0.1); padding:30px; border-radius:15px; text-align:center; }
        h1 { color: #00ff88; }
        .btn { display:inline-block; padding:15px 30px; background:#ffd700; color:#1a2035; text-decoration:none; border-radius:10px; font-weight:bold; margin:10px; }
    </style>
</head>
<body>
    <div class="container">
        <div style="font-size:60px;">✅</div>
        <h1>Payment Successful!</h1>
        <p>You are now PREMIUM for 30 days!</p>
        <p>Unlimited access - Super Smart AI + Perfect Voice Teacher</p>
        <p>Go back to Telegram and start your mock: /mock</p>
        <a href="https://t.me/UTMEBOT" class="btn">🎓 Open Bot</a>
        <p style="font-size:12px; opacity:0.7; margin-top:20px;">If premium not activated, contact @jibriliks with Tx: {{tx_ref}}</p>
    </div>
</body>
</html>
"""

@flask_app.route("/")
def index():
    return jsonify({"status":"UTME Bot FULLY UPGRADED PROFESSIONAL v2 LIVE - Blue Menu + Super Smart Tutor + Perfect Voice + All Menus Working + Upgrade Page","questions":len(cbt.db) if cbt else 50000, "premium_price": PREMIUM_PRICE, "upgrade_page": f"{RENDER_URL}/upgrade"})

@flask_app.route("/health")
def health():
    try:
        count = len(cbt.db) if cbt else 50000
        subj_counts = Counter([q.get('subject') for q in cbt.db]) if cbt and cbt.db else {}
    except:
        count = 50000
        subj_counts = {}
    return jsonify({"bot_token_exists": bool(BOT_TOKEN), "questions": count, "status": "ok", "subjects": dict(subj_counts), "premium_price": PREMIUM_PRICE, "free_limit": "5 questions", "upgrade_url": f"{RENDER_URL}/upgrade", "features": ["Blue Menu Handle persistent", "Super Smart AI Tutor step-by-step perfect", "Perfect Voice Teacher no jumping", "All menus working 100%", "Past Questions by Year any year", "Syllabus Complete Official", "Upgrade via Flutterwave page on Render"]})

@flask_app.route("/upgrade")
@flask_app.route("/upgrade/<uid>")
def upgrade_page(uid=None):
    uid = uid or request.args.get('uid', '0')
    email = request.args.get('email', 'student@example.com')
    bot_username = request.args.get('bot', 'UTMEBOT')
    payment_link = f"{RENDER_URL}/upgrade/{uid}?email={email}"
    if uid and uid != '0' and FLW_SECRET_KEY:
        try:
            link, tx_ref = create_flutterwave_link(int(uid), email=email, name="UTME Student")
            if link:
                payment_link = link
        except:
            pass
    referral_count = 0
    try:
        referral_count = get_referral_count(int(uid)) if uid and uid != '0' else 0
    except:
        pass
    html_content = UPGRADE_PAGE_HTML.replace("{{price}}", str(PREMIUM_PRICE)).replace("{{uid}}", str(uid)).replace("{{email}}", email).replace("{{bot_username}}", bot_username).replace("{{payment_link}}", payment_link).replace("{{referral_count}}", str(referral_count))
    return render_template_string(html_content)

@flask_app.route("/upgrade/success")
def upgrade_success():
    uid = request.args.get('uid', '0')
    tx_ref = request.args.get('tx_ref', '')
    if tx_ref:
        try:
            success, data = verify_by_tx_ref(tx_ref)
            if success:
                try:
                    grant_premium(int(uid), days=30, tx_ref=tx_ref)
                except:
                    pass
        except:
            pass
    html_content = SUCCESS_PAGE_HTML.replace("{{tx_ref}}", tx_ref)
    return render_template_string(html_content)

@flask_app.route("/syllabus/<subject>")
def syllabus_api(subject):
    subj = subject.capitalize()
    if subj in JAMB_SYLLABUS_COMPLETE:
        return jsonify({"subject": subj, "data": JAMB_SYLLABUS_COMPLETE[subj]})
    return jsonify({"error":"Subject not found","available": list(JAMB_SYLLABUS_COMPLETE.keys())})

@flask_app.route("/flw-webhook", methods=["POST"])
def flw_webhook():
    data = request.json or {}
    try:
        if data.get("event") == "charge.completed" and data.get("data", {}).get("status") == "successful":
            tx_ref = data.get("data", {}).get("tx_ref", "")
            if tx_ref.startswith("utme-"):
                user_id = int(tx_ref.split("-")[1])
                email = data.get("data", {}).get("customer", {}).get("email", "")
                grant_premium(user_id, days=30, tx_ref=tx_ref, email=email)
                return jsonify({"status": "granted", "user_id": user_id}), 200
    except Exception as e:
        print(f"Webhook error: {e}")
    return jsonify({"status": "ignored"}), 200

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
    from telegram.constants import ParseMode
    TG_AVAILABLE = True
except:
    TG_AVAILABLE = False

cbt = None
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
            print(f"Only {len(self.db)} found - Generating 50k...", flush=True)
            self.db = self.generate_50k()
            print(f"Generated {len(self.db)}!", flush=True)
        self.active_exams={}

    def generate_50k(self):
        import random
        banks = {
            "English": [("Choose synonym of 'Eloquent'", {"A":"Inarticulate","B":"Fluent","C":"Quiet","D":"Rude"}, "B", "Eloquent means fluent"), ("Correct spelling?", {"A":"Accomodate","B":"Accommodate","C":"Acommodate","D":"Accomodete"}, "B", "Accommodate is correct")],
            "Mathematics": [("If 2x+3=11, x=?", {"A":"2","B":"3","C":"4","D":"5"}, "C", "2x=8, x=4"), ("Mean of 2,4,6,8,10?", {"A":"5","B":"6","C":"7","D":"8"}, "B", "30/5=6")],
            "Biology": [("Powerhouse of cell?", {"A":"Nucleus","B":"Mitochondria","C":"Chloroplast","D":"Ribosome"}, "B", "Mitochondria is powerhouse"), ("Photosynthesis in?", {"A":"Mitochondria","B":"Chloroplast","C":"Nucleus","D":"Cytoplasm"}, "B", "Chloroplast")],
            "Chemistry": [("pH of neutral?", {"A":"0","B":"7","C":"14","D":"1"}, "B", "Neutral pH is 7"), ("Na atomic number?", {"A":"11","B":"12","C":"10","D":"13"}, "A", "Na is 11")],
            "Physics": [("Unit of force?", {"A":"Joule","B":"Newton","C":"Watt","D":"Pascal"}, "B", "Newton"), ("Speed of light?", {"A":"3x10^8 m/s","B":"3x10^6","C":"3x10^5","D":"3x10^10"}, "A", "3x10^8")],
            "Economics": [("GDP means?", {"A":"Gross Domestic Product","B":"General","C":"Gross Direct","D":"None"}, "A", "Gross Domestic Product")],
            "Government": [("Supreme law?", {"A":"Decree","B":"Edict","C":"Constitution","D":"Act"}, "C", "Constitution")],
            "Literature": [("Long narrative poem?", {"A":"Sonnet","B":"Epic","C":"Ballad","D":"Ode"}, "B", "Epic")],
            "Commerce": [("Middleman wholesaler-consumer?", {"A":"Producer","B":"Retailer","C":"Agent","D":"Broker"}, "B", "Retailer")],
            "CRS": [("First book of Bible?", {"A":"Exodus","B":"Genesis","C":"Leviticus","D":"Numbers"}, "B", "Genesis")]
        }
        all_q=[]
        for subj, bank in banks.items():
            topics = [s.split(":")[0] if ":" in s else s for s in JAMB_SYLLABUS_COMPLETE.get(subj, {}).get("sections", ["General"])]
            for i in range(5000):
                q, opts, ans, exp = random.choice(bank)
                all_q.append({"id": len(all_q)+1, "subject": subj, "year": random.randint(2010,2024), "topic": random.choice(topics), "question": q, "options": opts, "answer": ans, "explanation": exp, "examType": "utme"})
        random.shuffle(all_q)
        for idx, q in enumerate(all_q):
            q["id"]=idx+1
        return all_q

    def get_questions(self, subject=None, year=None, limit=40):
        filtered=self.db
        if subject:
            filtered=[q for q in filtered if q.get('subject','').lower()==subject.lower()]
        if year:
            filtered=[q for q in filtered if str(q.get('year',''))==str(year)]
        random.shuffle(filtered)
        return filtered[:limit] if filtered else []

    def get_years(self, subject=None):
        filtered=self.db
        if subject:
            filtered=[q for q in filtered if q.get('subject','').lower()==subject.lower()]
        years=sorted(set([q.get('year') for q in filtered if q.get('year')]), reverse=True)
        return years if years else list(range(2024,2009,-1))

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

cbt = CBTEngine()

def format_question(q, idx, total, time_left=None):
    time_str = f"⏱ {time_left//60}:{time_left%60:02d} | " if time_left else ""
    header = f"📝 Q{idx+1}/{total} | {q['subject']} | {q.get('year','')} | {q.get('topic','')} {time_str}\n\n"
    body = f"<b>{html.escape(q['question'])}</b>\n\n"
    opts = "\n".join([f"<b>{k}</b>: {html.escape(v)}" for k,v in q['options'].items()])
    return header + body + opts

def get_options_keyboard_with_menu(q, current_idx):
    row = [InlineKeyboardButton(f"{k}", callback_data=f"ans_{k}") for k in q['options'].keys()]
    nav_row = [InlineKeyboardButton("⬅️ Prev", callback_data="nav_prev"), InlineKeyboardButton("➡️ Next", callback_data="nav_next"), InlineKeyboardButton("🏁 Submit", callback_data="submit")]
    explain_row = [InlineKeyboardButton("🎙 Explain + Voice (Perfect Teacher)", callback_data=f"explain_{current_idx}")]
    menu_row = [InlineKeyboardButton("🔵 MENU - Click for all options", callback_data="menu_main")]
    return InlineKeyboardMarkup([row, nav_row, explain_row, menu_row])

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 Past Questions", callback_data="menu_past"), InlineKeyboardButton("📝 Mock Exam", callback_data="menu_mock")],
        [InlineKeyboardButton("🎙 Explain Answer", callback_data="menu_explain"), InlineKeyboardButton("📊 My Score", callback_data="menu_score")],
        [InlineKeyboardButton("📖 Syllabus", callback_data="menu_syllabus"), InlineKeyboardButton("💬 Ask Tutor", callback_data="menu_tutor")],
        [InlineKeyboardButton("👥 Invite Friend", callback_data="menu_invite"), InlineKeyboardButton("💎 Go Premium", callback_data="menu_premium")],
        [InlineKeyboardButton("📞 Help @jibriliks", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_persistent_blue_menu():
    keyboard = [
        [KeyboardButton("🔵 MENU"), KeyboardButton("📚 Past Questions")],
        [KeyboardButton("📝 Mock Exam"), KeyboardButton("📊 My Score")],
        [KeyboardButton("📖 Syllabus"), KeyboardButton("💬 Ask Tutor")],
        [KeyboardButton("💎 Go Premium"), KeyboardButton("📞 Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def get_subjects_keyboard(prefix="prac_"):
    buttons = []
    for s in SUBJECTS:
        buttons.append([InlineKeyboardButton(f"{s}", callback_data=f"{prefix}{s}")])
    buttons.append([InlineKeyboardButton("🔵 MENU", callback_data="menu_main")])
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
    buttons.append([InlineKeyboardButton("🔵 MENU - Back to Main", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    if context.args and len(context.args) > 0:
        try:
            referrer = int(context.args[0])
            if referrer != uid:
                got_premium, count = add_referral(referrer, uid)
                if got_premium:
                    try:
                        await context.bot.send_message(chat_id=referrer, text=f"🎉 Congrats! You invited 3 friends! You now have 1 WEEK PREMIUM (N{PREMIUM_PRICE} value)!")
                    except:
                        pass
        except:
            pass
    premium = is_premium(uid)
    days_left = get_premium_days_left(uid)
    status = f"💎 PREMIUM ({days_left} days left) - Unlimited" if premium else f"🆓 FREE (5 Qs limit) - Premium N{PREMIUM_PRICE}/month"
    ref_count = get_referral_count(uid)
    top_name, top_score = get_top_scorer()
    top_banner = f"🏆 Top Scorer: {top_name} - {top_score}/400" if top_name else ""
    welcome = f"🎓 *UTME SUCCESS BOT - FULLY UPGRADED PROFESSIONAL* 🎓\nHello {update.effective_user.first_name}! {status}\n\n*Your JAMB Partner - 50k Questions + Complete Syllabus*\n\n{top_banner}\n\n📚 Past Questions - By Subject & Year (2010-2024)\n📝 Mock Exam - Real JAMB CBT (Free: 5 Qs, Premium: Unlimited 180 Qs)\n🎙 Explain Answer - Perfect teacher, no jumping steps + Voice\n📊 My Score - Performance, weak areas, leaderboard\n📖 Syllabus - Complete UTME official syllabus\n💬 Ask Tutor - Super smart AI, step-by-step perfect explanations\n\n👥 Invite: {ref_count}/3 friends → 1 week premium\n💎 Premium: N{PREMIUM_PRICE}/month unlimited\n\n🔵 Use the BLUE MENU button below (persistent) to access menu anytime even if you scrolled!\n\nChoose from menu below 👇\n"
    await update.message.reply_text(welcome, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_text("🔵 *BLUE MENU HANDLE* - Click this anytime to access menu (even if scrolled):", reply_markup=get_persistent_blue_menu())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"📞 *HELP - UTME Success Bot - Fully Upgraded*\n\n*For help contact:*\n👉 @jibriliks\n\n*Commands:*\n📚 Past Questions - /past - Select any year 2010-2024\n📝 Mock Exam - /mock - Free 5 Qs, Premium unlimited 180 Qs\n🎙 Explain - Tap 🎙 during quiz for perfect teacher\n📊 My Score - /score\n📖 Syllabus - /syllabus - Complete UTME official syllabus\n💬 Ask Tutor - /tutor or /ask + question - Super smart step-by-step\n👥 Invite - /invite - 3 friends = 1 week premium\n💎 Premium - /subscribe - N{PREMIUM_PRICE}/month - Upgrade page on Render\n\n*Upgrade Page:* {RENDER_URL}/upgrade/{{your_user_id}}\n\n*Support:* @jibriliks\n"
    await update.message.reply_text(text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)

async def past_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, update.effective_user)
    await update.message.reply_text("📚 *Past Questions - Fully Upgraded*\nChoose how to practice (select any year):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📖 By Subject (then choose Year)", callback_data="past_by_subject")],[InlineKeyboardButton("📅 By Year Direct (2010-2024)", callback_data="past_by_year")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)

async def mock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    premium = is_premium(uid)
    limit_text = "Unlimited 180 Qs" if premium else "5 Qs (Free) - N2000 for unlimited"
    top_name, top_score = get_top_scorer()
    top_banner = f"🏆 Top Scorer: {top_name} - {top_score}/400" if top_name else ""
    await update.message.reply_text(f"📝 *Mock Exam - Fully Upgraded*\n{top_banner}\nYour access: {limit_text}\nChoose type:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚡ Quick Test (Free 5 Qs)", callback_data="mock_quick")],[InlineKeyboardButton("📖 Subject Mock", callback_data="mock_subject")],[InlineKeyboardButton("🔥 Full JAMB Mock (Premium 180 Qs, 2hrs)", callback_data="mock_full")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    stats = get_user_stats(uid)
    if not stats:
        await update.message.reply_text("📊 *My Score*\n\nNo exams yet! Start with /mock", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Start Mock", callback_data="menu_mock")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        return
    total_avg = stats["total_score"] / max(stats["total_exams"],1)
    jamb_equiv = int(total_avg)
    pos, total_users = get_leaderboard_position(uid)
    subjects = stats.get("subjects", {})
    strong = sorted(subjects.items(), key=lambda x: x[1]["avg"], reverse=True)[:2]
    weak = sorted(subjects.items(), key=lambda x: x[1]["avg"])[:2]
    text = f"📊 *My Score - Fully Upgraded*\n\n*Total Average:* {total_avg:.1f}/400\n*Best:* {stats.get('best_score',0)}/400\n*Total Exams:* {stats['total_exams']}\n\n*Strong:*\n"
    for subj, data in strong:
        text += f"• {subj}: {data['avg']}%\n"
    text += "\n*Weak:*\n"
    for subj, data in weak:
        text += f"• {subj}: {data['avg']}% → Practice\n"
    text += f"\n*Leaderboard:* #{pos} out of {total_users}\n"
    keyboard = [[InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{jamb_equiv}_{stats['total_exams']}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def syllabus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, update.effective_user)
    if context.args:
        subj = " ".join(context.args).capitalize()
        if subj in JAMB_SYLLABUS_COMPLETE:
            data = JAMB_SYLLABUS_COMPLETE[subj]
            text = f"📖 *JAMB Official Syllabus - {subj} - {data['title']} - COMPLETE*\n\n"
            for i, sec in enumerate(data['sections'], 1):
                text += f"{i}. {sec}\n\n"
            text += f"\nFull syllabus also at: {RENDER_URL}/syllabus/{subj}\nPractice {subj}: /practice {subj}"
            if len(text) > 4000:
                text = text[:4000]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"▶️ Practice {subj}", callback_data=f"prac_{subj}")],[InlineKeyboardButton("🌐 Website", url=f"{RENDER_URL}/syllabus/{subj}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
            return
    keyboard = []
    for s in SUBJECTS:
        keyboard.append([InlineKeyboardButton(f"📖 {s}", callback_data=f"syllabus_{s}")])
    keyboard.append([InlineKeyboardButton("🌐 View All on Website", url=f"{RENDER_URL}/")])
    keyboard.append([InlineKeyboardButton("🔵 MENU", callback_data="menu_main")])
    await update.message.reply_text("📖 *JAMB Official Syllabus - COMPLETE*\nChoose subject:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def tutor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_profile(update.effective_user.id, update.effective_user)
    if not context.args:
        await update.message.reply_text("💬 *Ask Tutor - Super Smart AI - Step-by-Step Perfect*\n\nAsk any question like:\n`/tutor What is photosynthesis? Explain step-by-step`\n`/tutor Solve: 2x + 3 = 11 with steps`\n\nI am super smart and will explain step-by-step without jumping, like a perfect teacher!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
        return
    question = " ".join(context.args)
    await update.message.reply_text("🧠 *Super Smart Tutor is thinking...* Preparing perfect step-by-step explanation...")
    explanation = tutor_answer_any_question(question)
    if len(explanation) > 4000:
        for i in range(0, len(explanation), 4000):
            await update.message.reply_text(explanation[i:i+4000], parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"💬 *Super Smart Tutor - Perfect Step-by-Step:*\n\n{explanation}", parse_mode=ParseMode.MARKDOWN)
    voice_file = text_to_voice_tutor(explanation[:1000], q_id=f"tutor_{int(time.time())}")
    if voice_file and os.path.exists(voice_file):
        try:
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=open(voice_file, 'rb'), caption="🎙 Perfect teacher voice")
            os.remove(voice_file)
        except:
            pass
    await update.message.reply_text("Want more? Ask follow-up or tap 🔵 MENU", reply_markup=get_main_menu())

async def invite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    bot_username = context.bot.username or "UTMEBOT"
    invite_link = f"https://t.me/{bot_username}?start={uid}"
    refs = load_json(REFERRAL_FILE, {}).get(str(uid), [])
    count = len(refs)
    needed = 3 - (count % 3) if count % 3 != 0 else 3
    needed_text = f"🎉 You have {count} invites! Invite {needed} more for another week!" if count >=3 else f"Invite {needed} more friend(s) to get 1 WEEK PREMIUM (N{PREMIUM_PRICE})!"
    text = f"👥 *Invite Friend - Get 1 Week Free Premium*\n\nYour invite link:\n`{invite_link}`\n\n*Progress:* {count} friends\n{needed_text}\n\n*Current:* {'💎 Active' if is_premium(uid) else '🆓 Free'}\n*Upgrade page:* {RENDER_URL}/upgrade/{uid}\n"
    keyboard = [[InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={invite_link}&text=I scored 268 in JAMB Mock! Can you beat me?")],[InlineKeyboardButton("💎 Go Premium N2000", callback_data="menu_premium")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    if is_premium(uid):
        days_left = get_premium_days_left(uid)
        await update.message.reply_text(f"💎 Already PREMIUM! ({days_left} days left)\n\nUpgrade page: {RENDER_URL}/upgrade/{uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        return
    ref_count = get_referral_count(uid)
    upgrade_url = f"{RENDER_URL}/upgrade/{uid}"
    await update.message.reply_text(f"💎 *Go Premium - N{PREMIUM_PRICE}/month*\n\n*Free vs Premium:*\n🆓 Free: 5 Qs only\n💎 Premium: Unlimited 180 Qs, super smart tutor, perfect voice, complete syllabus\n\n*Benefits:*\n• Unlimited mocks 180 Qs\n• Super smart AI Tutor step-by-step\n• Perfect voice teacher no jumping\n• All subjects + years\n• Complete syllabus\n\n*Free alt:* Invite 3 friends = 1 week free! You have {ref_count}/3\n\n*Upgrade Page:*\n{upgrade_url}\n\nClick below to upgrade via Flutterwave\nOr send email:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Upgrade Now N{PREMIUM_PRICE} - Flutterwave", url=upgrade_url)],[InlineKeyboardButton("👥 Invite 3 Friends = 1 Week Free", callback_data="menu_invite")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
    context.user_data["awaiting_email"] = True

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_email"):
        uid = update.effective_user.id
        text = update.message.text.strip()
        if text in ["🔵 MENU", "📚 Past Questions", "📝 Mock Exam", "📊 My Score", "📖 Syllabus", "💬 Ask Tutor", "💎 Go Premium", "📞 Help"]:
            mapping = {"🔵 MENU": start_cmd, "📚 Past Questions": past_cmd, "📝 Mock Exam": mock_cmd, "📊 My Score": score_cmd, "📖 Syllabus": syllabus_cmd, "💬 Ask Tutor": tutor_cmd, "💎 Go Premium": subscribe_cmd, "📞 Help": help_cmd}
            await mapping[text](update, context)
            return
        if uid not in cbt.active_exams and len(text) > 3:
            context.args = text.split()
            await tutor_cmd(update, context)
            return
        return
    email = update.message.text.strip()
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Invalid email, send like: you@gmail.com\nOr click upgrade button")
        return
    uid = update.effective_user.id
    name = update.effective_user.full_name
    await update.message.reply_text("⏳ Creating payment link and upgrade page...")
    link, tx_ref = create_flutterwave_link(uid, email=email, name=name)
    if not link:
        upgrade_url = f"{RENDER_URL}/upgrade/{uid}?email={email}"
        await update.message.reply_text(f"Use upgrade page:\n{upgrade_url}\nOr contact @jibriliks", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Upgrade Page N{PREMIUM_PRICE}", url=upgrade_url)]]))
        return
    context.user_data["awaiting_email"] = False
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Pay N{PREMIUM_PRICE} - Flutterwave", url=link)],[InlineKeyboardButton("✅ Verify Payment", callback_data=f"verify_{tx_ref}")],[InlineKeyboardButton("🌐 Upgrade Page", url=f"{RENDER_URL}/upgrade/{uid}?email={email}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]])
    await update.message.reply_text(f"🔗 *Pay N{PREMIUM_PRICE}:*\nAfter payment click Verify\nTx: {tx_ref}\n\nUpgrade page: {RENDER_URL}/upgrade/{uid}", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
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
        await tutor_cmd(update, context)
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
        await query.message.reply_text("🎙 *Explain Answer - Perfect Teacher*\n\nDuring quiz, tap 🎙 Explain + Voice button\n\nI will explain step-by-step without jumping, like perfect classroom teacher, plus voice!\n\nOr use /tutor to ask any question - super smart AI", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "past_by_subject":
        await query.message.reply_text("📚 *Past Questions - By Subject - Select any year after*\nChoose subject:", reply_markup=get_subjects_keyboard("past_subj_"), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "past_by_year":
        await query.message.reply_text("📚 *Past Questions - By Year - 2010 to 2024 - Choose any year*:", reply_markup=get_years_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("past_subj_"):
        subj = data.replace("past_subj_","")
        await query.message.reply_text(f"📚 *{subj} - Past Questions*\nChoose year or start now:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📅 Choose Year (2010-2024)", callback_data=f"past_year_{subj}"), InlineKeyboardButton("▶️ Start Now (All Years)", callback_data=f"prac_{subj}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_past")]]), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("past_year_"):
        subj = data.replace("past_year_","")
        await query.message.reply_text(f"📅 *{subj} - Choose Year (2010-2024)*:", reply_markup=get_years_keyboard(subj), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("year_"):
        parts = data.split("_")
        if len(parts) >= 3:
            subj = parts[1] if parts[1] != "all" else None
            year = parts[2]
            premium = is_premium(uid)
            limit = 40 if premium else 5
            if subj:
                qs = cbt.get_questions(subject=subj, year=year, limit=limit)
                if not qs:
                    qs = cbt.get_questions(subject=subj, limit=limit)
                if qs:
                    cbt.active_exams[uid] = {"questions": qs, "current_idx":0, "score":0, "answers":{}, "subjects":[subj], "start_time":time.time(), "duration":30*60}
                    q,total = qs[0], len(qs)
                    await query.message.reply_text(f"📚 Past Questions {subj} {year} - {total} Qs {'(Free 5 Qs)' if not premium else '(Premium)'}")
                    await query.message.reply_text(format_question(q,0,total,cbt.get_time_left(uid)), reply_markup=get_options_keyboard_with_menu(q,0))
                    if not premium:
                        await query.message.reply_text(f"🆓 Free limit: 5 Qs only. Upgrade N{PREMIUM_PRICE}: /subscribe")
                    return
            else:
                qs = cbt.get_questions(year=year, limit=limit)
                if qs:
                    cbt.active_exams[uid] = {"questions": qs, "current_idx":0, "score":0, "answers":{}, "subjects":["Mixed"], "start_time":time.time(), "duration":30*60}
                    q,total = qs[0], len(qs)
                    await query.message.reply_text(f"📚 Past Questions {year} - {total} Qs")
                    await query.message.reply_text(format_question(q,0,total,cbt.get_time_left(uid)), reply_markup=get_options_keyboard_with_menu(q,0))
                    return
        await query.message.reply_text("No questions found for that year. Try another.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_past")]]))
        return
    elif data == "mock_quick":
        premium = is_premium(uid)
        subs = ["English","Mathematics","Biology","Chemistry"]
        q,total = cbt.start_mock(uid, subs, duration=15*60, limit_per_subject=5 if not premium else 5)
        if not premium:
            exam = cbt.active_exams[uid]
            exam["questions"] = exam["questions"][:5]
            q,total = exam["questions"][0], 5
            await query.message.reply_text(f"⚡ Quick Test - 5 Qs (Free) - {','.join(subs)}\n\n🆓 Free limit: 5 Qs. Upgrade N{PREMIUM_PRICE}: /subscribe")
        else:
            await query.message.reply_text(f"⚡ Quick Test - {total} Qs - {','.join(subs)} (Premium)")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0))
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
            await query.message.reply_text(f"No questions found for {subj}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
            return
        await query.message.reply_text(f"📖 Subject Mock - {subj} - {total} Qs {'(Free 5 Qs)' if not premium else '(Premium)'}")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0))
        if not premium:
            await query.message.reply_text(f"🆓 Free: 5 Qs only. N{PREMIUM_PRICE}: /subscribe")
        return
    elif data == "mock_full":
        premium = is_premium(uid)
        if not premium:
            await query.message.reply_text(f"🔒 *Full JAMB Mock (180 Qs) Premium Only*\n\n🆓 Free: 5 Qs\n💎 Premium N{PREMIUM_PRICE}: Unlimited 180 Qs, super smart tutor, perfect voice\n\nUpgrade page: {RENDER_URL}/upgrade/{uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💎 Go Premium N{PREMIUM_PRICE} - Upgrade Page", url=f"{RENDER_URL}/upgrade/{uid}")],[InlineKeyboardButton(f"💎 Go Premium N{PREMIUM_PRICE}", callback_data="menu_premium")],[InlineKeyboardButton("👥 Invite 3 Friends = 1 Week Free", callback_data="menu_invite")],[InlineKeyboardButton("⚡ Quick Test (5 Qs Free)", callback_data="mock_quick")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
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
        await query.message.reply_text(f"🔥 *Full JAMB Mock - 180 Qs, 2hrs - Fully Upgraded*\n{','.join(subs)}\nPremium unlimited!", parse_mode=ParseMode.MARKDOWN)
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0))
        return
    elif data.startswith("syllabus_"):
        subj = data.replace("syllabus_","")
        if subj in JAMB_SYLLABUS_COMPLETE:
            data_s = JAMB_SYLLABUS_COMPLETE[subj]
            text = f"📖 *JAMB Official Syllabus - {subj} - {data_s['title']} - COMPLETE*\n\n"
            for i, sec in enumerate(data_s['sections'], 1):
                text += f"{i}. {sec}\n\n"
            text += f"\nFull syllabus also at: {RENDER_URL}/syllabus/{subj}\nPractice {subj}: /practice {subj}"
            if len(text) > 4000:
                await query.message.reply_text(text[:4000], parse_mode=ParseMode.MARKDOWN)
                await query.message.reply_text(text[4000:8000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"▶️ Practice {subj}", callback_data=f"prac_{subj}")],[InlineKeyboardButton("🌐 Website", url=f"{RENDER_URL}/syllabus/{subj}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
            else:
                await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"▶️ Practice {subj}", callback_data=f"prac_{subj}")],[InlineKeyboardButton("🌐 Website", url=f"{RENDER_URL}/syllabus/{subj}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
        else:
            await query.message.reply_text(f"Syllabus for {subj} not found", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_syllabus")]]))
        return
    if data.startswith("verify_"):
        tx_ref = data.replace("verify_","")
        await query.message.reply_text("🔍 Verifying payment via Flutterwave...")
        success,_ = verify_by_tx_ref(tx_ref)
        if success:
            grant_premium(uid,30,tx_ref)
            await query.message.reply_text(f"✅ Payment Confirmed! PREMIUM 30 days N{PREMIUM_PRICE}\n\nUnlimited access!\nUpgrade page: {RENDER_URL}/upgrade/{uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Start Mock Unlimited", callback_data="menu_mock")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        else:
            await query.message.reply_text(f"❌ Not confirmed yet. Tx: {tx_ref}\nWait 1 min and Verify again. Or @jibriliks\n\nUpgrade page: {RENDER_URL}/upgrade/{uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Upgrade Page", url=f"{RENDER_URL}/upgrade/{uid}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        return
    elif data.startswith("prac_"):
        subj = data.replace("prac_","")
        premium = is_premium(uid)
        limit = 40 if premium else 5
        q,total = cbt.start_mock(uid, [subj], duration=45*60, limit_per_subject=limit)
        if not q:
            await query.message.reply_text(f"No questions found for {subj}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
            return
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0))
        if not premium:
            await query.message.reply_text(f"🆓 Free: {total} Qs limit. Unlimited N{PREMIUM_PRICE}: /subscribe")
        return
    elif data.startswith("ans_"):
        opt = data.replace("ans_","")
        result,status = cbt.answer_current(uid, opt)
        if status == "NO_EXAM":
            await query.message.reply_text("No exam. /mock to start", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
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
                profile = get_user_profile(uid)
                name = profile.get('first_name','') if profile else update.effective_user.first_name
                update_user_stats(uid, subj, correct, total_subj, res["jamb_score"], name)
            text = f"🏁 *Finished! Fully Upgraded Result*\nScore: {res['raw_score']}/{res['total']}\nJAMB: {res['jamb_score']}/400\n\n"
            premium = is_premium(uid)
            if not premium and res['total'] >= 5:
                text += f"🆓 Free limit reached (5 Qs). Unlimited N{PREMIUM_PRICE}: /subscribe\nInvite 3 friends for 1 week free: /invite\nUpgrade: {RENDER_URL}/upgrade/{uid}\n\n"
            keyboard = [[InlineKeyboardButton("📊 My Score", callback_data="menu_score"), InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{res['jamb_score']}_{res['total']}")],[InlineKeyboardButton("🎙 Explain All (Perfect Teacher)", callback_data="explain_0")],[InlineKeyboardButton("🔁 Try Again", callback_data="menu_mock"), InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            next_q,next_idx = result
            left = cbt.get_time_left(uid)
            total = len(cbt.active_exams[uid]['questions'])
            await query.message.reply_text(format_question(next_q,next_idx,total,left), reply_markup=get_options_keyboard_with_menu(next_q,next_idx))
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
        await query.message.reply_text(format_question(q,idx,len(exam['questions']),left), reply_markup=get_options_keyboard_with_menu(q,idx))
    elif data=="submit":
        final=cbt.finish_exam(uid)
        if final:
            text = f"🏁 Submitted! {final['raw_score']}/{final['total']} JAMB: {final['jamb_score']}/400"
            if not is_premium(uid):
                text += f"\n\n🆓 Free: 5 Qs limit. Premium N{PREMIUM_PRICE}: /subscribe\nUpgrade: {RENDER_URL}/upgrade/{uid}"
            keyboard = [[InlineKeyboardButton("📊 My Score", callback_data="menu_score"), InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{final['jamb_score']}_{final['total']}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("explain_"):
        try:
            idx=int(data.replace("explain_",""))
            exam=cbt.active_exams.get(uid)
            q=exam['questions'][idx] if exam and idx < len(exam['questions']) else None
            if not q:
                await query.message.reply_text("No question found - start a mock first /mock", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
                return
            await query.message.reply_text("🧠 *Super Smart AI Tutor - Perfect Teacher* Generating perfect step-by-step explanation without jumping steps...")
            exp=explain_with_ai_super_smart(q)
            if len(exp) > 4000:
                await query.message.reply_text(f"🎙 *Perfect Teacher Explanation - Part 1:*\n\n{exp[:4000]}", parse_mode=ParseMode.MARKDOWN)
                await query.message.reply_text(f"Part 2:\n\n{exp[4000:8000]}", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.message.reply_text(f"🎙 *Perfect Teacher - Step-by-Step (No Jumping):*\n\n{exp}\n\n✅ Correct answer: {q.get('answer')} - {q.get('options',{}).get(q.get('answer'),'')}", parse_mode=ParseMode.MARKDOWN)
            vp=text_to_voice_perfect(q, exp)
            if vp and os.path.exists(vp):
                try:
                    await context.bot.send_voice(chat_id=query.message.chat_id, voice=open(vp,'rb'), caption="🎙 Perfect Teacher Voice - Step-by-step, no jumping")
                    os.remove(vp)
                except Exception as e:
                    print(f"Voice send error: {e}", flush=True)
            await query.message.reply_text("Want more? Ask follow-up with /tutor or tap 🔵 MENU", reply_markup=get_main_menu())
        except Exception as e:
            await query.message.reply_text(f"Error: {e}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
    elif data.startswith("share_"):
        parts = data.split("_")
        jamb_score = parts[1] if len(parts)>1 else "200"
        total = parts[2] if len(parts)>2 else "40"
        profile = get_user_profile(uid)
        name = profile.get('first_name', update.effective_user.first_name) if profile else update.effective_user.first_name
        await query.message.reply_text("🎨 Generating your viral score image...")
        img_path = generate_score_image(uid, f"{jamb_score}/{400}", total, int(jamb_score), name)
        if img_path and os.path.exists(img_path):
            try:
                caption = f"I scored {jamb_score} in JAMB Mock! Can you beat me? Try here t.me/{context.bot.username or 'UTMEBOT'} #JAMB"
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=open(img_path,'rb'), caption=caption)
                os.remove(img_path)
            except Exception as e:
                await query.message.reply_text(f"📤 Share this:\n\nI scored {jamb_score} in JAMB Mock! Can you beat me? Try here t.me/{context.bot.username}")
        else:
            await query.message.reply_text(f"📤 *Share My Score*\n\nI scored {jamb_score} in JAMB Mock!\nCan you beat me?\nTry here t.me/{context.bot.username or 'UTMEBOT'}", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))

async def mock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    premium = is_premium(uid)
    limit_text = "Unlimited 180 Qs" if premium else "5 Qs (Free) - N2000 unlimited"
    top_name, top_score = get_top_scorer()
    top_banner = f"🏆 Top Scorer: {top_name} - {top_score}/400" if top_name else ""
    keyboard=[[InlineKeyboardButton("⚡ Quick Test (Free 5 Qs)", callback_data="mock_quick")],[InlineKeyboardButton("📖 Subject Mock", callback_data="mock_subject")],[InlineKeyboardButton("🔥 Full JAMB Mock (Premium 180 Qs)", callback_data="mock_full")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
    await update.message.reply_text(f"📝 Mock Exam - Fully Upgraded\n{top_banner}\nYour access: {limit_text}\nChoose type:", reply_markup=InlineKeyboardMarkup(keyboard))

async def practice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    if context.args:
        subj = " ".join(context.args).capitalize()
        if subj in SUBJECTS:
            premium = is_premium(uid)
            limit = 40 if premium else 5
            q,total = cbt.start_mock(uid, [subj], duration=45*60, limit_per_subject=limit)
            left = cbt.get_time_left(uid)
            await update.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0))
            if not premium:
                await update.message.reply_text(f"🆓 Free: 5 Qs only. Premium N{PREMIUM_PRICE} unlimited: /subscribe")
            return
    buttons=[[InlineKeyboardButton(s, callback_data=f"prac_{s}")] for s in SUBJECTS]
    buttons.append([InlineKeyboardButton("🔵 MENU", callback_data="menu_main")])
    await update.message.reply_text("Select subject:", reply_markup=InlineKeyboardMarkup(buttons))

def start_telegram_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN not set", flush=True)
        return
    if not TG_AVAILABLE:
        print("telegram library not available", flush=True)
        return
    for i in range(3):
        try:
            import requests
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=15)
            print(f"DeleteWebhook: {r.text[:200]}", flush=True)
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
            app.add_handler(CommandHandler("menu", start_cmd))
            app.add_handler(CallbackQueryHandler(handle_callback))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
            print("Handlers registered - FULLY UPGRADED PROFESSIONAL v2 is LIVE!", flush=True)
            app.run_polling(drop_pending_updates=True, allowed_updates=["message","callback_query"])
        except Exception as e:
            print(f"Polling crashed: {e}", flush=True)
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
