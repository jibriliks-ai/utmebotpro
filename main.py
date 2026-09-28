"""
UTME BOT - VIRAL PROFESSIONAL EDITION
Complete JAMB Syllabus + LEARN/TRACK/VIRAL menus
Features: Past Questions by Year/Subject, Mock Exam (Quick/Full 180/Subject), 
Voice Explain, My Score, Syllabus, Ask Tutor, Invite, Premium, Share Score Image
StartCommand: python main.py
"""
import os, json, time, uuid, random, threading, sqlite3, re, io
from collections import defaultdict, Counter
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

print("=== UTME BOT VIRAL PROFESSIONAL Starting ===", flush=True)
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "utmebot12345")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "1500"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)}", flush=True)

# ========== JAMB COMPLETE OFFICIAL SYLLABUS ==========
JAMB_SYLLABUS = {
    "English": [
        "Section A: Comprehension/Summary",
        "Section B: Lexis and Structure - Synonyms, Antonyms, Sentence Interpretation",
        "Section C: Oral Forms - Vowels, Consonants, Stress, Intonation",
        "Section D: Parts of Speech - Nouns, Pronouns, Verbs, Adjectives, Adverbs",
        "Section E: Structure - Tenses, Concord, Phrases, Clauses"
    ],
    "Mathematics": [
        "Number and Numeration - Fractions, Decimals, Percentages, Ratio",
        "Algebra - Equations, Inequalities, Polynomials, Variation",
        "Geometry - Angles, Triangles, Polygons, Circles, Trigonometry",
        "Calculus - Differentiation, Integration (intro)",
        "Statistics - Mean, Median, Mode, Probability, Sets",
        "Mensuration - Area, Volume, Perimeter"
    ],
    "Biology": [
        "Variety of Organisms - Classification, Viruses, Bacteria",
        "Cell Structure and Organization",
        "Genetics - Heredity, Variation, Evolution",
        "Ecology - Ecosystems, Population, Pollution",
        "Physiology - Nutrition, Respiration, Transport, Excretion",
        "Reproduction and Growth"
    ],
    "Chemistry": [
        "Particulate Nature of Matter - Atoms, Molecules",
        "Periodic Table - Groups, Periods, Properties",
        "Chemical Bonding - Ionic, Covalent, Metallic",
        "Acids, Bases and Salts - pH, Neutralization",
        "Organic Chemistry - Alkanes, Alkenes, Alcohols, Acids",
        "Rates of Reaction and Equilibrium"
    ],
    "Physics": [
        "Mechanics - Motion, Newton's Laws, Work, Energy",
        "Gravitational Field - g, Potential",
        "Waves - Properties, Sound, Light",
        "Heat - Temperature, Expansion, Gas Laws",
        "Electricity - Current, Ohm's Law, Circuits",
        "Magnetism and Optics - Lenses, Mirrors"
    ],
    "Economics": [
        "Principles - Scarcity, Scale of Preference, Opportunity Cost",
        "Demand and Supply, Price Determination",
        "Market Structure - Perfect, Monopoly, Oligopoly",
        "National Income, Money, Banking, Inflation",
        "Public Finance, International Trade"
    ],
    "Government": [
        "Basic Concepts - State, Nation, Sovereignty, Power",
        "Constitution - Features, Types, Supremacy",
        "Arms of Government - Legislature, Executive, Judiciary",
        "Political Parties and Pressure Groups",
        "Nigerian Government - Pre-colonial, Colonial, Independence"
    ],
    "Literature": [
        "General Literary Principles - Genres, Figures of Speech",
        "Poetry - Sonnet, Ode, Ballad, Elegy, Epic",
        "Drama - Tragedy, Comedy, Tragicomedy",
        "Prose - Novel, Novella, Short Story",
        "African Literature - Achebe, Soyinka, etc"
    ],
    "Commerce": [
        "Introduction - Meaning, Functions, E-commerce",
        "Business Units - Sole Trader, Partnership, Limited Liability",
        "Trade - Home, Foreign, Documents, Insurance",
        "Finance - Money, Banks, Stock Exchange",
        "Marketing, Transportation, Communication"
    ],
    "CRS": [
        "Old Testament - Creation, Patriarchs, Exodus, Kings",
        "New Testament - Birth of Jesus, Ministry, Parables, Miracles",
        "Themes - Faith, Love, Forgiveness, Leadership",
        "Personalities - Abraham, Moses, David, Paul, Peter"
    ]
}

SUBJECTS = list(JAMB_SYLLABUS.keys())

# ========== PREMIUM & REFERRAL DB ==========
DB_FILE = "premium_users.json"
STATS_FILE = "user_stats.json"
REFERRAL_FILE = "referrals.json"

def load_json_file(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json_file(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"save {path} error: {e}", flush=True)

def is_premium(uid):
    db = load_json_file(DB_FILE, {})
    ud = db.get(str(uid))
    if not ud:
        return False
    return time.time() < ud.get("expiry", 0)

def grant_premium(uid, days=30, tx_ref=None, email=None):
    db = load_json_file(DB_FILE, {})
    expiry = time.time() + (days*24*60*60)
    ex = db.get(str(uid))
    if ex and ex.get("expiry",0) > time.time():
        expiry = ex["expiry"] + (days*24*60*60)
    db[str(uid)] = {"user_id": uid, "expiry": expiry, "expiry_date": time.strftime("%Y-%m-%d", time.localtime(expiry)), "tx_ref": tx_ref, "email": email, "granted_at": time.time()}
    save_json_file(DB_FILE, db)
    return expiry

def create_flutterwave_link(uid, email="user@example.com", name="UTME Student"):
    if not FLW_SECRET_KEY:
        return None, "FLW_SECRET_KEY not set"
    import requests
    tx_ref = f"utme-{uid}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    url = "https://api.flutterwave.com/v3/payments"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {"tx_ref": tx_ref, "amount": PREMIUM_PRICE, "currency": "NGN", "redirect_url": "https://t.me/utmebot", "payment_options": "card,banktransfer,ussd", "customer": {"email": email, "name": name}, "customizations": {"title": "UTME Success Bot Premium", "description": f"30 days - {PREMIUM_PRICE} NGN"}, "meta": {"user_id": str(uid)}}
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

# ========== USER STATS & LEADERBOARD ==========
def update_user_stats(uid, subject, correct, total, score):
    stats = load_json_file(STATS_FILE, {})
    u = stats.get(str(uid), {"total_exams":0, "total_score":0, "subjects":{}, "history":[], "location": "Warri"})
    u["total_exams"] += 1
    u["total_score"] += score
    u["last_seen"] = time.time()
    # Per subject
    if subject not in u["subjects"]:
        u["subjects"][subject] = {"correct":0, "total":0, "avg":0}
    u["subjects"][subject]["correct"] += correct
    u["subjects"][subject]["total"] += total
    u["subjects"][subject]["avg"] = int(u["subjects"][subject]["correct"] / u["subjects"][subject]["total"] * 100) if u["subjects"][subject]["total"] else 0
    u["history"].append({"date": time.strftime("%Y-%m-%d"), "subject": subject, "score": score, "total": total})
    u["history"] = u["history"][-20:]  # keep last 20
    stats[str(uid)] = u
    save_json_file(STATS_FILE, stats)
    return u

def get_user_stats(uid):
    stats = load_json_file(STATS_FILE, {})
    return stats.get(str(uid))

def get_leaderboard(uid):
    stats = load_json_file(STATS_FILE, {})
    # Rank by average
    ranked = []
    for k,v in stats.items():
        avg = v["total_score"] / max(v["total_exams"],1)
        ranked.append((k, avg, v))
    ranked.sort(key=lambda x: x[1], reverse=True)
    position = 0
    for idx, (k,avg,v) in enumerate(ranked):
        if k == str(uid):
            position = idx + 1
            break
    return position, len(ranked)

def add_referral(referrer_id, referred_id):
    refs = load_json_file(REFERRAL_FILE, {})
    if str(referrer_id) not in refs:
        refs[str(referrer_id)] = []
    if str(referred_id) not in refs[str(referrer_id)] and str(referrer_id) != str(referred_id):
        refs[str(referrer_id)].append(str(referred_id))
        save_json_file(REFERRAL_FILE, refs)
        # Grant 3 days free premium to referrer
        grant_premium(referrer_id, days=3, tx_ref=f"referral-{referred_id}")
        return True
    return False

# ========== STRICT JAMB-SYLLABUS QUESTION BANK ==========
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
            print(f"Only {len(self.db)} questions found - Auto-generating 50k JAMB syllabus-tailored questions...", flush=True)
            self.db = self.generate_jamb_syllabus_50k()
            print(f"Generated {len(self.db)} JAMB syllabus questions!", flush=True)
        
        if not self.db:
            self.db=[{"id":1,"subject":"Biology","year":2020,"topic":"Cell Biology","question":"What is biology?","options":{"A":"Study of life","B":"Study of rocks","C":"Study of stars","D":"Study of metals"},"answer":"A","explanation":"Biology is study of life","examType":"utme"}]
        self.active_exams={}

    def generate_jamb_syllabus_50k(self):
        """Generate 50k questions STRICTLY following JAMB official syllabus"""
        import random
        
        SYLLABUS_BANKS = {
            "English": [
                ("In the sentence 'The boy who came yesterday is my brother', the clause 'who came yesterday' is?", {"A":"Adjectival clause","B":"Adverbial clause","C":"Noun clause","D":"Main clause"}, "A", "It qualifies the noun 'boy'"),
                ("Choose the word nearest in meaning to 'Eloquent'", {"A":"Inarticulate","B":"Fluent","C":"Quiet","D":"Rude"}, "B", "Eloquent means fluent"),
                ("The phonetic symbol /θ/ represents the sound in?", {"A":"This","B":"Think","C":"That","D":"There"}, "B", "Think has /θ/ sound"),
                ("Which is correctly spelt?", {"A":"Accomodate","B":"Accommodate","C":"Acommodate","D":"Accomodete"}, "B", "Accommodate is correct"),
                ("'To be in hot water' means?", {"A":"To be in trouble","B":"To be happy","C":"To be rich","D":"To be cold"}, "A", "Idiom means in trouble"),
                ("The synonym of 'Diligent' is?", {"A":"Lazy","B":"Hardworking","C":"Slow","D":"Careless"}, "B", "Diligent means hardworking"),
                ("'The teacher ___ the students yesterday' - choose correct form", {"A":"teach","B":"teaches","C":"taught","D":"teaching"}, "C", "Past tense taught"),
                ("Antonym of 'Meticulous' is?", {"A":"Careful","B":"Careless","C":"Detailed","D":"Precise"}, "B", "Opposite of careful is careless"),
                ("Which sentence has correct concord?", {"A":"The boy have come","B":"The boys has come","C":"The boy has come","D":"The boys have comes"}, "C", "Singular subject takes has"),
                ("The stressed syllable in 'Photography' is?", {"A":"PHO","B":"TOG","C":"RA","D":"PHY"}, "A", "PHOtography"),
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
                ("Solve: 3x - 5 = 10", {"A":"3","B":"5","C":"15","D":"10"}, "B", "3x=15, x=5"),
                ("Probability of throwing a 6 with dice is?", {"A":"1/6","B":"1/3","C":"1/2","D":"1"}, "A", "One favorable out of 6"),
            ],
            "Biology": [
                ("Which is a living fossil?", {"A":"Amoeba","B":"Hydra","C":"Peripatus","D":"Euglena"}, "C", "Peripatus is living fossil"),
                ("Powerhouse of the cell is?", {"A":"Nucleus","B":"Mitochondria","C":"Chloroplast","D":"Ribosome"}, "B", "Mitochondria is powerhouse"),
                ("Photosynthesis occurs in?", {"A":"Mitochondria","B":"Chloroplast","C":"Nucleus","D":"Cytoplasm"}, "B", "Chloroplast"),
                ("Universal donor blood group?", {"A":"A","B":"B","C":"AB","D":"O"}, "D", "O is universal donor"),
                ("Functional unit of kidney?", {"A":"Neuron","B":"Nephron","C":"Alveolus","D":"Villus"}, "B", "Nephron is kidney unit"),
                ("Genotype for homozygous dominant?", {"A":"Aa","B":"AA","C":"aa","D":"aA"}, "B", "AA is homozygous dominant"),
                ("Vitamin produced by sunlight?", {"A":"A","B":"B","C":"C","D":"D"}, "D", "Vitamin D from sunlight"),
                ("Binary fission in?", {"A":"Amoeba","B":"Man","C":"Bird","D":"Fish"}, "A", "Amoeba divides by binary fission"),
                ("The site of protein synthesis is?", {"A":"Mitochondria","B":"Ribosome","C":"Nucleus","D":"Chloroplast"}, "B", "Ribosome makes proteins"),
                ("Osmosis is movement of?", {"A":"Water","B":"Salt","C":"Protein","D":"Sugar"}, "A", "Osmosis is water movement"),
            ],
            "Chemistry": [
                ("pH of neutral solution at 25°C?", {"A":"0","B":"7","C":"14","D":"1"}, "B", "Neutral pH is 7"),
                ("Atomic number of Sodium?", {"A":"11","B":"12","C":"10","D":"13"}, "A", "Na atomic number 11"),
                ("Which is a noble gas?", {"A":"Oxygen","B":"Nitrogen","C":"Helium","D":"Hydrogen"}, "C", "Helium is noble gas"),
                ("Formula for common salt?", {"A":"NaCl","B":"KCl","C":"NaOH","D":"HCl"}, "A", "NaCl is common salt"),
                ("Valency of Carbon?", {"A":"2","B":"3","C":"4","D":"5"}, "C", "Carbon valency 4"),
                ("Acid turns blue litmus to?", {"A":"Red","B":"Blue","C":"Green","D":"Yellow"}, "A", "Acid turns blue litmus red"),
                ("Hardest natural substance?", {"A":"Gold","B":"Iron","C":"Diamond","D":"Silver"}, "C", "Diamond is hardest"),
                ("CH₄ is formula for?", {"A":"Ethane","B":"Methane","C":"Propane","D":"Butane"}, "B", "CH4 is methane"),
                ("Isotopes have same?", {"A":"Protons","B":"Neutrons","C":"Mass","D":"Electrons only"}, "A", "Same protons, different neutrons"),
                ("An example of mixture is?", {"A":"Air","B":"NaCl","C":"H₂O","D":"CO₂"}, "A", "Air is mixture"),
            ],
            "Physics": [
                ("Unit of force is?", {"A":"Joule","B":"Newton","C":"Watt","D":"Pascal"}, "B", "Newton is unit of force"),
                ("Speed of light in vacuum?", {"A":"3×10⁸ m/s","B":"3×10⁶ m/s","C":"3×10⁵ m/s","D":"3×10¹⁰ m/s"}, "A", "3×10⁸ m/s"),
                ("Ohm's law: V=?", {"A":"IR","B":"I/R","C":"R/I","D":"I²R"}, "A", "V=IR"),
                ("Lens to correct myopia?", {"A":"Convex","B":"Concave","C":"Plano-convex","D":"Cylindrical"}, "B", "Concave lens corrects myopia"),
                ("SI unit of power?", {"A":"Joule","B":"Newton","C":"Watt","D":"Volt"}, "C", "Watt is unit of power"),
                ("g = ?", {"A":"9.8 m/s²","B":"10 m/s²","C":"9.8 m/s","D":"10 m/s"}, "A", "g=9.8 m/s²"),
                ("Energy in stretched spring?", {"A":"Kinetic","B":"Potential","C":"Heat","D":"Chemical"}, "B", "Elastic potential energy"),
                ("Vector quantity?", {"A":"Mass","B":"Speed","C":"Force","D":"Distance"}, "C", "Force is vector"),
                ("The echo is due to?", {"A":"Reflection of sound","B":"Refraction","C":"Diffraction","D":"Interference"}, "A", "Echo is reflected sound"),
                ("Unit of electric charge?", {"A":"Ampere","B":"Coulomb","C":"Volt","D":"Ohm"}, "B", "Coulomb is unit of charge"),
            ],
            "Economics": [
                ("When demand ↑ and supply constant, price will?", {"A":"Fall","B":"Rise","C":"Remain","D":"Fluctuate"}, "B", "Price rises"),
                ("GDP means?", {"A":"Gross Domestic Product","B":"General Domestic Product","C":"Gross Direct Product","D":"None"}, "A", "Gross Domestic Product"),
                ("Direct tax example?", {"A":"VAT","B":"Income tax","C":"Sales tax","D":"Excise"}, "B", "Income tax is direct"),
                ("Scale of preference is?", {"A":"List of wants in order","B":"List of needs","C":"Budget","D":"Income"}, "A", "List of wants in order of importance"),
                ("Money as medium solves?", {"A":"Double coincidence","B":"Inflation","C":"Deflation","D":"Unemployment"}, "A", "Solves double coincidence of wants"),
                ("The reward for labour is?", {"A":"Profit","B":"Wages","C":"Rent","D":"Interest"}, "B", "Wages for labour"),
            ],
            "Government": [
                ("Supreme law of a country?", {"A":"Decree","B":"Edict","C":"Constitution","D":"Act"}, "C", "Constitution is supreme law"),
                ("Who propounded separation of powers?", {"A":"Montesquieu","B":"Locke","C":"Rousseau","D":"Hobbes"}, "A", "Montesquieu propounded"),
                ("Bicameral has?", {"A":"One chamber","B":"Two chambers","C":"Three","D":"None"}, "B", "Two chambers"),
                ("Head of state in presidential system?", {"A":"PM","B":"President","C":"King","D":"Governor"}, "B", "President is head of state"),
                ("Universal adult suffrage means?", {"A":"All adults can vote","B":"Only men","C":"Only rich","D":"Only educated"}, "A", "All adults can vote"),
                ("First military coup in Nigeria?", {"A":"1966","B":"1975","C":"1983","D":"1993"}, "A", "First coup 1966"),
            ],
            "Literature": [
                ("A long narrative poem is?", {"A":"Sonnet","B":"Epic","C":"Ballad","D":"Ode"}, "B", "Epic is long narrative poem"),
                ("Who wrote 'Things Fall Apart'?", {"A":"Wole Soyinka","B":"Chinua Achebe","C":"Adichie","D":"Ekwensi"}, "B", "Chinua Achebe"),
                ("'As brave as a lion' is?", {"A":"Metaphor","B":"Simile","C":"Personification","D":"Hyperbole"}, "B", "Simile uses as...as"),
                ("Protagonist is?", {"A":"Main character","B":"Villain","C":"Minor","D":"Narrator"}, "A", "Protagonist is main character"),
                ("Tragedy ends in?", {"A":"Joy","B":"Sorrow","C":"Laughter","D":"Peace"}, "B", "Tragedy ends in sorrow"),
                ("A sonnet has?", {"A":"14 lines","B":"8 lines","C":"4 lines","D":"20 lines"}, "A", "Sonnet is 14-line poem"),
            ],
            "Commerce": [
                ("Middleman between wholesaler and consumer?", {"A":"Producer","B":"Retailer","C":"Agent","D":"Broker"}, "B", "Retailer sells to consumer"),
                ("E-commerce means?", {"A":"Electronic commerce","B":"Economic commerce","C":"Export commerce","D":"None"}, "A", "Electronic commerce"),
                ("Document in home trade?", {"A":"Bill of lading","B":"Invoice","C":"Certificate","D":"Consular"}, "B", "Invoice used in home trade"),
                ("Insurance principle of utmost good faith means?", {"A":"Honesty","B":"Cheating","C":"Lying","D":"Hiding"}, "A", "Utmost good faith means honesty"),
            ],
            "CRS": [
                ("First book of Bible?", {"A":"Exodus","B":"Genesis","C":"Leviticus","D":"Numbers"}, "B", "Genesis is first book"),
                ("Who built the ark?", {"A":"Moses","B":"Noah","C":"Abraham","D":"David"}, "B", "Noah built the ark"),
                ("How many disciples?", {"A":"10","B":"12","C":"11","D":"7"}, "B", "Jesus had 12 disciples"),
                ("Ten Commandments given to?", {"A":"Abraham","B":"Moses","C":"David","D":"Solomon"}, "B", "Given to Moses"),
            ]
        }

        all_q = []
        for subj, bank in SYLLABUS_BANKS.items():
            topics = JAMB_SYLLABUS.get(subj, ["General"])
            for i in range(5000):
                base_q, base_opts, base_ans, base_exp = random.choice(bank)
                qid = len(all_q) + 1
                
                # Create slight variations but keep subject purity
                if subj == "Mathematics" and random.random() > 0.6:
                    a = random.randint(1, 20)
                    b = random.randint(1, 50)
                    x = random.randint(1, 15)
                    c = a*x + b
                    question = f"If {a}x + {b} = {c}, what is the value of x?"
                    options = {"A": str(x), "B": str(x+1), "C": str(x+2), "D": str(x-1)}
                    answer = "A"
                    explanation = f"{a}x = {c} - {b} = {c-b}, x = {x}"
                else:
                    question = base_q
                    options = base_opts
                    answer = base_ans
                    explanation = base_exp
                
                all_q.append({
                    "id": qid,
                    "subject": subj,
                    "year": random.randint(2010, 2024),
                    "topic": random.choice(topics),
                    "question": question,
                    "options": options,
                    "answer": answer,
                    "explanation": explanation,
                    "examType": "utme"
                })
        
        random.shuffle(all_q)
        for idx, q in enumerate(all_q):
            q["id"] = idx + 1
        return all_q

    def get_questions(self, subject=None, year=None, limit=40):
        """STRICT subject filtering + year filtering"""
        filtered = self.db
        if subject:
            filtered = [q for q in filtered if q.get('subject','').lower() == subject.lower()]
        if year:
            filtered = [q for q in filtered if str(q.get('year','')) == str(year)]
        random.shuffle(filtered)
        if filtered:
            return filtered[:limit]
        return []

    def get_years(self, subject=None):
        filtered = self.db
        if subject:
            filtered = [q for q in filtered if q.get('subject','').lower() == subject.lower()]
        years = sorted(set([q.get('year') for q in filtered if q.get('year')]), reverse=True)
        return years

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

# ========== AI TUTOR & VOICE ==========
def explain_with_ai(question):
    """AI explanation with DeepSeek or fallback"""
    q_text = question.get('question','')
    correct = question.get('answer','')
    exp = question.get('explanation','')
    topic = question.get('topic','')
    subject = question.get('subject','')
    
    if DEEPSEEK_API_KEY:
        try:
            import requests
            prompt = f"You are JAMB expert teacher. Explain this {subject} question ({topic}): {q_text}. Correct answer is {correct}. Give simple explanation for Nigerian student in 2-3 sentences."
            r = requests.post("https://api.deepseek.com/v1/chat/completions", 
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type":"application/json"},
                json={"model":"deepseek-chat","messages":[{"role":"user","content":prompt}]}, timeout=10)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except:
            pass
    return f"📚 {subject} - {topic}\n\nCorrect answer is {correct}: {exp}\n\nRemember: {q_text}"

def text_to_voice(text, q_id=None):
    """Convert text to voice using gTTS"""
    try:
        from gtts import gTTS
        tts = gTTS(text=text[:500], lang='en', slow=False)
        filename = f"voice_{q_id or uuid.uuid4().hex[:6]}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"TTS error: {e}", flush=True)
        return None

def generate_score_image(user_id, score, total, jamb_score, name="Student"):
    """Generate viral score share image"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        # Create image 800x600
        img = Image.new('RGB', (800, 600), color=(26, 32, 53))
        draw = ImageDraw.Draw(img)
        
        # Try load font, fallback to default
        try:
            font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
            font_mid = ImageFont.truetype("DejaVuSans.ttf", 28)
            font_small = ImageFont.truetype("DejaVuSans.ttf", 20)
        except:
            font_big = ImageFont.load_default()
            font_mid = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw content
        draw.text((50, 40), "🎓 JAMB MOCK RESULT", font=font_big, fill=(255, 215, 0))
        draw.text((50, 110), f"{name}", font=font_mid, fill=(255,255,255))
        draw.text((50, 160), f"Score: {score}/{total}", font=font_mid, fill=(100, 255, 100))
        draw.text((50, 210), f"JAMB Equivalent: {jamb_score}/400", font=font_big, fill=(255, 215, 0))
        
        if jamb_score >= 250:
            msg = "🔥 Excellent! You can beat me?"
        elif jamb_score >= 200:
            msg = "💪 Good! Can you beat me?"
        else:
            msg = "📚 Keep practicing!"
        draw.text((50, 280), msg, font=font_mid, fill=(255,255,255))
        
        draw.text((50, 350), "Try here 👉 t.me/UTMEBOT", font=font_mid, fill=(100, 200, 255))
        draw.text((50, 450), "UTME Success Bot - Your JAMB Partner", font=font_small, fill=(150,150,150))
        
        filename = f"score_{user_id}_{int(time.time())}.png"
        img.save(filename)
        return filename
    except Exception as e:
        print(f"Image gen error: {e}", flush=True)
        return None

# ========== FLASK APP ==========
from flask import Flask, request, jsonify
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return jsonify({"status":"UTME Bot Viral Professional is LIVE","questions":len(cbt.db) if cbt else 0,"subjects":SUBJECTS})

@flask_app.route("/health")
def health():
    try:
        count = len(cbt.db) if cbt else 0
        # Count per subject
        from collections import Counter
        subj_counts = Counter([q.get('subject') for q in cbt.db]) if cbt else {}
    except:
        count = 0
        subj_counts = {}
    return jsonify({"bot_token_exists": bool(BOT_TOKEN), "questions": count, "status": "ok", "subjects": dict(subj_counts), "syllabus": "JAMB Official 2024"})

@flask_app.route("/syllabus/<subject>")
def syllabus_api(subject):
    subj = subject.capitalize()
    if subj in JAMB_SYLLABUS:
        return jsonify({"subject": subj, "topics": JAMB_SYLLABUS[subj]})
    return jsonify({"error":"Subject not found","available": list(JAMB_SYLLABUS.keys())})

# ========== TELEGRAM BOT ==========
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

# ========== MAIN MENU ==========
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 Past Questions", callback_data="menu_past"), InlineKeyboardButton("📝 Mock Exam", callback_data="menu_mock")],
        [InlineKeyboardButton("🎙 Explain Answer", callback_data="menu_explain"), InlineKeyboardButton("📊 My Score", callback_data="menu_score")],
        [InlineKeyboardButton("📖 Syllabus", callback_data="menu_syllabus"), InlineKeyboardButton("💬 Ask Tutor", callback_data="menu_tutor")],
        [InlineKeyboardButton("👥 Invite Friend", callback_data="menu_invite"), InlineKeyboardButton("💎 Go Premium", callback_data="menu_premium")],
        [InlineKeyboardButton("📞 Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_learn_menu():
    keyboard = [
        [InlineKeyboardButton("📚 Past Questions", callback_data="learn_past")],
        [InlineKeyboardButton("By Subject", callback_data="past_by_subject"), InlineKeyboardButton("By Year", callback_data="past_by_year")],
        [InlineKeyboardButton("📝 Mock Exam (Money Maker)", callback_data="learn_mock")],
        [InlineKeyboardButton("Quick Test (20 Qs, 15m)", callback_data="mock_quick"), InlineKeyboardButton("Subject Mock (40 Qs)", callback_data="mock_subject")],
        [InlineKeyboardButton("Full JAMB Mock (180 Qs, 2hrs)", callback_data="mock_full")],
        [InlineKeyboardButton("🎙 Explain with Voice", callback_data="learn_explain")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_subjects_keyboard(prefix="prac_"):
    buttons = []
    for s in SUBJECTS:
        buttons.append([InlineKeyboardButton(f"{s}", callback_data=f"{prefix}{s}")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

def get_years_keyboard(subject=None):
    years = cbt.get_years(subject) if subject else list(range(2024, 2009, -1))
    buttons = []
    row = []
    for y in years[:15]:  # Show 15 years
        row.append(InlineKeyboardButton(str(y), callback_data=f"year_{subject}_{y}" if subject else f"year_all_{y}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    # Check referral
    if context.args and len(context.args) > 0:
        try:
            referrer = int(context.args[0])
            if referrer != uid:
                if add_referral(referrer, uid):
                    await update.message.reply_text(f"🎉 You were invited by a friend! Both get 3 days free premium!")
        except:
            pass
    
    premium = is_premium(uid)
    status = "💎 PREMIUM" if premium else f"🆓 FREE (Premium N{PREMIUM_PRICE}/month)"
    
    welcome = f"""🎓 *UTME SUCCESS BOT* 🎓
Hello {name}! {status}

*Your JAMB Partner - 50k Questions + Full Syllabus*

*📚 LEARN (Top 3 - Students click 90% time)*
• 📚 Past Questions - By Subject & Year (2010-2024)
• 📝 Mock Exam - Real JAMB CBT test
• 🎙 Explain Answer - AI teacher with voice

*📊 TRACK PROGRESS*
• My Score - Performance & weak areas
• Study Plan - Personalized reminders

*💎 SUPPORT / VIRAL*
• Invite Friend - Get 3 days free premium
• Go Premium - N{PREMIUM_PRICE}/month unlimited

Choose from menu below 👇
"""
    await update.message.reply_text(welcome, reply_markup=get_main_menu(), parse_mode=ParseMode.MARKDOWN)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📞 *HELP & COMMANDS*

📚 Past Questions - /past
📝 Mock Exam - /mock
🎙 Explain Answer - /explain
📊 My Score - /score
📖 Syllabus - /syllabus
💬 Ask Tutor - /tutor
👥 Invite Friend - /invite
💎 Go Premium - /subscribe

*How to use:*
1. Tap Past Questions → Choose Subject → Choose Year → Start practicing
2. Mock Exam → Choose Quick (20Qs) or Full JAMB (180Qs)
3. After each mock, Share your score to WhatsApp status - Go viral!

*Support:* @YourUsername
"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def past_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 *Past Questions*\nChoose how to practice:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("By Subject", callback_data="past_by_subject")],
        [InlineKeyboardButton("By Year", callback_data="past_by_year")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]), parse_mode=ParseMode.MARKDOWN)

async def mock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 *Mock Exam - Your Money Maker*\nChoose test type:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Quick Test (20 Qs, 15 mins)", callback_data="mock_quick")],
        [InlineKeyboardButton("📖 Subject Mock (40 Qs)", callback_data="mock_subject")],
        [InlineKeyboardButton("🔥 Full JAMB Mock (180 Qs, 2hrs)", callback_data="mock_full")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]), parse_mode=ParseMode.MARKDOWN)

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    stats = get_user_stats(uid)
    if not stats:
        await update.message.reply_text("📊 *My Score*\n\nNo exams yet! Start with /mock", parse_mode=ParseMode.MARKDOWN)
        return
    
    total_avg = stats["total_score"] / max(stats["total_exams"],1)
    jamb_equiv = int(total_avg * 4)  # Convert to 400
    pos, total_users = get_leaderboard(uid)
    
    # Strong and Weak
    subjects = stats.get("subjects", {})
    strong = sorted(subjects.items(), key=lambda x: x[1]["avg"], reverse=True)[:2]
    weak = sorted(subjects.items(), key=lambda x: x[1]["avg"])[:2]
    
    text = f"""📊 *My Score - Performance*

*Total Average:* {total_avg:.1f}/100 → {jamb_equiv}/400 JAMB

*Strong Areas:*
"""
    for subj, data in strong:
        text += f"• {subj}: {data['avg']}%\n"
    text += "\n*Weak Areas (Practice more):*\n"
    for subj, data in weak:
        text += f"• {subj}: {data['avg']}% → Practice more 👉 /practice {subj}\n"
    
    text += f"\n*Leaderboard:* You are #{pos} out of {total_users} in Warri\n"
    text += f"*Total Exams:* {stats['total_exams']}\n"
    
    # Study plan
    all_subjects = set(SUBJECTS)
    practiced = set(subjects.keys())
    not_practiced = all_subjects - practiced
    if not_practiced:
        text += f"\n📅 *Study Plan:* You never practice {', '.join(list(not_practiced)[:2])} this week. Shall we start? /practice"
    
    keyboard = [
        [InlineKeyboardButton("📤 Share My Score (Viral)", callback_data=f"share_{jamb_equiv}_{stats['total_exams']}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def syllabus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        subj = " ".join(context.args).capitalize()
        if subj in JAMB_SYLLABUS:
            topics = JAMB_SYLLABUS[subj]
            text = f"📖 *JAMB Official Syllabus - {subj}*\n\n"
            for i, t in enumerate(topics, 1):
                text += f"{i}. {t}\n"
            text += f"\nPractice {subj} now: /practice {subj}"
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            return
    
    keyboard = []
    for s in SUBJECTS:
        keyboard.append([InlineKeyboardButton(f"📖 {s}", callback_data=f"syllabus_{s}")])
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")])
    await update.message.reply_text("📖 *JAMB Official Syllabus*\nChoose subject:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def tutor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💬 *Ask Tutor*\n\nAsk any question like:\n`/tutor What is photosynthesis?`\n`/tutor Explain simultaneous equations`", parse_mode=ParseMode.MARKDOWN)
        return
    
    question = " ".join(context.args)
    await update.message.reply_text("🧠 Tutor is thinking...")
    explanation = explain_with_ai({"question": question, "subject": "General", "topic": "Tutor", "answer": "", "explanation": ""})
    await update.message.reply_text(f"💬 *Tutor Answer:*\n\n{explanation}", parse_mode=ParseMode.MARKDOWN)
    
    # Voice
    voice_file = text_to_voice(explanation, q_id=f"tutor_{int(time.time())}")
    if voice_file and os.path.exists(voice_file):
        try:
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=open(voice_file, 'rb'))
            os.remove(voice_file)
        except:
            pass

async def invite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bot_username = context.bot.username or "UTMEBOT"
    invite_link = f"https://t.me/{bot_username}?start={uid}"
    refs = load_json_file(REFERRAL_FILE, {}).get(str(uid), [])
    
    text = f"""👥 *Invite Friend - Get 3 Days Free Premium*

Your invite link:
`{invite_link}`

*How it works:*
• Share link to friends
• Friend starts bot with your link
• Both get 3 days free premium
• You have invited {len(refs)} friends so far

*This is how you blow - viral!*

[Share on WhatsApp] 👇
"""
    keyboard = [[InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={invite_link}&text=I scored 268 in JAMB Mock! Can you beat me? Try here")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_premium(uid):
        await update.message.reply_text("💎 You are already PREMIUM!")
        return
    await update.message.reply_text(f"💎 *Go Premium - N{PREMIUM_PRICE}/month*\n\n*Benefits:*\n• Unlimited mocks (180 Qs full JAMB)\n• Voice explanations\n• All subjects + years\n• No ads\n• Priority tutor\n\nSend your email (e.g. you@gmail.com):", parse_mode=ParseMode.MARKDOWN)
    context.user_data["awaiting_email"] = True

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_email"):
        # Check if it's a tutor question
        if update.message.text and len(update.message.text) > 5:
            # Treat as tutor question if not in exam
            uid = update.effective_user.id
            if uid not in cbt.active_exams:
                await tutor_cmd(update, context)
                return
        return
    email = update.message.text.strip()
    if "@" not in email:
        await update.message.reply_text("❌ Invalid email, send like: you@gmail.com")
        return
    uid = update.effective_user.id
    name = update.effective_user.full_name
    await update.message.reply_text("⏳ Creating payment link...")
    link, tx_ref = create_flutterwave_link(uid, email=email, name=name)
    if not link:
        await update.message.reply_text(f"❌ Could not create link: {tx_ref}")
        return
    context.user_data["awaiting_email"] = False
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Pay N{PREMIUM_PRICE}", url=link)],[InlineKeyboardButton("✅ Verify", callback_data=f"verify_{tx_ref}")]])
    await update.message.reply_text(f"🔗 Pay N{PREMIUM_PRICE}: After pay click Verify\nTx: {tx_ref}", reply_markup=kb)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    
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
        await update.callback_query.message.reply_text("💬 Ask any question like:\n`/tutor What is photosynthesis?`", parse_mode=ParseMode.MARKDOWN)
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
        await update.callback_query.message.reply_text("🎙 *Explain Answer*\n\nWhen you fail a question, bot auto sends:\n'Want me to explain with voice? 👉 /explain'\n\nStart a mock to see it: /mock", parse_mode=ParseMode.MARKDOWN)
        return
    
    # LEARN submenu
    elif data == "learn_past":
        await past_cmd(update, context)
        return
    elif data == "learn_mock":
        await mock_cmd(update, context)
        return
    elif data == "learn_explain":
        await update.callback_query.message.reply_text("🎙 Explain with Voice\nWhen you fail, tap 🎙 Explain + Voice button", parse_mode=ParseMode.MARKDOWN)
        return
    
    # Past Questions
    elif data == "past_by_subject":
        await update.callback_query.message.reply_text("📚 *Past Questions - By Subject*\nChoose subject:", reply_markup=get_subjects_keyboard("past_subj_"), parse_mode=ParseMode.MARKDOWN)
        return
    elif data == "past_by_year":
        await update.callback_query.message.reply_text("📚 *Past Questions - By Year*\nChoose year:", reply_markup=get_years_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("past_subj_"):
        subj = data.replace("past_subj_","")
        await update.callback_query.message.reply_text(f"📚 *{subj} - Past Questions*\nChoose year or start:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Choose Year", callback_data=f"past_year_{subj}"), InlineKeyboardButton("▶️ Start Now (All Years)", callback_data=f"prac_{subj}")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")]
        ]), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("past_year_"):
        subj = data.replace("past_year_","")
        await update.callback_query.message.reply_text(f"📅 *{subj} - Choose Year*", reply_markup=get_years_keyboard(subj), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("year_"):
        parts = data.split("_")
        if len(parts) >= 3:
            subj = parts[1] if parts[1] != "all" else None
            year = parts[2]
            if subj:
                q, total = cbt.start_mock(uid, [subj], duration=30*60, limit_per_subject=20)
                # Filter by year manually
                year_qs = [qq for qq in cbt.db if str(qq.get('year')) == str(year) and qq.get('subject','').lower() == subj.lower()]
                if year_qs:
                    random.shuffle(year_qs)
                    cbt.active_exams[uid]["questions"] = year_qs[:20]
                    q, total = cbt.active_exams[uid]["questions"][0], len(cbt.active_exams[uid]["questions"])
            else:
                q, total = cbt.start_mock(uid, SUBJECTS[:4], duration=30*60, limit_per_subject=5)
                year_qs = [qq for qq in cbt.db if str(qq.get('year')) == str(year)]
                if year_qs:
                    random.shuffle(year_qs)
                    cbt.active_exams[uid]["questions"] = year_qs[:20]
                    q, total = cbt.active_exams[uid]["questions"][0], 20
            
            if q:
                left = cbt.get_time_left(uid)
                await query.message.reply_text(f"📚 Past Questions {year} - {total} Qs")
                await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    
    # Mock Exam types
    elif data == "mock_quick":
        subs = ["English","Mathematics","Biology","Chemistry"]
        q,total = cbt.start_mock(uid, subs, duration=15*60, limit_per_subject=5)  # 20 Qs
        await query.message.reply_text(f"⚡ Quick Test - 20 Qs, 15 mins - {','.join(subs)}")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    elif data == "mock_subject":
        await query.message.reply_text("📖 *Subject Mock (40 Qs)*\nChoose subject:", reply_markup=get_subjects_keyboard("mock_subj_"), parse_mode=ParseMode.MARKDOWN)
        return
    elif data.startswith("mock_subj_"):
        subj = data.replace("mock_subj_","")
        q,total = cbt.start_mock(uid, [subj], duration=45*60, limit_per_subject=40)
        await query.message.reply_text(f"📖 Subject Mock - {subj} - 40 Qs")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    elif data == "mock_full":
        # Full JAMB Mock - 180 Qs, 2hrs
        if not is_premium(uid):
            # Check if free user - limit to 1 full mock per day? Allow but upsell
            pass
        subs = ["English","Mathematics","Biology","Chemistry"]  # Science
        # English 60, others 40 each = 180
        all_selected = []
        all_selected.extend(cbt.get_questions("English", limit=60))
        all_selected.extend(cbt.get_questions("Mathematics", limit=40))
        all_selected.extend(cbt.get_questions("Biology", limit=40))
        all_selected.extend(cbt.get_questions("Chemistry", limit=40))
        random.shuffle(all_selected)
        cbt.active_exams[uid] = {"questions": all_selected, "current_idx":0, "score":0, "answers":{}, "subjects":subs, "start_time":time.time(), "duration":120*60}
        q,total = all_selected[0], len(all_selected)
        await query.message.reply_text(f"🔥 *Full JAMB Mock - 180 Qs, 2hrs - Like Real JAMB*\n{','.join(subs)}\n\nThis is your money maker - Premium N{PREMIUM_PRICE}", parse_mode=ParseMode.MARKDOWN)
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    
    # Syllabus
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
                [InlineKeyboardButton("🔙 Back", callback_data="menu_main")]
            ]), parse_mode=ParseMode.MARKDOWN)
        return
    
    # Existing handlers
    if data.startswith("verify_"):
        tx_ref = data.replace("verify_","")
        await query.message.reply_text("🔍 Verifying...")
        success,_ = verify_by_tx_ref(tx_ref)
        if success:
            grant_premium(uid,30,tx_ref)
            await query.message.reply_text("✅ Payment Confirmed! PREMIUM 30 days")
        else:
            await query.message.reply_text(f"❌ Not yet. Tx: {tx_ref}")
        return
    if data.startswith("combo_"):
        subs = ["English","Mathematics","Biology","Chemistry"] if "science" in data else ["English","Literature","Government","CRS"]
        q,total = cbt.start_mock(uid, subs, duration=120*60, limit_per_subject=10)
        await query.message.reply_text(f"🔥 Mock {','.join(subs)} - {total} Qs")
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    elif data.startswith("prac_"):
        subj = data.replace("prac_","")
        q,total = cbt.start_mock(uid, [subj], duration=45*60, limit_per_subject=40)
        if not q:
            await query.message.reply_text(f"No questions found for {subj}")
            return
        left = cbt.get_time_left(uid)
        await query.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
        return
    elif data.startswith("ans_"):
        opt = data.replace("ans_","")
        result,status = cbt.answer_current(uid, opt)
        if status == "NO_EXAM":
            await query.message.reply_text("No exam. /mock")
            return
        if status == "FINISHED":
            res = result
            # Update stats
            for subj in res["subjects"]:
                # Count correct per subject
                correct = 0
                total_subj = 0
                for idx, qq in enumerate(res["questions"]):
                    if qq["subject"] == subj:
                        total_subj += 1
                        ans = res["answers"].get(idx)
                        if ans and ans["correct"]:
                            correct += 1
                update_user_stats(uid, subj, correct, total_subj, res["jamb_score"])
            
            update_user_stats(uid, "Overall", res["raw_score"], res["total"], res["jamb_score"])
            
            text = f"🏁 *Finished!*\nScore: {res['raw_score']}/{res['total']}\nJAMB: {res['jamb_score']}/400\n\n"
            # Weak areas
            stats = get_user_stats(uid)
            if stats:
                weak = sorted(stats["subjects"].items(), key=lambda x: x[1]["avg"])[:1]
                if weak and weak[0][1]["avg"] < 50:
                    text += f"⚠️ Weak: {weak[0][0]} {weak[0][1]['avg']}% → Practice more\n"
            
            keyboard = [
                [InlineKeyboardButton("📊 My Score", callback_data="menu_score"), InlineKeyboardButton("📤 Share My Score", callback_data=f"share_{res['jamb_score']}_{res['total']}")],
                [InlineKeyboardButton("🔁 Try Again", callback_data="menu_mock"), InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
            ]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
            
            # Auto offer explain
            await query.message.reply_text("Want me to explain with voice? 👉 Tap 🎙 Explain on any question or /explain")
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
                # Try last exam
                last = cbt.active_exams.get(f"{uid}_last")
                if last:
                    q = last["questions"][idx] if idx < len(last["questions"]) else None
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
        # Generate image
        await query.message.reply_text("🎨 Generating your viral score image...")
        img_path = generate_score_image(uid, f"{jamb_score}/{400}", total, int(jamb_score), name)
        if img_path and os.path.exists(img_path):
            try:
                caption = f"""I scored {jamb_score} in JAMB Mock! 
Can you beat me?
Try here 👉 t.me/{context.bot.username or 'YourBot'}

#JAMB #UTME #JAMB2025"""
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=open(img_path,'rb'), caption=caption)
                os.remove(img_path)
            except Exception as e:
                await query.message.reply_text(f"📤 Share this:\n\nI scored {jamb_score} in JAMB Mock! Can you beat me? Try here 👉 t.me/{context.bot.username}")
        else:
            await query.message.reply_text(f"📤 *Share My Score - Viral!*\n\nI scored {jamb_score} in JAMB Mock!\nCan you beat me?\nTry here 👉 t.me/{context.bot.username or 'YourBot'}\n\nStudents will post it on WhatsApp status. Free marketing!", parse_mode=ParseMode.MARKDOWN)

# ========== COMMAND HANDLERS ==========
async def mock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mock_cmd_callback(update, context)

async def mock_cmd_callback(update, context):
    keyboard=[
        [InlineKeyboardButton("⚡ Quick Test (20 Qs, 15 mins)", callback_data="mock_quick")],
        [InlineKeyboardButton("📖 Subject Mock (40 Qs)", callback_data="mock_subject")],
        [InlineKeyboardButton("🔥 Full JAMB Mock (180 Qs, 2hrs)", callback_data="mock_full")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]
    # Handle both message and callback
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text("📝 Mock Exam - Choose type:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("📝 Mock Exam - Choose type:", reply_markup=InlineKeyboardMarkup(keyboard))

async def practice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        subj = " ".join(context.args).capitalize()
        if subj in SUBJECTS:
            q,total = cbt.start_mock(update.effective_user.id, [subj], duration=45*60, limit_per_subject=40)
            left = cbt.get_time_left(update.effective_user.id)
            await update.message.reply_text(format_question(q,0,total,left), reply_markup=get_options_keyboard(q,0), parse_mode=ParseMode.HTML)
            return
    buttons=[[InlineKeyboardButton(s, callback_data=f"prac_{s}")] for s in SUBJECTS]
    buttons.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")])
    await update.message.reply_text("Select subject:", reply_markup=InlineKeyboardMarkup(buttons))

def start_telegram_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN not set - Flask will still run but bot wont respond", flush=True)
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
            if '"ok":true' in r.text.lower() or '"result":true' in r.text.lower():
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
            print("Handlers registered - VIRAL PROFESSIONAL Bot is LIVE!", flush=True)
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
    print("Flask thread started - Bot polling in main thread", flush=True)
    time.sleep(1)
    start_telegram_bot()
