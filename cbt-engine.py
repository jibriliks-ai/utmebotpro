
"""
cbt_engine.py - v19 FINAL - LOCAL DATABANK + ALOC + FALLBACK
- Loads from local databank/ JSON files first (your 960+ converted questions)
- Then tries ALOC live
- Then fallback built-in
- NEVER returns empty
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
ALOC_CODE = {"english":"english","mathematics":"mathematics","biology":"biology","physics":"physics","chemistry":"chemistry","economics":"economics","government":"government","commerce":"commerce","accounting":"accounting","literature":"englishlit","crk":"crk","geography":"geography","civic":"civiledu","history":"history"}

CACHE = {}
CACHE_TIME = {}

# Load local databank
LOCAL_DATABANK = {}
DATABANK_DIR = Path(__file__).parent / "databank"
if DATABANK_DIR.exists():
    for json_file in DATABANK_DIR.glob("*.json"):
        if json_file.name == "all_questions.json":
            continue
        subj = json_file.stem
        try:
            data = json.loads(json_file.read_text())
            LOCAL_DATABANK[subj] = data
            print(f"✅ Loaded local databank {subj}: {len(data)} Qs")
        except Exception as e:
            print(f"⚠️ Failed to load {json_file}: {e}")
else:
    print("⚠️ No databank dir found")

# Also try all_questions.json as fallback
ALL_QS = []
all_path = DATABANK_DIR / "all_questions.json"
if all_path.exists():
    try:
        ALL_QS = json.loads(all_path.read_text())
        print(f"✅ Loaded all_questions.json: {len(ALL_QS)} Qs")
    except:
        pass

def get_local_questions(subject, year=None, limit=40):
    """Get questions from local databank"""
    subj = subject.lower()
    # Map accounting to accounting, literature etc
    # Try exact match
    qs = LOCAL_DATABANK.get(subj, [])
    if not qs and subj == "english":
        # English may be in literature? No
        pass
    # If year provided, filter by year if available
    if year:
        filtered = [q for q in qs if str(q.get("year")) == str(year)]
        if len(filtered) >= limit//2:
            qs = filtered
    # If not enough, supplement from ALL_QS
    if len(qs) < limit:
        # Add from all that match subject
        extra = [q for q in ALL_QS if q.get("subject_key") == subj or q.get("subject","").lower() == subj]
        # Avoid duplicates
        existing_ids = set([q.get("id") for q in qs])
        for q in extra:
            if q.get("id") not in existing_ids:
                qs.append(q)
            if len(qs) >= limit*2:
                break
    random.shuffle(qs)
    return qs[:limit]

# Fallback built-in
FALLBACK_QUESTIONS = {
    "english": [
        {"q": "Synonym of 'abundant'?", "a": "Scarce", "b": "Plentiful", "c": "Few", "d": "Rare", "ans": "B"},
        {"q": "Antonym of 'brave'?", "a": "Courageous", "b": "Fearless", "c": "Cowardly", "d": "Bold", "ans": "C"},
    ],
    "mathematics": [
        {"q": "Simplify: 2x + 3x - x", "a": "4x", "b": "5x", "c": "6x", "d": "4", "ans": "A"},
        {"q": "Solve: 2x + 5 = 15", "a": "5", "b": "10", "c": "7.5", "d": "2", "ans": "A"},
    ],
}

for subj in ALL_SUBJECTS:
    if subj not in FALLBACK_QUESTIONS:
        FALLBACK_QUESTIONS[subj] = FALLBACK_QUESTIONS["english"] + FALLBACK_QUESTIONS["mathematics"]

def get_fallback(subject, year="2023", limit=40):
    import random
    subj = subject.lower()
    base = FALLBACK_QUESTIONS.get(subj, FALLBACK_QUESTIONS["english"])
    res = []
    for i in range(limit):
        q = base[i % len(base)]
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
            "explanation": ""
        })
    return res

class ALOCFetcher:
    def __init__(self, token=ALOC_ACCESS_TOKEN):
        self.token=token
        self.base_v2="https://questions.aloc.com.ng/api/v2"
        self.base_old="https://questions.aloc.ng/api/v2"
        self.session=requests.Session()
        self.session.headers.update({"Accept":"application/json","User-Agent":"UTME-Bot-v19"})
        if token:
            self.session.headers.update({"AccessToken": token, "access-token": token})

    def fetch(self, subject, year, limit=40):
        key=(subject.lower(), str(year), limit)
        if key in CACHE and time.time()-CACHE_TIME.get(key,0)<21600:
            return CACHE[key]
        
        # 1. Try local databank first - YOUR CONVERTED FILES
        local_qs = get_local_questions(subject, year, limit)
        if local_qs and len(local_qs) >= 3:
            print(f"✅ LOCAL DATABANK {subject} {year} -> {len(local_qs)} Qs")
            CACHE[key]=local_qs
            CACHE_TIME[key]=time.time()
            return local_qs
        
        # 2. Try ALOC
        aloc_code=ALOC_CODE.get(subject.lower(), subject.lower())
        urls=[
            f"{self.base_v2}/q/{limit}?subject={aloc_code}&year={year}&type=utme",
            f"{self.base_old}/q/{limit}?subject={aloc_code}&year={year}&type=utme",
        ]
        for url in urls:
            try:
                r=self.session.get(url, timeout=5)
                if r.status_code==200:
                    try:
                        data=r.json()
                        qs=self.parse(data, subject, year)
                        if qs and len(qs)>=3:
                            CACHE[key]=qs
                            CACHE_TIME[key]=time.time()
                            print(f"✅ ALOC {subject} {year} -> {len(qs)}")
                            return qs
                    except:
                        continue
            except:
                continue
        
        # 3. Try local without year filter
        local_any = get_local_questions(subject, None, limit)
        if local_any:
            print(f"✅ LOCAL ANY YEAR {subject} -> {len(local_any)}")
            CACHE[key]=local_any
            CACHE_TIME[key]=time.time()
            return local_any
        
        # 4. Fallback
        print(f"⚠️ FALLBACK {subject} {year} -> {limit} Qs")
        fb = get_fallback(subject, year, limit)
        CACHE[key]=fb
        CACHE_TIME[key]=time.time()
        return fb

    def parse(self, data, subject, year):
        items=[]
        if isinstance(data, dict):
            if isinstance(data.get("data"), list): items=data["data"]
            elif isinstance(data.get("result"), list): items=data["result"]
            elif isinstance(data.get("questions"), list): items=data["questions"]
            elif "question" in data: items=[data]
        elif isinstance(data, list): items=data
        res=[]
        for idx,it in enumerate(items):
            qtext=str(it.get("question","") or it.get("question_text","")).strip()
            if not qtext or len(qtext)<10: continue
            oa=it.get("option_a") or (it.get("option") or {}).get("a") or ""
            ob=it.get("option_b") or (it.get("option") or {}).get("b") or ""
            oc=it.get("option_c") or (it.get("option") or {}).get("c") or ""
            od=it.get("option_d") or (it.get("option") or {}).get("d") or ""
            if isinstance(it.get("options"), list) and len(it["options"])>=4:
                oa,ob,oc,od=it["options"][:4]
            ans=str(it.get("answer","") or it.get("correct_option","")).strip().upper()
            if ans.lower() in ["a","b","c","d"]: ans=ans.upper()
            if ans not in ["A","B","C","D"]: ans="A"
            qid=it.get("id") or f"{subject}_{year}_{idx}_{random.randint(1000,9999)}"
            res.append({
                "id":str(qid),"subject":SUBJECT_DISPLAY.get(subject.lower(),subject.title()),
                "subject_key":subject.lower(),"year":str(it.get("year",year)),
                "topic":it.get("topic","General"),"question":qtext,
                "option_a":str(oa) or "A","option_b":str(ob) or "B","option_c":str(oc) or "C","option_d":str(od) or "D",
                "answer":ans,"explanation":it.get("explanation","") or ""
            })
        return res

fetcher = ALOCFetcher()

def format_question(q, idx, total):
    return f"Q{idx}/{total} | {q.get('subject')} | {q.get('year')}\n\n{q.get('question')}\n\nA: {q.get('option_a')}\nB: {q.get('option_b')}\nC: {q.get('option_c')}\nD: {q.get('option_d')}"
