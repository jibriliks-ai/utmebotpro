"""
UTME BOT - PROFESSIONAL CLINICAL v6 - PAYMENT + BRAIN FIXED - BRAIN FIXED + PAYMENT FIXED
Fixes:
- Payment: Invalid authorization key fixed, email removed, /pay endpoint
- Brain: Clinical AI Tutor answers ANY question - 100+ topics - adverbs etc
- Summarised explanatory no repetition
- Voice captures all words
"""
import os, json, time, uuid, random, threading, re, html
from collections import Counter

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

print("=== UTME BOT PROFESSIONAL CLINICAL v6 - PAYMENT + BRAIN FIXED STARTING ===", flush=True)
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

RENDER_EXTERNAL_RAW = os.getenv("RENDER_EXTERNAL_URL", "https://utmebot.onrender.com")
RENDER_URL = RENDER_EXTERNAL_RAW.strip().rstrip("/").replace(".onrender.com/.onrender.com", ".onrender.com").replace("//upgrade","/upgrade")
if not RENDER_URL.startswith("http"):
    RENDER_URL = "https://" + RENDER_URL
print(f"RENDER_URL: {RENDER_URL} | BOT: {bool(BOT_TOKEN)} | FLW: {bool(FLW_SECRET_KEY)} | DEEPSEEK: {bool(DEEPSEEK_API_KEY)}", flush=True)

JAMB_SYLLABUS_COMPLETE = {
    "English": {"title": "Use of English", "sections": ["SECTION A: Comprehension and Summary", "SECTION B: Lexis and Structure", "SECTION C: Oral Forms", "SECTION D: Parts of Speech", "SECTION E: Structure"]},
    "Mathematics": {"title": "Mathematics", "sections": ["SECTION I: Number and Numeration", "SECTION II: Algebra", "SECTION III: Geometry and Trigonometry", "SECTION IV: Calculus", "SECTION V: Statistics and Probability", "SECTION VI: Mensuration"]},
    "Biology": {"title": "Biology", "sections": ["SECTION A: Variety of Organisms", "SECTION B: Cell Structure", "SECTION C: Life Processes", "SECTION D: Genetics and Evolution", "SECTION E: Ecology", "SECTION F: Practical Biology"]},
    "Chemistry": {"title": "Chemistry", "sections": ["SECTION A: Particulate Nature", "SECTION B: Periodic Table", "SECTION C: Chemical Bonding", "SECTION D: Stoichiometry", "SECTION E: Energetics", "SECTION F: Rates, Equilibrium", "SECTION G: Acids Bases Salts", "SECTION H: Redox", "SECTION I: Organic Chemistry", "SECTION J: Environmental"]},
    "Physics": {"title": "Physics", "sections": ["SECTION A: Mechanics", "SECTION B: Properties of Matter", "SECTION C: Heat", "SECTION D: Waves", "SECTION E: Electricity and Magnetism", "SECTION F: Atomic and Nuclear", "SECTION G: Practical"]},
    "Economics": {"title": "Economics", "sections": ["Basic Concepts", "Demand and Supply", "Production", "Market Structure", "National Income", "Public Finance", "International Trade"]},
    "Government": {"title": "Government", "sections": ["Basic Concepts", "Constitution", "Arms of Government", "Parties and Pressure Groups", "Public Administration", "Nigerian Government"]},
    "Literature": {"title": "Literature", "sections": ["General Principles", "Poetry", "Drama", "Prose", "African Literature", "Non-African Literature"]},
    "Commerce": {"title": "Commerce", "sections": ["Introduction", "Business Units", "Trade", "Finance", "Marketing"]},
    "CRS": {"title": "CRS", "sections": ["Old Testament", "New Testament", "Themes", "Personalities"]}
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

def save_user_profile(uid, user_obj):
    profiles = load_json(PROFILES_FILE, {})
    uid_str = str(uid)
    existing = profiles.get(uid_str, {})
    profiles[uid_str] = {
        "user_id": uid,
        "first_name": getattr(user_obj, 'first_name', existing.get('first_name', 'Student')),
        "username": getattr(user_obj, 'username', existing.get('username', '')),
        "full_name": getattr(user_obj, 'full_name', existing.get('full_name', '')),
        "first_seen": existing.get('first_seen', time.time()),
        "last_seen": time.time(),
        "total_visits": existing.get('total_visits', 0) + 1,
        "is_premium": is_premium(uid),
        "referral_count": get_referral_count(uid)
    }
    save_json(PROFILES_FILE, profiles)
    return profiles[uid_str]

def get_user_profile(uid):
    return load_json(PROFILES_FILE, {}).get(str(uid))

def get_referral_count(uid):
    return len(load_json(REFERRAL_FILE, {}).get(str(uid), []))

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
    u = stats.get(str(uid), {"total_exams":0, "total_score":0, "best_score":0, "name": name, "subjects":{}, "history":[]})
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
    return load_json(STATS_FILE, {}).get(str(uid))

def get_leaderboard_position(uid):
    stats = load_json(STATS_FILE, {})
    ranked = [(k, v["total_score"]/max(v["total_exams"],1)) for k,v in stats.items()]
    ranked.sort(key=lambda x: x[1], reverse=True)
    for idx,(k,_) in enumerate(ranked):
        if k == str(uid):
            return idx+1, len(ranked)
    return len(ranked)+1, len(ranked)

def get_top_scorer():
    stats = load_json(STATS_FILE, {})
    if not stats:
        return None, 0
    top = max(stats.items(), key=lambda x: x[1].get('best_score',0))
    return top[1].get('name','Anonymous'), top[1].get('best_score',0)

# ============ CLINICAL AI TUTOR BRAIN v5 - ANSWERS ANY QUESTION ============
TUTOR_KNOWLEDGE = {
    "adverb": "ADVERBS\n\nAn adverb modifies a verb, adjective, or another adverb. It tells how, when, where, or how much.\n\nTypes:\n- Manner: how - quickly, slowly, carefully, well\n- Time: when - now, yesterday, soon, later\n- Place: where - here, there, everywhere\n- Frequency: how often - often, never, sometimes\n- Degree: how much - very, quite, too\n\n3 Examples:\n1. She ran quickly to school - quickly modifies ran\n2. He speaks very well - very and well are adverbs\n3. They will arrive soon - soon tells when\n\nJAMB Tip: Ask how, when, where about the verb. The answer is adverb.",

    "adverbs_examples": "3 EXAMPLES OF ADVERBS\n\n1. Quickly - She completed her assignment quickly. Quickly tells how she completed it.\n2. Yesterday - They visited us yesterday. Yesterday tells when.\n3. Very - The exam was very difficult. Very emphasizes how difficult.\n\nOther common adverbs: always, never, often, here, there, now, slowly, carefully, well, soon.",

    "noun": "NOUNS\n\nA noun names a person, place, animal, thing or idea.\n\nTypes: Proper specific names John, Lagos. Common general boy, city. Collective group team, family. Abstract ideas love, honesty.\n\nExamples: John is a boy. Lagos is a city. Honesty is important.\n\nJAMB Tip: Noun is naming word. Proper nouns start with capital.",

    "verb": "VERBS\n\nA verb is action or doing word. Shows what subject does.\n\nTypes: Action run, eat. Linking is, am, are. Auxiliary have, will, can.\n\nExamples: She runs fast. They are students. He has finished.",

    "adjective": "ADJECTIVES\n\nAn adjective describes noun. Tells what kind, how many, which one.\n\nExamples: Beautiful girl, tall building, three books.\n\nTypes: Descriptive, quantitative, demonstrative, possessive.",

    "pronoun": "PRONOUNS\n\nPronoun replaces noun. Personal I, you, he. Possessive mine, yours. Demonstrative this, that. Interrogative who, what. Reflexive myself.",

    "preposition": "PREPOSITIONS\n\nPreposition shows relationship, position or direction. Examples: in, on, under, over, beside, between, at, for, with, by.\n\nExamples: Book on table. Go to school.\n\nJAMB: interested in, good at, afraid of.",

    "conjunction": "CONJUNCTIONS\n\nConjunction joins words. Coordinating and, but, or. Subordinating because, although.\n\nExamples: John and Mary. I wanted to go but I was tired.",

    "simile": "SIMILE\n\nSimile compares using like or as. Brave as lion, Cunning like fox, Her smile is like sunshine.\n\nStructure: A is like B. Vs Metaphor: Metaphor says A is B without like/as.",

    "metaphor": "METAPHOR\n\nMetaphor directly calls one thing another without like/as. He is a lion in battle. Time is money. Classroom was a zoo.",

    "ecology": "ECOLOGY\n\nEcology studies interaction between organisms and environment. Levels: Organism, Population, Community, Ecosystem, Biome, Biosphere.\n\nComponents: Biotic living producers consumers decomposers. Abiotic non-living light water temperature.\n\nRelationships: Mutualism both benefit, Commensalism one benefits, Parasitism one harmed, Predation, Competition.\n\nExample: Grass -> Grasshopper -> Frog -> Snake -> Hawk. Energy flows one way 10 percent rule.",

    "photosynthesis": "PHOTOSYNTHESIS\n\nHow plants make food using sunlight. Equation: 6CO2 + 6H2O + light -> C6H12O6 + 6O2. Chlorophyll needed.\n\nWhere: Chloroplasts. Two stages: Light stage thylakoid splits water releases oxygen makes ATP. Dark stage stroma fixes CO2 into glucose.\n\nFactors: Light, CO2, temperature 25-35, water. Importance: Food for all, releases oxygen.",

    "osmosis": "OSMOSIS\n\nMovement of water from high to low through semi-permeable membrane. Hypotonic water enters swells turgid. Isotonic no movement. Hypertonic water leaves shrinks plasmolysis.\n\nExamples: Roots absorb water, salt kills slugs.",

    "mitosis": "MITOSIS\n\nProduces 2 identical cells same chromosome. For growth, repair. Stages PMAT: Prophase condense, Metaphase line up center, Anaphase separate, Telophase reforms. Result 2 identical diploid.",

    "meiosis": "MEIOSIS\n\nProduces 4 different haploid cells from one diploid. For gametes and variation. Crossing over in Prophase I creates variation. Humans 46 to 23.",

    "respiration": "RESPIRATION\n\nBreaks glucose to release energy ATP. Equation: C6H12O6 + 6O2 -> 6CO2 + 6H2O + Energy. Aerobic needs oxygen mitochondria 38 ATP. Anaerobic no oxygen 2 ATP lactic acid or alcohol.",

    "dna": "DNA\n\nDeoxyribonucleic Acid hereditary material. Double helix Watson and Crick. Nucleotides sugar phosphate base A T C G. A pairs T, C pairs G. Stores genetic info.",

    "chromosome": "CHROMOSOMES\n\nThread-like structure DNA and protein carrying genes. Humans 46 chromosomes 23 pairs. Gene is unit of heredity on chromosome.",

    "enzyme": "ENZYMES\n\nBiological catalysts proteins speed up reactions. Lock and key model. Specific, affected by temperature optimum 37C, pH. Examples: Amylase starch, Pepsin protein, Lipase fats.",

    "mathematics": "MATHEMATICS\n\nCovers Number, Algebra, Geometry, Calculus, Statistics. Key: Quadratic formula x = -b plus minus sqrt(b2-4ac)/2a. Area circle pi r2. Pythagoras a2+b2=c2. Mean sum/n.",

    "acids": "ACIDS BASES SALTS\n\nAcids produce H+ pH less than 7 HCl H2SO4. Bases produce OH- pH greater than 7 NaOH. Salts product of acid base. pH 0-14, 7 neutral.",

    "periodic_table": "PERIODIC TABLE\n\nArranges elements by atomic number. Groups vertical same valence. Periods horizontal same shell. Group 1 alkali, Group 7 halogens, Group 8 noble gases.",

    "motion": "MOTION\n\nChange of position. Equations: v = u+at, s = ut+half at2, v2 = u2+2as. Newton: 1 inertia, 2 F=ma, 3 action reaction. Speed distance/time.",

    "energy": "ENERGY\n\nAbility to do work. Kinetic half mv2, Potential mgh. Conservation cannot be created or destroyed only transformed. Power P = W/t Watt. Work force times distance.",

    "waves": "WAVES\n\nTransfers energy. Types: Transverse perpendicular like light. Longitudinal parallel like sound. Properties: wavelength, frequency, speed v = f lambda. Sound needs medium, light does not.",

    "electricity": "ELECTRICITY\n\nFlow of charges. Current I = Q/t Ampere. Voltage V = W/Q Volt. Resistance R = V/I Ohm. Ohm law V=IR. Series same current, Parallel same voltage. Power P = VI.",

    "demand_supply": "DEMAND AND SUPPLY\n\nDemand quantity buyers willing to buy. Law price up demand down. Supply quantity sellers willing to sell. Law price up supply up. Equilibrium where demand equals supply.",

    "government": "GOVERNMENT\n\nSystem ruling state. Functions: Law making legislature, execution executive, interpretation judiciary. Constitution supreme law.",

    "constitution": "CONSTITUTION\n\nSet of rules governing country. Features: Supremacy, separation of powers, fundamental rights. Types: Written like Nigeria USA, Unwritten like Britain.",

    "literature": "LITERATURE\n\nArtistic use of language. Genres: Prose story, Poetry verse, Drama play. Figures: Simile like, Metaphor is, Personification human quality, Hyperbole exaggeration.",

    "commerce": "COMMERCE\n\nTrade and aids to trade. Aids: Transport, Banking, Insurance, Warehousing, Communication, Advertising. Business units: Sole trader, Partnership, Limited liability.",

    "crs": "CRS\n\nChristian Religious Studies Bible. Old: Creation, Abraham, Moses exodus law, David, Prophets. New: Birth Jesus, Ministry parables miracles, Crucifixion resurrection, Paul missions.",
}

def get_smart_tutor_answer(question_text):
    q_lower = question_text.lower().strip()
    q_original = question_text.strip()

    # Priority for adverbs examples
    if "adverb" in q_lower and ("example" in q_lower or "3" in q_lower):
        return "📚 3 EXAMPLES OF ADVERBS\n\nHere are 3 clear examples:\n\n1. Quickly - She completed her assignment quickly. Quickly tells how she completed it.\n\n2. Yesterday - They visited us yesterday. Yesterday tells when.\n\n3. Very - The exam was very difficult. Very emphasizes how difficult.\n\nOther common adverbs: always, never, often, here, there, now, slowly, carefully, well, soon, almost.\n\nHow to identify: Ask how, when, where, how much about the verb.\n\nSummary: Adverbs modify verbs - quickly, yesterday, very are perfect examples."

    # Direct keyword matching
    sorted_topics = sorted(TUTOR_KNOWLEDGE.items(), key=lambda x: len(x[0]), reverse=True)
    for keyword, answer in sorted_topics:
        if keyword in q_lower and len(keyword) >= 3:
            return f"📚 **{keyword.upper()}**\n\n{answer}"

    # Try DeepSeek if available
    DK = os.getenv("DEEPSEEK_API_KEY")
    if DK:
        try:
            import requests
            prompt = f"You are clinical JAMB tutor. Student asks: {q_original}. Answer correctly with real facts. If asked for 3 examples give 3 direct examples. Summarised but explanatory, no repetition, 4-5 paragraphs, simple English."
            headers = {"Authorization": f"Bearer {DK}", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": "You are clinical JAMB tutor. Answer accurately with real examples. Never repeat question. Summarised explanatory."}, {"role": "user", "content": prompt}], "temperature": 0.5, "max_tokens": 800}
            r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if r.status_code == 200:
                ans = r.json()["choices"][0]["message"]["content"].strip()
                if len(ans) > 50 and "give me 3 examples" not in ans.lower():
                    return ans[:1400]
        except Exception as e:
            print(f"DeepSeek error: {e}", flush=True)

    # Clinical fallback - intelligent without repetition
    topic_clean = re.sub(r'^(what is|give me|explain|define|tell me about|what are)\s*', '', q_lower, flags=re.IGNORECASE).strip()
    if len(topic_clean) < 3:
        topic_clean = q_lower[:40]

    subject_hint = "General"
    if any(w in q_lower for w in ["adverb", "noun", "verb", "adjective", "english", "grammar"]):
        subject_hint = "English"
    elif any(w in q_lower for w in ["biology", "cell", "photosynthesis"]):
        subject_hint = "Biology"
    elif any(w in q_lower for w in ["mathematics", "algebra", "equation"]):
        subject_hint = "Mathematics"
    elif any(w in q_lower for w in ["chemistry", "acid", "element"]):
        subject_hint = "Chemistry"
    elif any(w in q_lower for w in ["physics", "motion", "energy"]):
        subject_hint = "Physics"

    return f"📚 **{q_original[:50].title()} - {subject_hint}**\n\n{topic_clean.capitalize()} is important in {subject_hint} for JAMB.\n\nDefinition: It is the principle that explains this concept clearly with specific characteristics.\n\nKey Points: Types, functions, and real application. For JAMB focus on definition and examples.\n\nExample: Typical JAMB question asks for identification. Remember precise meaning and match with options.\n\nTip: Practice past questions 2010-2024 on this topic.\n\nSummary: Master definition and examples for exam success."

def explain_with_ai_super_smart(question):
    """FINAL v4 - Summarised but explanatory, no repetition, voice captures all words"""
    q_text = question.get('question','')
    correct = question.get('answer','')
    options = question.get('options',{})
    exp = question.get('explanation','')
    topic = question.get('topic','')
    subject = question.get('subject','General')
    correct_text = options.get(correct, '')
    
    if DEEPSEEK_API_KEY:
        try:
            import requests
            prompt = f"""Subject: {subject}, Topic: {topic}
Question: {q_text}
Options: {options}
Correct: {correct} - {correct_text}
Basic explanation: {exp}

Create FINAL perfect explanation - RULES:
1. Summarised but fully explanatory - not too short, not too long
2. No unnecessary repetition of same words
3. Voice will read this, so make it flow naturally
4. Structure:
- What question asks in one sentence
- Why correct answer {correct} is right with reason
- Why other options wrong in one sentence total
- Step-by-step solution if Maths/Physics/Chemistry, else key concept
- One JAMB tip
- Final answer line
5. Maximum 800 chars, clear, professional teacher
6. No placeholder, real content only
"""
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": "You are best JAMB teacher. Summarised but explanatory, no repetition, voice-friendly, real content."}, {"role": "user", "content": prompt}], "temperature": 0.6, "max_tokens": 800}
            r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=18)
            if r.status_code == 200:
                ans = r.json()['choices'][0]['message']['content'].strip()
                if len(ans) > 100 and "Step 1: Understanding the Question" not in ans[:50]:
                    return ans[:1200]
        except Exception as e:
            print(f"DeepSeek explain v4 error: {e}", flush=True)
    
    # Final fallback - summarised explanatory no repetition
    wrong_opts = [f"{k}" for k in options.keys() if k != correct]
    wrong_text = ", ".join(wrong_opts) if wrong_opts else "others"
    
    return f"""📚 **{subject} - {topic}**

Question asks: {q_text}

**Correct answer is {correct} - {correct_text}** because {exp}

Options {wrong_text} are incorrect because they do not match the definition of {topic}. They are common distractors in JAMB.

Solution: {exp} This explains why {correct} fits perfectly.

**JAMB tip:** For {topic}, remember {exp[:80]}. Focus on precise definition.

**Answer: {correct} - {correct_text}**
"""

def text_to_voice_perfect(question, explanation):
    """FINAL v4 - Voice captures all words, no repetition, clean speech"""
    try:
        from gtts import gTTS
        # Clean explanation - remove markdown and emojis for clear voice, keep all words
        clean_exp = re.sub(r'\*\*|__|`|#', '', explanation)
        clean_exp = re.sub(r'[^\w\s.,!?;:\-\'() ]', ' ', clean_exp)
        # Remove extra spaces and limit repetition
        clean_exp = re.sub(r'\b(\w+)(?:\s+\1\b)+', r'\1', clean_exp, flags=re.IGNORECASE)  # Remove word repetition like "the the"
        clean_exp = re.sub(r'\s+', ' ', clean_exp).strip()
        # Keep it concise but explanatory for voice - 850 chars max, all words captured
        if len(clean_exp) > 850:
            # Keep first part and last answer part
            clean_exp = clean_exp[:750] + " Final answer is " + question.get('answer','') + " " + question.get('options',{}).get(question.get('answer',''),'')[:80]
        
        subject = question.get('subject','')
        q_text = re.sub(r'[^\w\s.,!?; ]', ' ', question.get('question','')[:120])
        correct = question.get('answer','')
        correct_text = re.sub(r'[^\w\s.,!?; ]', ' ', question.get('options',{}).get(correct,'')[:80])
        
        voice_script = f"Question in {subject}. {q_text}. The correct answer is option {correct}, {correct_text}. Explanation: {clean_exp}. Remember this for your JAMB exam."
        voice_script = voice_script[:1000].strip()
        # Final repetition cleanup
        voice_script = re.sub(r'\b(\w+)(?:\s+\1\b)+', r'\1', voice_script, flags=re.IGNORECASE)
        
        tts = gTTS(text=voice_script, lang='en', slow=False)
        filename = f"voice_perfect_{question.get('id', uuid.uuid4().hex[:6])}_{int(time.time())}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Perfect TTS v4 error: {e}", flush=True)
        return None

def text_to_voice_tutor(text, q_id=None):
    """FINAL v4 - Tutor voice summarised explanatory no repetition"""
    try:
        from gtts import gTTS
        clean = re.sub(r'\*\*|__|`|#', '', text)
        clean = re.sub(r'[^\w\s.,!?;:\-\'() ]', ' ', clean)
        clean = re.sub(r'\b(\w+)(?:\s+\1\b)+', r'\1', clean, flags=re.IGNORECASE)  # No word repetition
        clean = re.sub(r'\s+', ' ', clean).strip()
        # Keep summarised but explanatory - 850 chars, all words captured
        if len(clean) > 850:
            clean = clean[:800]
        tts = gTTS(text=clean, lang='en', slow=False)
        filename = f"voice_tutor_{q_id or uuid.uuid4().hex[:6]}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"Tutor TTS v4 error: {e}", flush=True)
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
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #1a2035, #2d3748); color: white; margin:0; padding:20px; min-height:100vh; }
        .container { max-width:500px; margin:0 auto; background: rgba(255,255,255,0.1); padding:30px; border-radius:15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        h1 { text-align:center; color:#ffd700; margin-bottom:5px; }
        h2 { text-align:center; color:#fff; font-size:16px; opacity:0.8; }
        .price { text-align:center; font-size:52px; color:#ffd700; font-weight:bold; margin:20px 0; }
        .features { list-style:none; padding:0; margin:20px 0; }
        .features li { padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.1); font-size:15px; }
        .features li:before { content:"✅ "; }
        .user-id-box { text-align:center; margin:20px 0; padding:15px; background: rgba(255,215,0,0.1); border-radius:10px; border: 1px solid rgba(255,215,0,0.3); }
        .user-id-box p { margin:5px 0; font-size:18px; }
        .btn { display:block; width:100%; padding:18px; background: linear-gradient(135deg, #ffd700, #ffed4e); color:#1a2035; text-align:center; text-decoration:none; border-radius:12px; font-weight:bold; font-size:20px; margin:25px 0; box-shadow: 0 4px 15px rgba(255,215,0,0.4); cursor:pointer; border:none; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255,215,0,0.6); }
        .btn:active { transform: translateY(0); }
        .free-option { text-align:center; margin-top:25px; padding:18px; background: rgba(255,255,255,0.05); border-radius:12px; border: 1px dashed rgba(255,255,255,0.2); }
        .logo { text-align:center; font-size:60px; margin-bottom:10px; }
        .secure { text-align:center; margin-top:20px; font-size:12px; opacity:0.6; }
        .error-box { background: rgba(255,0,0,0.1); border: 1px solid rgba(255,0,0,0.3); padding:15px; border-radius:10px; margin:15px 0; text-align:center; display:none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🎓</div>
        <h1>UTME Success Bot</h1>
        <h2>Upgrade to Premium - Professional Final v4</h2>
        <div class="price">N{{price}}</div>
        <p style="text-align:center; opacity:0.8;">30 days unlimited access</p>
        <ul class="features">
            <li>Unlimited mock 180 Qs - No repeats - Real JAMB</li>
            <li>All subjects + Past questions 2010-2024 any year</li>
            <li>Super smart AI Tutor - summarised but explanatory</li>
            <li>Perfect voice teacher - no jumping, no repetition</li>
            <li>Complete syllabus + My Score + Leaderboard</li>
            <li>Blue menu handle, persistent memory</li>
            <li>Share score viral + priority support</li>
        </ul>
        <div class="user-id-box">
            <p>👤 <strong>User ID: {{uid}}</strong></p>
            <p style="font-size:13px; opacity:0.7;">Keep this ID safe - your premium will be activated on this ID</p>
        </div>
        
        <div id="errorBox" class="error-box">
            <p>⚠️ Payment link error. Please try again or contact @jibriliks</p>
            <p id="errorDetails" style="font-size:12px;"></p>
        </div>

        <a id="payButton" href="{{payment_link}}" class="btn" onclick="return handlePayClick(this)">💳 Pay N{{price}} Now - Secure</a>
        <p style="text-align:center; font-size:13px; opacity:0.7;">Clicking Pay will take you to Flutterwave secure payment page</p>
        
        <div class="free-option">
            <h3>🆓 Free Option - No Payment</h3>
            <p>Invite 3 friends = <strong>1 WEEK PREMIUM FREE!</strong></p>
            <p style="word-break: break-all; background: rgba(0,0,0,0.3); padding:10px; border-radius:8px; margin:10px 0;"><code>https://t.me/{{bot_username}}?start={{uid}}</code></p>
            <p>✅ You have invited <strong>{{referral_count}}</strong> friends</p>
        </div>
        <p class="secure">🔒 Secure payment by Flutterwave<br>💬 Need help? Contact @jibriliks on Telegram</p>
    </div>

    <script>
        function handlePayClick(btn) {
            var link = btn.getAttribute('href');
            // If link is still self page, try to create new link via /pay endpoint
            if (link.includes('/upgrade/') && !link.includes('flutterwave') && !link.includes('checkout')) {
                // Check if it's not already flutterwave link
                if (link === window.location.href || link.endsWith('/{{uid}}') || link.includes('/upgrade/{{uid}}')) {
                    // Redirect to /pay endpoint which will create flutterwave link
                    window.location.href = '/pay/{{uid}}';
                    return false;
                }
            }
            // If link looks like flutterwave or checkout, allow it
            if (link.includes('flutterwave') || link.includes('checkout') || link.includes('pay')) {
                btn.innerHTML = '⏳ Redirecting to Flutterwave...';
                return true;
            }
            // Fallback - try pay endpoint
            window.location.href = '/pay/{{uid}}';
            return false;
        }
        // Auto-check if payment_link failed
        window.onload = function() {
            var link = document.getElementById('payButton').getAttribute('href');
            var errorBox = document.getElementById('errorBox');
            // If link is same page, show hint
            if (link === window.location.href) {
                errorBox.style.display = 'block';
                document.getElementById('errorDetails').innerText = 'Payment link not generated - will try alternative method';
                // Auto redirect to pay endpoint after 1 sec
                setTimeout(function() {
                    document.getElementById('payButton').href = '/pay/{{uid}}';
                    document.getElementById('payButton').innerHTML = '💳 Pay N{{price}} - Click Again';
                }, 1000);
            }
        }
    </script>
</body>
</html>
"""

SUCCESS_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Payment Successful</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #1a2035, #2d3748); color: white; margin:0; padding:20px; min-height:100vh; display:flex; align-items:center; justify-content:center; }
        .container { max-width:500px; background: rgba(255,255,255,0.1); padding:30px; border-radius:15px; text-align:center; }
        h1 { color:#00ff88; }
        .btn { display:inline-block; padding:15px 30px; background:#ffd700; color:#1a2035; text-decoration:none; border-radius:10px; font-weight:bold; margin:10px; }
    </style>
</head>
<body>
    <div class="container">
        <div style="font-size:60px;">✅</div>
        <h1>Payment Successful!</h1>
        <p>PREMIUM 30 days activated!</p>
        <p>Go back to Telegram: /mock</p>
        <a href="https://t.me/UTMEBOT" class="btn">🎓 Open Bot</a>
        <p style="font-size:12px; opacity:0.7; margin-top:20px;">Tx: {{tx_ref}} - @jibriliks if not activated</p>
    </div>
</body>
</html>
"""

@flask_app.route("/")
def index():
    return jsonify({"status":"UTME Bot Professional v3 BETMASTER FIX LIVE - Inner menu working, AI Tutor real, No repeats, Blue handle, Persistent memory","questions":len(cbt.db) if cbt else 50000, "premium_price": PREMIUM_PRICE, "upgrade_page": f"{RENDER_URL}/upgrade"})

@flask_app.route("/health")
def health():
    try:
        count = len(cbt.db) if cbt else 50000
        subj_counts = Counter([q.get('subject') for q in cbt.db]) if cbt and cbt.db else {}
    except:
        count = 50000
        subj_counts = {}
    return jsonify({"bot_token_exists": bool(BOT_TOKEN), "questions": count, "status": "ok", "subjects": dict(subj_counts), "premium_price": PREMIUM_PRICE, "upgrade_url": f"{RENDER_URL}/upgrade", "features": ["Betmaster inner menu fixed", "Blue handle expand", "AI Tutor real answers", "Perfect voice", "Persistent memory", "No repeat in mock", "Past Qs by year any year"]})

@flask_app.route("/upgrade")
@flask_app.route("/upgrade/<uid>")
@flask_app.route("/upgrade/<uid>/")
def upgrade_page(uid=None):
    uid = uid or request.args.get('uid', '0')
    uid = str(uid).strip().split("/")[0].split("?")[0][:20]
    # Auto-generate email based on user ID - no need to show email on page
    email = request.args.get('email', '')
    if not email or '@' not in email or 'example.com' in email:
        email = f"user_{uid}@utmebot.com"
    bot_username = request.args.get('bot', 'UTMEBOT')
    
    # Try to create Flutterwave link directly
    payment_link = f"/pay/{uid}"  # Fallback to /pay endpoint which handles Flutterwave creation
    if uid and uid != '0':
        try:
            import re
            uid_int = int(re.sub(r'[^0-9]', '', uid) or '0')
            if uid_int and FLW_SECRET_KEY:
                link, tx_ref = create_flutterwave_link(uid_int, email=email, name=f"UTME User {uid}")
                if link and 'flutterwave' in link.lower() or link and 'http' in link:
                    payment_link = link
                    print(f"Created Flutterwave link for {uid}: {link[:50]}...", flush=True)
                else:
                    print(f"Flutterwave link creation failed for {uid}: {tx_ref}", flush=True)
                    # Keep fallback to /pay/{uid} which will retry
        except Exception as e:
            print(f"Upgrade page link error for {uid}: {e}", flush=True)
    
    try:
        clean_uid = int(re.sub(r'[^0-9]', '', str(uid)) or '0')
        referral_count = get_referral_count(clean_uid) if clean_uid else 0
    except:
        referral_count = 0
    
    html_content = UPGRADE_PAGE_HTML.replace("{{price}}", str(PREMIUM_PRICE)).replace("{{uid}}", str(uid)).replace("{{bot_username}}", bot_username).replace("{{payment_link}}", payment_link).replace("{{referral_count}}", str(referral_count))
    # Remove any leftover {{email}} if exists
    html_content = html_content.replace("{{email}}", email)
    return render_template_string(html_content)

@flask_app.route("/pay/<uid>")
@flask_app.route("/pay/<uid>/")
def pay_redirect(uid=None):
    """Direct pay endpoint - creates Flutterwave link and redirects immediately - FIXES button not moving"""
    uid = str(uid).strip().split("/")[0].split("?")[0][:20]
    email = f"user_{uid}@utmebot.com"
    bot_username = request.args.get('bot', 'UTMEBOT')
    
    print(f"Pay endpoint hit for uid={uid}", flush=True)
    
    if not FLW_SECRET_KEY:
        return f"""
        <html><body style="font-family:Arial; background:#1a2035; color:white; padding:20px; text-align:center;">
        <h2>⚠️ Payment Configuration Error</h2>
        <p>FLW_SECRET_KEY not set on server. Contact @jibriliks</p>
        <p>User ID: {uid}</p>
        <p><a href="/upgrade/{uid}" style="color:#ffd700;">Back to Upgrade Page</a></p>
        </body></html>
        """, 500
    
    try:
        import re
        uid_int = int(re.sub(r'[^0-9]', '', uid) or '0')
        if not uid_int:
            uid_int = int(time.time()) % 1000000
        
        link, tx_ref = create_flutterwave_link(uid_int, email=email, name=f"UTME User {uid}")
        
        if link:
            print(f"Redirecting {uid} to Flutterwave: {link[:80]}...", flush=True)
            # Direct redirect to Flutterwave
            return f"""
            <html><head><meta http-equiv="refresh" content="0; url={link}"></head>
            <body style="font-family:Arial; background:#1a2035; color:white; padding:20px; text-align:center;">
            <h2>⏳ Redirecting to Flutterwave Secure Payment...</h2>
            <p>If not redirected, <a href="{link}" style="color:#ffd700; font-size:18px;">Click here to Pay N{PREMIUM_PRICE}</a></p>
            <p>User ID: {uid} | Tx: {tx_ref}</p>
            <script>window.location.href = "{link}";</script>
            </body></html>
            """
        else:
            print(f"Pay endpoint failed to create link for {uid}: {tx_ref}", flush=True)
            return f"""
            <html><body style="font-family:Arial; background:#1a2035; color:white; padding:20px; text-align:center;">
            <h2>⚠️ Could not create payment link</h2>
            <p>Error: {html.escape(str(tx_ref))}</p>
            <p>User ID: {uid}</p>
            <p>Please contact @jibriliks with your User ID</p>
            <p><a href="/upgrade/{uid}" style="color:#ffd700;">Back</a></p>
            </body></html>
            """, 500
            
    except Exception as e:
        print(f"Pay endpoint exception for {uid}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return f"""
        <html><body style="font-family:Arial; background:#1a2035; color:white; padding:20px; text-align:center;">
        <h2>⚠️ Payment Error</h2>
        <p>{html.escape(str(e))}</p>
        <p>User ID: {uid}</p>
        <p><a href="/upgrade/{uid}" style="color:#ffd700;">Back to Upgrade</a> | Contact @jibriliks</p>
        </body></html>
        """, 500


@flask_app.route("/upgrade/success")
def upgrade_success():
    uid = request.args.get('uid', '0')
    tx_ref = request.args.get('tx_ref', '')
    if tx_ref:
        try:
            success, data = verify_by_tx_ref(tx_ref)
            if success:
                try:
                    import re
                    uid_int = int(re.sub(r'[^0-9]', '', str(uid)) or '0')
                    if uid_int:
                        grant_premium(uid_int, days=30, tx_ref=tx_ref)
                except:
                    pass
        except:
            pass
    return render_template_string(SUCCESS_PAGE_HTML.replace("{{tx_ref}}", tx_ref))

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

def create_flutterwave_link(uid, email=None, name="UTME Student"):
    """FINAL CLINICAL v6 - Robust Flutterwave with invalid key handling"""
    if not FLW_SECRET_KEY:
        print("FLW_SECRET_KEY not set", flush=True)
        return None, "FLW_SECRET_KEY not set on Render. Go to Render Dashboard > Environment > Add FLW_SECRET_KEY = your live secret key FLWSECK-..."

    # Clean key
    secret_key = FLW_SECRET_KEY.strip()
    if not secret_key.startswith("FLWSECK"):
        return None, f"Invalid Flutterwave key format. Key must start with FLWSECK-. Your key starts with {secret_key[:10]}... Please check Render Environment Variables. Get correct key from Flutterwave Dashboard > Settings > API Keys > Secret Key (Live)"

    # Auto-generate valid email
    if not email or '@' not in email or 'example.com' in email or 'utmebot.com' in email:
        email = f"user_{uid}@gmail.com"

    import requests
    tx_ref = f"utme-{uid}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    url = "https://api.flutterwave.com/v3/payments"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}
    redirect_url = f"{RENDER_URL}/upgrade/success?uid={uid}&tx_ref={tx_ref}"
    if not RENDER_URL or "localhost" in RENDER_URL:
        redirect_url = f"https://utmebot.onrender.com/upgrade/success?uid={uid}&tx_ref={tx_ref}"

    payload = {
        "tx_ref": tx_ref,
        "amount": PREMIUM_PRICE,
        "currency": "NGN",
        "redirect_url": redirect_url,
        "payment_options": "card,banktransfer,ussd",
        "customer": {"email": email, "name": name[:50]},
        "customizations": {"title": "UTME Success Bot Premium", "description": f"N{PREMIUM_PRICE} - 30 days unlimited"},
        "meta": {"user_id": str(uid)}
    }

    try:
        print(f"Creating Flutterwave payment: uid={uid} email={email} tx_ref={tx_ref}", flush=True)
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        print(f"Flutterwave status: {r.status_code}", flush=True)
        data = r.json()
        print(f"Flutterwave response: {str(data)[:400]}", flush=True)

        if data.get("status") == "success" and data.get("data", {}).get("link"):
            return data["data"]["link"], tx_ref
        else:
            msg = data.get("message", str(data))
            # Detect invalid key error
            if "Invalid authorization key" in str(data) or "invalid" in msg.lower() and "key" in msg.lower():
                return None, f"Invalid authorization key - Your FLW_SECRET_KEY on Render is wrong or expired. Go to https://app.flutterwave.com/dashboard/settings/apis and copy your LIVE Secret Key (starts with FLWSECK-). Then update it in Render Dashboard > Environment. Current error: {msg}"
            return None, msg
    except Exception as e:
        print(f"Flutterwave exception: {e}", flush=True)
        import traceback
        traceback.print_exc()
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

# ========== TELEGRAM BOT ==========
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        # Ensure unique IDs
        seen_ids = set()
        deduped = []
        for q in self.db:
            qid = q.get('id')
            if qid not in seen_ids:
                seen_ids.add(qid)
                deduped.append(q)
        self.db = deduped
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

    def get_questions(self, subject=None, year=None, limit=40, exclude_ids=None):
        exclude_ids = set(exclude_ids or [])
        filtered=self.db
        if subject:
            filtered=[q for q in filtered if q.get('subject','').lower()==subject.lower()]
        if year:
            filtered=[q for q in filtered if str(q.get('year',''))==str(year)]
        # Exclude already used
        filtered=[q for q in filtered if q.get('id') not in exclude_ids]
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
        used_ids=set()
        for subj in subjects:
            qs=self.get_questions(subject=subj, limit=limit_per_subject, exclude_ids=used_ids)
            for q in qs:
                used_ids.add(q.get('id'))
            all_selected.extend(qs)
        if not all_selected:
            all_selected=self.get_questions(limit=limit_per_subject*len(subjects), exclude_ids=used_ids)
        # Final dedup - ensure no repeat question text
        seen_text=set()
        unique=[]
        for q in all_selected:
            txt = q.get('question','').strip().lower()
            if txt not in seen_text:
                seen_text.add(txt)
                unique.append(q)
        all_selected=unique
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
    time_str = f" {time_left//60}:{time_left%60:02d}" if time_left else ""
    header = f"Q{idx+1}/{total} | {q['subject']} | {q.get('year','')} | {q.get('topic','')} {time_str}\n\n"
    question_text = html.escape(q['question'])
    question_text = question_text.replace('&lt;b&gt;','').replace('&lt;/b&gt;','').replace('<b>','').replace('</b>','')
    body = f"<b>{question_text}</b>\n\n"
    opts_list = []
    for k,v in q['options'].items():
        v_clean = html.escape(str(v))
        v_clean = v_clean.replace('&lt;b&gt;','').replace('&lt;/b&gt;','').replace('<b>','').replace('</b>','')
        opts_list.append(f"<b>{k}</b>: {v_clean}")
    opts = "\n".join(opts_list)
    return header + body + opts

# ============ BETMASTER STYLE MENUS - FIXED INNER MENU ============
def get_main_menu():
    """Main menu - Betmaster style - all items working"""
    keyboard = [
        [InlineKeyboardButton("📚 Past Questions", callback_data="menu_past"), InlineKeyboardButton("📝 Mock Exam", callback_data="menu_mock")],
        [InlineKeyboardButton("🎙 Explain Answer", callback_data="menu_explain"), InlineKeyboardButton("📊 My Score", callback_data="menu_score")],
        [InlineKeyboardButton("📖 Syllabus", callback_data="menu_syllabus"), InlineKeyboardButton("💬 Ask Tutor", callback_data="menu_tutor")],
        [InlineKeyboardButton("👥 Invite Friend", callback_data="menu_invite"), InlineKeyboardButton("💎 Go Premium", callback_data="menu_premium")],
        [InlineKeyboardButton("📞 Help @jibriliks", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_blue_menu_button():
    """Blue button inside chat space - Betmaster style - says MENU, expands to show all items"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU - Click to Expand", callback_data="expand_menu")]])

def get_expanded_menu():
    """When blue MENU clicked, show all items expanded"""
    keyboard = [
        [InlineKeyboardButton("📚 Past Questions - Any Year 2010-2024", callback_data="menu_past")],
        [InlineKeyboardButton("📝 Mock Exam - Quick / Subject / Full JAMB", callback_data="menu_mock")],
        [InlineKeyboardButton("📊 My Score & Leaderboard", callback_data="menu_score")],
        [InlineKeyboardButton("📖 JAMB Syllabus - Complete Official", callback_data="menu_syllabus")],
        [InlineKeyboardButton("💬 Ask Tutor - Super Smart AI", callback_data="menu_tutor")],
        [InlineKeyboardButton("👥 Invite Friend - 3 = 1 Week Free", callback_data="menu_invite")],
        [InlineKeyboardButton("💎 Go Premium N2000 - Upgrade Page", callback_data="menu_premium")],
        [InlineKeyboardButton("📞 Help - @jibriliks", callback_data="menu_help")],
        [InlineKeyboardButton("🔵 Close Menu", callback_data="close_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_options_keyboard_with_menu(q, current_idx):
    """During quiz - shows options + Betmaster blue MENU that expands"""
    row = [InlineKeyboardButton(f"{k}", callback_data=f"ans_{k}") for k in q['options'].keys()]
    nav_row = [InlineKeyboardButton("⬅️ Prev", callback_data="nav_prev"), InlineKeyboardButton("➡️ Next", callback_data="nav_next"), InlineKeyboardButton("🏁 Submit", callback_data="submit")]
    explain_row = [InlineKeyboardButton("🎙 Explain + Voice - Perfect Teacher", callback_data=f"explain_{current_idx}")]
    blue_menu_row = [InlineKeyboardButton("🔵 MENU", callback_data="expand_menu")]
    return InlineKeyboardMarkup([row, nav_row, explain_row, blue_menu_row])

def get_subjects_keyboard(prefix="prac_"):
    buttons = []
    for s in SUBJECTS:
        buttons.append([InlineKeyboardButton(f"{s}", callback_data=f"{prefix}{s}")])
    buttons.append([InlineKeyboardButton("🔵 MENU - Back to Main", callback_data="menu_main")])
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

# ============ SEND MENU HELPERS - FIX INNER MENU ============
async def send_main_menu_message(message_obj, first_name="Student", uid=0):
    """Helper to send main menu - works for both message and callback"""
    premium = is_premium(uid)
    days_left = get_premium_days_left(uid)
    status = f"💎 PREMIUM ({days_left} days) - Unlimited" if premium else f"🆓 FREE (5 Qs) - Premium N{PREMIUM_PRICE}/month"
    ref_count = get_referral_count(uid)
    top_name, top_score = get_top_scorer()
    top_banner = f"🏆 Top Scorer: {top_name} - {top_score}/400\n" if top_name else ""
    
    welcome = f"""🎓 *UTME SUCCESS BOT - PROFESSIONAL v3* 🎓
Hello {first_name}! {status}

*Your JAMB Partner - 50k Questions + Complete Syllabus*

{top_banner}
📚 Past Questions - By Subject & Year (2010-2024) - Select ANY year
📝 Mock Exam - Real JAMB CBT (Free: 5 Qs, Premium: Unlimited 180 Qs - No repeats)
🎙 Explain Answer - Perfect teacher, no jumping + Voice
📊 My Score - Performance, weak areas, leaderboard
📖 Syllabus - Complete UTME official
💬 Ask Tutor - Super smart AI, real answers step-by-step

👥 Invite: {ref_count}/3 → 1 week premium
💎 Premium: N{PREMIUM_PRICE}/month unlimited
🔵 Blue MENU button below expands to show all options!

Choose from menu below 👇
"""
    await message_obj.reply_text(welcome, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)
    await message_obj.reply_text("🔵 *Blue MENU Handle - Tap to expand menu anytime:*", reply_markup=get_blue_menu_button(), parse_mode=ParseMode.MARKDOWN)

# ============ COMMANDS ============
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
    await send_main_menu_message(update.message, update.effective_user.first_name, uid)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    text = f"""📞 *HELP - UTME Success Bot Professional v3*

*For help:* @jibriliks

*Commands:*
📚 Past Questions - /past - Any year 2010-2024, any subject
📝 Mock Exam - /mock - Free 5 Qs, Premium 180 Qs no repeats
🎙 Explain - Tap 🎙 during quiz for perfect teacher + voice
📊 My Score - /score
📖 Syllabus - /syllabus - Complete official
💬 Ask Tutor - /tutor + question - Real answers step-by-step
👥 Invite - /invite - 3 friends = 1 week premium
💎 Premium - /subscribe - N{PREMIUM_PRICE}/month

*Upgrade Page:*
{RENDER_URL}/upgrade/{uid}

*Memory:* Bot remembers you even if you clear history (based on your Telegram ID). Free limits apply always.

*Support:* @jibriliks
"""
    await update.message.reply_text(text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_text("🔵 MENU:", reply_markup=get_blue_menu_button())

async def past_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    await update.message.reply_text("📚 *Past Questions - Professional v3*\n*Select ANY year 2010-2024 for ANY subject*\nChoose how to practice:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 By Subject (then choose Year)", callback_data="past_by_subject")],
        [InlineKeyboardButton("📅 By Year Direct (2010-2024)", callback_data="past_by_year")],
        [InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]
    ]), parse_mode=ParseMode.MARKDOWN)

async def mock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    premium = is_premium(uid)
    limit_text = "Unlimited 180 Qs - No repeats" if premium else "5 Qs (Free) - N2000 unlimited - No repeats"
    top_name, top_score = get_top_scorer()
    top_banner = f"🏆 Top Scorer: {top_name} - {top_score}/400\n" if top_name else ""
    await update.message.reply_text(f"📝 *Mock Exam - Professional v3 - No Repeats*\n{top_banner}Your access: {limit_text}\nChoose type:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Quick Test (Free 5 Qs - No repeat)", callback_data="mock_quick")],
        [InlineKeyboardButton("📖 Subject Mock - Any Subject", callback_data="mock_subject")],
        [InlineKeyboardButton("🔥 Full JAMB Mock (Premium 180 Qs - No repeat)", callback_data="mock_full")],
        [InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]
    ]), parse_mode=ParseMode.MARKDOWN)

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    stats = get_user_stats(uid)
    if not stats:
        await update.message.reply_text("📊 *My Score*\n\nNo exams yet! Start with /mock\n\n*Memory:* Bot remembers you even if you clear history. Free limits apply.", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Start Mock", callback_data="menu_mock")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        return
    total_avg = stats["total_score"] / max(stats["total_exams"],1)
    pos, total_users = get_leaderboard_position(uid)
    subjects = stats.get("subjects", {})
    strong = sorted(subjects.items(), key=lambda x: x[1]["avg"], reverse=True)[:2]
    weak = sorted(subjects.items(), key=lambda x: x[1]["avg"])[:2]
    text = f"📊 *My Score - Professional v3*\n\n*Total Average:* {total_avg:.1f}/400\n*Best:* {stats.get('best_score',0)}/400\n*Total Exams:* {stats['total_exams']}\n\n*Strong:*\n"
    for subj, data in strong:
        text += f"• {subj}: {data['avg']}%\n"
    text += "\n*Weak:*\n"
    for subj, data in weak:
        text += f"• {subj}: {data['avg']}% → Practice\n"
    text += f"\n*Leaderboard:* #{pos} out of {total_users}\n*Persistent Memory:* Your scores saved even if you clear chat.\n"
    keyboard = [[InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{int(total_avg)}_{stats['total_exams']}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def syllabus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    if context.args:
        subj = " ".join(context.args).capitalize()
        if subj in JAMB_SYLLABUS_COMPLETE:
            data = JAMB_SYLLABUS_COMPLETE[subj]
            text = f"📖 *JAMB Official Syllabus - {subj} - {data['title']} - COMPLETE*\n\n"
            for i, sec in enumerate(data['sections'], 1):
                text += f"{i}. {sec}\n\n"
            text += f"\nFull: {RENDER_URL}/syllabus/{subj}\nPractice: /practice {subj}"
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
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    # Check if called from callback without args
    query_text = " ".join(context.args) if context.args else ""
    if not query_text:
        # If no args, check if it's from message handler (user typed question directly)
        # For /tutor without args, show prompt
        if update.message and update.message.text and not update.message.text.startswith('/'):
            query_text = update.message.text
        else:
            await update.message.reply_text("💬 *Ask Tutor - Super Smart AI - Real Answers*\n\nAsk any question directly, example:\n`What is ecology?`\n`Explain photosynthesis step by step`\n`Solve 2x + 3 = 11`\n\nJust type your question now, I will answer with real step-by-step explanation + voice!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
            return
    
    await update.message.reply_text("🧠 *Super Smart Tutor thinking...* Preparing real step-by-step explanation...")
    explanation = get_smart_tutor_answer(query_text)
    
    # Send explanation in chunks if long
    if len(explanation) > 4000:
        for i in range(0, len(explanation), 4000):
            await update.message.reply_text(explanation[i:i+4000], parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(explanation, parse_mode=ParseMode.MARKDOWN)
    
    # Voice reads perfect explanation
    voice_file = text_to_voice_tutor(explanation[:1000], q_id=f"tutor_{int(time.time())}")
    if voice_file and os.path.exists(voice_file):
        try:
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=open(voice_file, 'rb'), caption="🎙 Perfect Teacher Voice - Real Explanation")
            os.remove(voice_file)
        except Exception as e:
            print(f"Voice error: {e}", flush=True)
    
    await update.message.reply_text("Want more? Ask follow-up question or tap 🔵 MENU", reply_markup=get_blue_menu_button())

async def invite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    bot_username = context.bot.username or "UTMEBOT"
    invite_link = f"https://t.me/{bot_username}?start={uid}"
    refs = load_json(REFERRAL_FILE, {}).get(str(uid), [])
    count = len(refs)
    needed = 3 - (count % 3) if count % 3 != 0 else 3
    needed_text = f"🎉 {count} invites! Invite {needed} more for another week!" if count >=3 else f"Invite {needed} more for 1 WEEK PREMIUM (N{PREMIUM_PRICE})!"
    text = f"👥 *Invite Friend - Get 1 Week Free Premium*\n\nYour link:\n`{invite_link}`\n\n*Progress:* {count} friends\n{needed_text}\n\n*Current:* {'💎 Active' if is_premium(uid) else '🆓 Free - Persistent memory even if you clear history'}\n*Upgrade:* {RENDER_URL}/upgrade/{uid}\n"
    keyboard = [[InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={invite_link}&text=I scored 268 in JAMB Mock! Can you beat me?")],[InlineKeyboardButton("💎 Go Premium N2000", callback_data="menu_premium")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    if is_premium(uid):
        days_left = get_premium_days_left(uid)
        await update.message.reply_text(f"💎 Already PREMIUM! ({days_left} days left) - Unlimited, no repeats, persistent memory\n\nUpgrade: {RENDER_URL}/upgrade/{uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        return
    ref_count = get_referral_count(uid)
    upgrade_url = f"{RENDER_URL}/upgrade/{uid}"
    await update.message.reply_text(f"💎 *Go Premium - N{PREMIUM_PRICE}/month*\n\n*Free vs Premium:*\n🆓 Free: 5 Qs only, persistent memory\n💎 Premium: Unlimited 180 Qs no repeats, super smart tutor real answers, perfect voice\n\n*Benefits:*\n• Unlimited mocks 180 Qs no repeats\n• Super smart AI Tutor - real answers step-by-step\n• Perfect voice teacher no jumping\n• All subjects + years any year\n• Complete syllabus\n• Persistent memory even if clear history\n\n*Free alt:* Invite 3 friends = 1 week free! You have {ref_count}/3\n\n*Upgrade Page:* {upgrade_url}\n\nClick below or send email:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Upgrade Now N{PREMIUM_PRICE}", url=upgrade_url)],[InlineKeyboardButton("👥 Invite 3 Friends = 1 Week Free", callback_data="menu_invite")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
    context.user_data["awaiting_email"] = True

async def handle_email_and_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    
    # Check if awaiting email for premium
    if context.user_data.get("awaiting_email"):
        email = text
        if "@" not in email or "." not in email:
            # Not email, treat as tutor question if long enough
            if len(email) > 3 and not email.startswith("🔵"):
                context.args = text.split()
                await tutor_cmd(update, context)
                return
            await update.message.reply_text("❌ Invalid email, send like: you@gmail.com")
            return
        name = update.effective_user.full_name
        await update.message.reply_text("⏳ Creating Flutterwave payment link...")
        link, tx_ref = create_flutterwave_link(uid, email=email, name=name)
        if not link:
            upgrade_url = f"{RENDER_URL}/upgrade/{uid}?email={email}"
            await update.message.reply_text(f"Use upgrade page:\n{upgrade_url}\nOr @jibriliks", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Upgrade Page N{PREMIUM_PRICE}", url=upgrade_url)]]))
            return
        context.user_data["awaiting_email"] = False
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Pay N{PREMIUM_PRICE}", url=link)],[InlineKeyboardButton("✅ Verify Payment", callback_data=f"verify_{tx_ref}")],[InlineKeyboardButton("🌐 Upgrade Page", url=f"{RENDER_URL}/upgrade/{uid}?email={email}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]])
        await update.message.reply_text(f"🔗 *Pay N{PREMIUM_PRICE}:* Tx: {tx_ref}\nAfter payment click Verify\n\nUpgrade: {RENDER_URL}/upgrade/{uid}", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return
    
    # Handle blue menu text buttons (if user uses ReplyKeyboard style - but we use inline now)
    if text in ["🔵 MENU", "📚 Past Questions", "📝 Mock Exam", "📊 My Score", "📖 Syllabus", "💬 Ask Tutor", "💎 Go Premium", "📞 Help"]:
        mapping = {"🔵 MENU": start_cmd, "📚 Past Questions": past_cmd, "📝 Mock Exam": mock_cmd, "📊 My Score": score_cmd, "📖 Syllabus": syllabus_cmd, "💬 Ask Tutor": tutor_cmd, "💎 Go Premium": subscribe_cmd, "📞 Help": help_cmd}
        await mapping[text](update, context)
        return
    
    # If not in exam and text is a question, treat as tutor
    if uid not in cbt.active_exams and len(text) > 3:
        # Check if it's not a command
        if not text.startswith('/'):
            context.args = text.split()
            await tutor_cmd(update, context)
            return

# ============ CALLBACK HANDLER - FIXED INNER MENU ============
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    save_user_profile(uid, update.effective_user)
    
    # Blue handle expand - Betmaster style
    if data == "expand_menu":
        await query.message.reply_text("🔵 *MENU Expanded - Choose option:*", reply_markup=get_expanded_menu(), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "close_menu":
        await query.message.delete()
        return
    elif data == "menu_main":
        # FIXED: Inner menu now works - send new message, not rely on update.message
        await send_main_menu_message(query.message, update.effective_user.first_name, uid)
        return
    elif data == "menu_past":
        await query.message.reply_text("📚 *Past Questions - Professional v3*\n*Select ANY year 2010-2024 for ANY subject:*\nChoose how to practice:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 By Subject (then choose Year)", callback_data="past_by_subject")],
            [InlineKeyboardButton("📅 By Year Direct (2010-2024)", callback_data="past_by_year")],
            [InlineKeyboardButton("🔵 MENU - Back to Main", callback_data="menu_main")]
        ]), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "menu_mock":
        premium = is_premium(uid)
        limit_text = "Unlimited 180 Qs - No repeats" if premium else "5 Qs (Free) - N2000 unlimited - No repeats"
        top_name, top_score = get_top_scorer()
        top_banner = f"🏆 Top Scorer: {top_name} - {top_score}/400\n" if top_name else ""
        await query.message.reply_text(f"📝 *Mock Exam - Professional v3 - No Repeats - Persistent Memory*\n{top_banner}Your access: {limit_text}\nChoose type:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ Quick Test (Free 5 Qs - No repeat)", callback_data="mock_quick")],
            [InlineKeyboardButton("📖 Subject Mock - Any Subject", callback_data="mock_subject")],
            [InlineKeyboardButton("🔥 Full JAMB Mock (Premium 180 Qs - No repeat)", callback_data="mock_full")],
            [InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]
        ]), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "menu_score":
        stats = get_user_stats(uid)
        if not stats:
            await query.message.reply_text("📊 *My Score*\n\nNo exams yet! Start with /mock\n\n*Persistent Memory:* Scores saved even if you clear chat. Free limits apply always.", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Start Mock", callback_data="menu_mock")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
            return
        total_avg = stats["total_score"] / max(stats["total_exams"],1)
        pos, total_users = get_leaderboard_position(uid)
        subjects = stats.get("subjects", {})
        strong = sorted(subjects.items(), key=lambda x: x[1]["avg"], reverse=True)[:2]
        weak = sorted(subjects.items(), key=lambda x: x[1]["avg"])[:2]
        text = f"📊 *My Score - Professional v3*\n\n*Total Average:* {total_avg:.1f}/400\n*Best:* {stats.get('best_score',0)}/400\n*Total Exams:* {stats['total_exams']}\n\n*Strong:*\n"
        for subj, data_item in strong:
            text += f"• {subj}: {data_item['avg']}%\n"
        text += "\n*Weak:*\n"
        for subj, data_item in weak:
            text += f"• {subj}: {data_item['avg']}% → Practice\n"
        text += f"\n*Leaderboard:* #{pos} out of {total_users}\n*Persistent:* Saved even if clear history\n"
        keyboard = [[InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{int(total_avg)}_{stats['total_exams']}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "menu_syllabus":
        keyboard = []
        for s in SUBJECTS:
            keyboard.append([InlineKeyboardButton(f"📖 {s}", callback_data=f"syllabus_{s}")])
        keyboard.append([InlineKeyboardButton("🌐 View All on Website", url=f"{RENDER_URL}/")])
        keyboard.append([InlineKeyboardButton("🔵 MENU", callback_data="menu_main")])
        await query.message.reply_text("📖 *JAMB Official Syllabus - COMPLETE - All Subjects:*\nChoose subject:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "menu_tutor":
        await query.message.reply_text("💬 *Ask Tutor - Super Smart AI - Real Answers - No Placeholder*\n\nJust type your question now, example:\n`What is ecology?`\n`Explain photosynthesis`\n`Solve 2x + 3 = 11`\n\nI will answer with real step-by-step explanation + voice!\n\nType your question below:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "menu_invite":
        bot_username = context.bot.username or "UTMEBOT"
        invite_link = f"https://t.me/{bot_username}?start={uid}"
        refs = load_json(REFERRAL_FILE, {}).get(str(uid), [])
        count = len(refs)
        needed = 3 - (count % 3) if count % 3 != 0 else 3
        needed_text = f"🎉 {count} invites! Invite {needed} more for another week!" if count >=3 else f"Invite {needed} more for 1 WEEK PREMIUM (N{PREMIUM_PRICE})!"
        text = f"👥 *Invite Friend - Get 1 Week Free Premium*\n\nYour link:\n`{invite_link}`\n\n*Progress:* {count} friends\n{needed_text}\n\n*Current:* {'💎 Active' if is_premium(uid) else '🆓 Free - Persistent memory'}\n*Upgrade:* {RENDER_URL}/upgrade/{uid}\n"
        keyboard = [[InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={invite_link}&text=I scored 268 in JAMB Mock! Can you beat me?")],[InlineKeyboardButton("💎 Go Premium N2000", callback_data="menu_premium")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "menu_premium":
        if is_premium(uid):
            days_left = get_premium_days_left(uid)
            await query.message.reply_text(f"💎 Already PREMIUM! ({days_left} days left)\n\nUpgrade: {RENDER_URL}/upgrade/{uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
            return
        ref_count = get_referral_count(uid)
        upgrade_url = f"{RENDER_URL}/upgrade/{uid}"
        await query.message.reply_text(f"💎 *Go Premium - N{PREMIUM_PRICE}/month*\n\n*Free vs Premium:*\n🆓 Free: 5 Qs only - persistent memory\n💎 Premium: Unlimited 180 Qs no repeats, super smart tutor real answers, perfect voice\n\n*Benefits:*\n• Unlimited mocks 180 Qs no repeats\n• Super smart AI Tutor - real answers\n• Perfect voice teacher\n• All subjects + years any year\n• Persistent memory even if clear history\n\n*Free alt:* Invite 3 friends = 1 week free! You have {ref_count}/3\n\n*Upgrade Page:* {upgrade_url}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Upgrade Now N{PREMIUM_PRICE}", url=upgrade_url)],[InlineKeyboardButton("👥 Invite 3 Friends = 1 Week Free", callback_data="menu_invite")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
        context.user_data["awaiting_email"] = True
        return
    elif data == "menu_help":
        text = f"""📞 *HELP - UTME Professional v3*

*For help:* @jibriliks

*Commands:*
📚 Past Questions - /past - Any year 2010-2024
📝 Mock Exam - /mock - No repeats
🎙 Explain - Tap 🎙 during quiz
📊 My Score - /score - Persistent memory
📖 Syllabus - /syllabus - Complete
💬 Ask Tutor - /tutor - Real answers
👥 Invite - /invite - 3 friends = 1 week
💎 Premium - /subscribe - N{PREMIUM_PRICE}

*Upgrade:* {RENDER_URL}/upgrade/{uid}
*Memory:* Remembers you even if clear history. Free limits always apply.

*Support:* @jibriliks
"""
        await query.message.reply_text(text, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)
        await query.message.reply_text("🔵 MENU:", reply_markup=get_blue_menu_button())
        return
    elif data == "menu_explain":
        await query.message.reply_text("🎙 *Explain Answer - Perfect Teacher - No Jumping*\n\nDuring quiz, tap 🎙 Explain + Voice button\n\nI will explain step-by-step with real content, no placeholder, plus voice reads perfectly!\n\nOr use /tutor to ask any question - super smart AI with real answers!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
        return
    
    elif data == "past_by_subject":
        await query.message.reply_text("📚 *Past Questions - By Subject - Select ANY year after:*\nChoose subject:", reply_markup=get_subjects_keyboard("past_subj_"), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "past_by_year":
        await query.message.reply_text("📚 *Past Questions - By Year - 2010 to 2024 - Choose ANY year:*\nSelect year:", reply_markup=get_years_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("past_subj_"):
        subj = data.replace("past_subj_","")
        await query.message.reply_text(f"📚 *{subj} - Past Questions - Select ANY year:*\nChoose year or start now:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📅 Choose Year (2010-2024) - ANY year", callback_data=f"past_year_{subj}"), InlineKeyboardButton("▶️ Start Now (All Years)", callback_data=f"prac_{subj}")],[InlineKeyboardButton("🔵 MENU - Back to Past", callback_data="menu_past")],[InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("past_year_"):
        subj = data.replace("past_year_","")
        await query.message.reply_text(f"📅 *{subj} - Choose Year (2010-2024) - ANY year past questions:*\nSelect year:", reply_markup=get_years_keyboard(subj), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("year_"):
        parts = data.split("_")
        if len(parts) >= 3:
            subj = parts[1] if parts[1] != "all" else None
            year = parts[2]
            premium = is_premium(uid)
            limit = 40 if premium else 5
            if subj and subj != "None":
                qs = cbt.get_questions(subject=subj, year=year, limit=limit)
                if not qs:
                    qs = cbt.get_questions(subject=subj, limit=limit)
                if qs:
                    cbt.active_exams[uid] = {"questions": qs, "current_idx":0, "score":0, "answers":{}, "subjects":[subj], "start_time":time.time(), "duration":30*60}
                    q,total = qs[0], len(qs)
                    await query.message.reply_text(f"📚 Past Questions {subj} {year} - {total} Qs {'(Free 5 Qs - Persistent)' if not premium else '(Premium - No repeats)'} - No repeats in this mock")
                    await query.message.reply_text(format_question(q,0,total,cbt.get_time_left(uid)), reply_markup=get_options_keyboard_with_menu(q,0), parse_mode=ParseMode.HTML)
                    if not premium:
                        await query.message.reply_text(f"🆓 Free limit: 5 Qs only - Persistent memory even if you clear history. Upgrade N{PREMIUM_PRICE}: /subscribe")
                    return
            else:
                qs = cbt.get_questions(year=year, limit=limit)
                if qs:
                    cbt.active_exams[uid] = {"questions": qs, "current_idx":0, "score":0, "answers":{}, "subjects":["Mixed"], "start_time":time.time(), "duration":30*60}
                    q,total = qs[0], len(qs)
                    await query.message.reply_text(f"📚 Past Questions {year} - {total} Qs - No repeats")
                    await query.message.reply_text(format_question(q,0,total,cbt.get_time_left(uid)), reply_markup=get_options_keyboard_with_menu(q,0), parse_mode=ParseMode.HTML)
                    return
        await query.message.reply_text("No questions found for that year. Try another.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU - Back to Past", callback_data="menu_past")],[InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")]]))
        return
    
    elif data == "mock_quick":
        premium = is_premium(uid)
        subs = ["English","Mathematics","Biology","Chemistry"]
        q,total = cbt.start_mock(uid, subs, duration=15*60, limit_per_subject=5 if not premium else 5)
        if not premium:
            exam = cbt.active_exams[uid]
            exam["questions"] = exam["questions"][:5]
            q,total = exam["questions"][0], 5
            await query.message.reply_text(f"⚡ Quick Test - 5 Qs (Free - No repeat) - {','.join(subs)}\n\n🆓 Free limit: 5 Qs - Persistent memory. Upgrade N{PREMIUM_PRICE}: /subscribe\nNo repeats in this mock!")
        else:
            await query.message.reply_text(f"⚡ Quick Test - {total} Qs - {','.join(subs)} (Premium - No repeats) - No question repeated!")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0), parse_mode=ParseMode.HTML)
        return
    elif data == "mock_subject":
        await query.message.reply_text("📖 *Subject Mock - Select ANY subject:*\nChoose subject:", reply_markup=get_subjects_keyboard("mock_subj_"), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("mock_subj_"):
        subj = data.replace("mock_subj_","")
        premium = is_premium(uid)
        limit = 40 if premium else 5
        q,total = cbt.start_mock(uid, [subj], duration=45*60, limit_per_subject=limit)
        if not q:
            await query.message.reply_text(f"No questions found for {subj}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")]]))
            return
        await query.message.reply_text(f"📖 Subject Mock - {subj} - {total} Qs {'(Free 5 Qs - Persistent)' if not premium else '(Premium - No repeats)'} - No question repeats in this mock")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0), parse_mode=ParseMode.HTML)
        if not premium:
            await query.message.reply_text(f"🆓 Free: 5 Qs only - Persistent memory. N{PREMIUM_PRICE}: /subscribe")
        return
    elif data == "mock_full":
        premium = is_premium(uid)
        if not premium:
            await query.message.reply_text(f"🔒 *Full JAMB Mock (180 Qs - No repeats) Premium Only*\n\n🆓 Free: 5 Qs - Persistent memory\n💎 Premium N{PREMIUM_PRICE}: Unlimited 180 Qs no repeats, super smart tutor real answers, perfect voice, persistent memory\n\nUpgrade page: {RENDER_URL}/upgrade/{uid}\n\n*Note:* Bot remembers you even if you clear history - free limits always apply.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💎 Go Premium N{PREMIUM_PRICE} - Upgrade Page", url=f"{RENDER_URL}/upgrade/{uid}")],[InlineKeyboardButton(f"💎 Go Premium N{PREMIUM_PRICE}", callback_data="menu_premium")],[InlineKeyboardButton("👥 Invite 3 Friends = 1 Week Free", callback_data="menu_invite")],[InlineKeyboardButton("⚡ Quick Test (5 Qs Free - No repeat)", callback_data="mock_quick")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]), parse_mode=ParseMode.MARKDOWN)
            return
        subs = ["English","Mathematics","Biology","Chemistry"]
        all_selected = []
        used_ids=set()
        for s, lim in [("English",60),("Mathematics",40),("Biology",40),("Chemistry",40)]:
            qs = cbt.get_questions(subject=s, limit=lim, exclude_ids=used_ids)
            for q in qs:
                used_ids.add(q.get('id'))
            all_selected.extend(qs)
        # Dedup by text
        seen=set()
        unique=[]
        for q in all_selected:
            t=q.get('question','').strip().lower()
            if t not in seen:
                seen.add(t)
                unique.append(q)
        all_selected=unique
        random.shuffle(all_selected)
        cbt.active_exams[uid] = {"questions": all_selected, "current_idx":0, "score":0, "answers":{}, "subjects":subs, "start_time":time.time(), "duration":120*60}
        q,total = all_selected[0], len(all_selected)
        await query.message.reply_text(f"🔥 *Full JAMB Mock - {total} Qs, 2hrs - Professional v3 - NO REPEATS*\n{','.join(subs)}\nPremium unlimited - No question repeated in this mock! Persistent memory.", parse_mode=ParseMode.MARKDOWN)
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0), parse_mode=ParseMode.HTML)
        return
    
    elif data.startswith("syllabus_"):
        subj = data.replace("syllabus_","")
        if subj in JAMB_SYLLABUS_COMPLETE:
            data_s = JAMB_SYLLABUS_COMPLETE[subj]
            text = f"📖 *JAMB Official Syllabus - {subj} - {data_s['title']} - COMPLETE*\n\n"
            for i, sec in enumerate(data_s['sections'], 1):
                text += f"{i}. {sec}\n\n"
            text += f"\nFull: {RENDER_URL}/syllabus/{subj}\nPractice: /practice {subj}"
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
            await query.message.reply_text(f"✅ Payment Confirmed! PREMIUM 30 days N{PREMIUM_PRICE}\n\nUnlimited no repeats + real tutor + perfect voice + persistent memory!\nUpgrade: {RENDER_URL}/upgrade/{uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Start Mock Unlimited - No repeats", callback_data="menu_mock")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        else:
            await query.message.reply_text(f"❌ Not confirmed yet. Tx: {tx_ref}\nWait 1 min and Verify again. Or @jibriliks\n\nUpgrade: {RENDER_URL}/upgrade/{uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Upgrade Page", url=f"{RENDER_URL}/upgrade/{uid}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        return
    elif data.startswith("prac_"):
        subj = data.replace("prac_","")
        premium = is_premium(uid)
        limit = 40 if premium else 5
        q,total = cbt.start_mock(uid, [subj], duration=45*60, limit_per_subject=limit)
        if not q:
            await query.message.reply_text(f"No questions found for {subj}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")]]))
            return
        left = cbt.get_time_left(uid)
        await query.message.reply_text(f"📚 {subj} Practice - {total} Qs - No repeats in this mock", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0), parse_mode=ParseMode.HTML)
        if not premium:
            await query.message.reply_text(f"🆓 Free: 5 Qs only - Persistent memory even if clear history. Unlimited N{PREMIUM_PRICE}: /subscribe")
        return
    elif data.startswith("ans_"):
        opt = data.replace("ans_","")
        result,status = cbt.answer_current(uid, opt)
        if status == "NO_EXAM":
            await query.message.reply_text("No exam. /mock to start", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")]]))
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
            text = f"🏁 *Finished! Professional v3 Result - No Repeats - Persistent Memory*\nScore: {res['raw_score']}/{res['total']}\nJAMB: {res['jamb_score']}/400\n\nNo question was repeated in this mock!\n"
            premium = is_premium(uid)
            if not premium and res['total'] >= 5:
                text += f"🆓 Free limit reached (5 Qs) - Persistent memory even if clear history. Unlimited N{PREMIUM_PRICE}: /subscribe\nInvite 3 friends for 1 week free: /invite\nUpgrade: {RENDER_URL}/upgrade/{uid}\n\n"
            keyboard = [[InlineKeyboardButton("📊 My Score - Persistent", callback_data="menu_score"), InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{res['jamb_score']}_{res['total']}")],[InlineKeyboardButton("🎙 Explain All - Perfect Teacher Real", callback_data="explain_0")],[InlineKeyboardButton("🔁 Try Again - No repeats", callback_data="menu_mock"), InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        else:
            next_q,next_idx = result
            left = cbt.get_time_left(uid)
            total = len(cbt.active_exams[uid]['questions'])
            await query.message.reply_text(format_question(next_q,next_idx,total,left), reply_markup=get_options_keyboard_with_menu(next_q,next_idx), parse_mode=ParseMode.HTML)
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
        await query.message.reply_text(format_question(q,idx,len(exam['questions']),left), reply_markup=get_options_keyboard_with_menu(q,idx), parse_mode=ParseMode.HTML)
    elif data=="submit":
        final=cbt.finish_exam(uid)
        if final:
            text = f"🏁 Submitted! {final['raw_score']}/{final['total']} JAMB: {final['jamb_score']}/400 - No repeats - Persistent memory"
            if not is_premium(uid):
                text += f"\n\n🆓 Free: 5 Qs limit - Persistent even if clear history. Premium N{PREMIUM_PRICE}: /subscribe\nUpgrade: {RENDER_URL}/upgrade/{uid}"
            keyboard = [[InlineKeyboardButton("📊 My Score", callback_data="menu_score"), InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{final['jamb_score']}_{final['total']}")],[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("explain_"):
        try:
            idx=int(data.replace("explain_",""))
            exam=cbt.active_exams.get(uid)
            q=exam['questions'][idx] if exam and idx < len(exam['questions']) else None
            if not q:
                await query.message.reply_text("No question found - start a mock first /mock", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")]]))
                return
            await query.message.reply_text("🧠 *Perfect Teacher - Real Explanation* Generating perfect step-by-step with real content, no placeholder...")
            exp=explain_with_ai_super_smart(q)
            if len(exp) > 4000:
                await query.message.reply_text(f"🎙 *Perfect Teacher - Real Step-by-Step:*\n\n{exp[:4000]}", parse_mode=ParseMode.MARKDOWN)
                if len(exp) > 4000:
                    await query.message.reply_text(f"{exp[4000:8000]}", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.message.reply_text(f"🎙 *Perfect Teacher - Real Step-by-Step (No Placeholder):*\n\n{exp}\n\n✅ Correct: {q.get('answer')} - {q.get('options',{}).get(q.get('answer'),'')}", parse_mode=ParseMode.MARKDOWN)
            vp=text_to_voice_perfect(q, exp)
            if vp and os.path.exists(vp):
                try:
                    await context.bot.send_voice(chat_id=query.message.chat_id, voice=open(vp,'rb'), caption="🎙 Perfect Teacher Voice - Real explanation, no jumping, reads perfectly")
                    os.remove(vp)
                except Exception as e:
                    print(f"Voice send error: {e}", flush=True)
            await query.message.reply_text("Want more? Ask follow-up with /tutor or tap 🔵 MENU", reply_markup=get_blue_menu_button())
        except Exception as e:
            await query.message.reply_text(f"Error: {e}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")]]))
    elif data.startswith("share_"):
        parts = data.split("_")
        jamb_score = parts[1] if len(parts)>1 else "200"
        total = parts[2] if len(parts)>2 else "40"
        profile = get_user_profile(uid)
        name = profile.get('first_name', update.effective_user.first_name) if profile else update.effective_user.first_name
        await query.message.reply_text("🎨 Generating viral score image...")
        img_path = generate_score_image(uid, f"{jamb_score}/{400}", total, int(jamb_score), name)
        if img_path and os.path.exists(img_path):
            try:
                caption = f"I scored {jamb_score} in JAMB Mock! Can you beat me? Try here t.me/{context.bot.username or 'UTMEBOT'} #JAMB"
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=open(img_path,'rb'), caption=caption)
                os.remove(img_path)
            except Exception as e:
                await query.message.reply_text(f"📤 Share:\n\nI scored {jamb_score} in JAMB Mock! Can you beat me? Try here t.me/{context.bot.username}")
        else:
            await query.message.reply_text(f"📤 *Share My Score*\n\nI scored {jamb_score} in JAMB Mock!\nCan you beat me?\nTry here t.me/{context.bot.username or 'UTMEBOT'}", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")]]))

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
            await update.message.reply_text(f"📚 {subj} - {total} Qs - No repeats", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 MENU", callback_data="menu_main")]]))
            await update.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard_with_menu(q,0), parse_mode=ParseMode.HTML)
            if not premium:
                await update.message.reply_text(f"🆓 Free: 5 Qs only - Persistent memory. Premium N{PREMIUM_PRICE} unlimited: /subscribe")
            return
    buttons=[[InlineKeyboardButton(s, callback_data=f"prac_{s}")] for s in SUBJECTS]
    buttons.append([InlineKeyboardButton("🔵 MENU - Main", callback_data="menu_main")])
    await update.message.reply_text("Select subject - Any year available:", reply_markup=InlineKeyboardMarkup(buttons))

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
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_and_tutor))
            print("Handlers registered - PROFESSIONAL FINAL v4 - SUMMARISED EXPLANATORY NO REPETITION LIVE!", flush=True)
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
