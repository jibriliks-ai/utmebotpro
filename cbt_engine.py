
"""
cbt_engine.py - v21 PROFESSIONAL - CLEAN CORE DATABANK
- Loads only core subjects: accounting, biology, chemistry, commerce, economics, english, government, literature, mathematics, physics
- Ignores duplicate _1, _2 files
- Always returns questions, never empty
- Includes search_databank for 200% smart tutor
- Includes get_random_question for channel posting
"""
import random, time, requests, os, json
from pathlib import Path

try:
    from config import ALOC_ACCESS_TOKEN, YEARS, ALL_SUBJECTS
except:
    ALOC_ACCESS_TOKEN = os.getenv("ALOC_ACCESS_TOKEN", "")
    YEARS = list(range(2010, 2025))
    ALL_SUBJECTS = ["english","mathematics","biology","physics","chemistry","economics","government","commerce","accounting","literature","crk","geography","civic","history"]

SUBJECT_DISPLAY = {
    "english":"📖 English","mathematics":"📐 Maths","biology":"🧬 Biology","physics":"⚛️ Physics","chemistry":"🧪 Chemistry",
    "economics":"💰 Economics","government":"🏛️ Government","commerce":"🏪 Commerce","accounting":"📊 Accounting",
    "literature":"📚 Literature","crk":"✝️ CRK","geography":"🌍 Geography","civic":"🇳🇬 Civic","history":"📜 History"
}

LOCAL_DATABANK = {}
ALL_QS = []
DATABANK_DIR = Path(__file__).parent / "databank"
CORE_SUBJECTS = ["accounting","biology","chemistry","commerce","economics","english","government","literature","mathematics","physics"]

if DATABANK_DIR.exists():
    for json_file in DATABANK_DIR.glob("*.json"):
        name = json_file.stem
        if name.startswith("all_"):
            continue
        if name not in CORE_SUBJECTS:
            continue
        try:
            data = json.loads(json_file.read_text())
            # Clean duplicates inside
            seen = set()
            clean = []
            for q in data:
                key = q.get("question","")[:80].lower().strip()
                if key and key not in seen:
                    seen.add(key)
                    clean.append(q)
            LOCAL_DATABANK[name] = clean
            print(f"✅ Loaded databank {name}: {len(clean)} Qs")
        except Exception as e:
            print(f"⚠️ Failed {json_file}: {e}")

# Load all_questions.json
all_path = DATABANK_DIR / "all_questions.json"
if all_path.exists():
    try:
        raw = json.loads(all_path.read_text())
        seen_all = set()
        deduped = []
        for q in raw:
            key = q.get("question","")[:80].lower().strip()
            if key and key not in seen_all:
                seen_all.add(key)
                deduped.append(q)
        ALL_QS = deduped
        print(f"✅ Loaded all_questions.json: {len(ALL_QS)} Qs")
    except Exception as e:
        print(f"⚠️ all_questions.json error: {e}")
        ALL_QS = []
        for qs in LOCAL_DATABANK.values():
            ALL_QS.extend(qs)

if not ALL_QS:
    for qs in LOCAL_DATABANK.values():
        ALL_QS.extend(qs)

def get_local_questions(subject, year=None, limit=40):
    subj = subject.lower().strip()
    qs = LOCAL_DATABANK.get(subj, [])
    if not qs:
        qs = [q for q in ALL_QS if q.get("subject_key")==subj]
    if not qs:
        qs = [q for q in ALL_QS if subj in q.get("subject_key","").lower()]
    random.shuffle(qs)
    return qs[:limit]

def search_databank(query, subject=None, limit=5):
    query_lower = query.lower()
    keywords = [w for w in query_lower.split() if len(w)>2][:6]
    if not keywords:
        return []
    pool = ALL_QS
    if subject:
        subj = subject.lower()
        filtered = [q for q in ALL_QS if q.get("subject_key")==subj]
        if filtered:
            pool = filtered
    results = []
    for q in pool:
        q_text = (q.get("question","") + " " + q.get("topic","") + " " + q.get("explanation","")).lower()
        score = 0
        for kw in keywords:
            if kw in q_text:
                score += 2 if kw in q.get("question","").lower() else 1
        if score>0:
            results.append((score,q))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:limit]]

def get_random_question(subject=None):
    pool = ALL_QS
    if subject:
        subj = subject.lower()
        filtered = [q for q in ALL_QS if q.get("subject_key")==subj]
        if filtered:
            pool = filtered
    return random.choice(pool) if pool else None

# Fallback
FALLBACK_QUESTIONS = {
    "english": [
        {"q": "Choose the synonym of 'abundant'?", "a": "Scarce", "b": "Plentiful", "c": "Few", "d": "Rare", "ans": "B", "exp": "Abundant means plentiful"},
        {"q": "What is the antonym of 'brave'?", "a": "Courageous", "b": "Fearless", "c": "Cowardly", "d": "Bold", "ans": "C", "exp": "Opposite of brave is cowardly"},
    ],
    "mathematics": [
        {"q": "Simplify: 2x + 3x - x", "a": "4x", "b": "5x", "c": "6x", "d": "4", "ans": "A", "exp": "2x+3x=5x, 5x-x=4x"},
        {"q": "Solve: 2x + 5 = 15", "a": "5", "b": "10", "c": "7.5", "d": "2", "ans": "A", "exp": "2x=10, x=5"},
    ],
}

def get_fallback(subject, year="2023", limit=40):
    subj = subject.lower()
    base = FALLBACK_QUESTIONS.get(subj, FALLBACK_QUESTIONS["english"] + FALLBACK_QUESTIONS["mathematics"])
    res=[]
    for i in range(limit):
        q=base[i % len(base)]
        res.append({
            "id": f"fb_{subj}_{year}_{i}_{random.randint(1000,9999)}",
            "subject": SUBJECT_DISPLAY.get(subj, subj.title()),
            "subject_key": subj,
            "year": str(year),
            "topic": "General",
            "question": q["q"],
            "option_a": q["a"],
            "option_b": q["b"],
            "option_c": q["c"],
            "option_d": q["d"],
            "answer": q["ans"],
            "explanation": q.get("exp","")
        })
    return res

class ALOCFetcher:
    def __init__(self, token=ALOC_ACCESS_TOKEN):
        self.token=token

    def fetch(self, subject, year=None, limit=40):
        local_qs = get_local_questions(subject, year, limit)
        if local_qs and len(local_qs)>=min(3,limit):
            return local_qs
        local_any = get_local_questions(subject, None, limit)
        if local_any:
            return local_any
        return get_fallback(subject, year or "2023", limit)

fetcher = ALOCFetcher()

def format_question(q, idx, total):
    subj = q.get('subject','JAMB')
    year = q.get('year','')
    topic = q.get('topic','')
    header = f"Q{idx}/{total} | {subj} {year} {('- '+topic) if topic and topic!='General' else ''}".strip()
    return f"{header}\n\n{q.get('question')}\n\nA) {q.get('option_a')}\nB) {q.get('option_b')}\nC) {q.get('option_c')}\nD) {q.get('option_d')}"
