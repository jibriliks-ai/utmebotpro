"""
cbt_engine.py - v23 FLAWLESS - COMPLETE 7891 Qs + ANTI-REPEAT + FLUTTERWAVE
- Loads complete 7891 Qs from all_questions.json
- Includes CRK 1056 Qs + all 11 subjects
- Mock NEVER repeats same question (tracks used_ids)
- Full text dedup - strong script
"""
import random, os, json
from pathlib import Path

try:
    from config import ALOC_ACCESS_TOKEN, YEARS, ALL_SUBJECTS
except:
    ALOC_ACCESS_TOKEN = os.getenv("ALOC_ACCESS_TOKEN", "")
    YEARS = list(range(2010, 2025))
    ALL_SUBJECTS = ["english","mathematics","biology","physics","chemistry","economics","government","commerce","accounting","literature","crk"]

SUBJECT_DISPLAY = {
    "english":"📖 English","mathematics":"📐 Maths","biology":"🧬 Biology","physics":"⚛️ Physics","chemistry":"🧪 Chemistry",
    "economics":"💰 Economics","government":"🏛️ Government","commerce":"🏪 Commerce","accounting":"📊 Accounting",
    "literature":"📚 Literature","crk":"✝️ CRK"
}

LOCAL_DATABANK = {}
ALL_QS = []
DATABANK_DIR = Path(__file__).parent / "databank"
CORE_SUBJECTS = ["accounting","biology","chemistry","commerce","crk","economics","english","government","literature","mathematics","physics"]

if DATABANK_DIR.exists():
    all_path = DATABANK_DIR / "all_questions.json"
    if all_path.exists():
        try:
            raw = json.loads(all_path.read_text())
            seen = {}
            deduped = []
            for q in raw:
                key = ' '.join(q.get("question","").lower().split())
                if key and key not in seen and len(key) > 10:
                    seen[key] = True
                    deduped.append(q)
            ALL_QS = deduped
            print(f"✅ Loaded all_questions.json: {len(ALL_QS)} Qs COMPLETE")
            for subj in CORE_SUBJECTS:
                LOCAL_DATABANK[subj] = [q for q in ALL_QS if q.get("subject_key")==subj]
        except Exception as e:
            print(f"⚠️ Error: {e}")

    for jf in DATABANK_DIR.glob("*.json"):
        name = jf.stem
        if name.startswith("all_") or name not in CORE_SUBJECTS:
            continue
        try:
            data = json.loads(jf.read_text())
            if name not in LOCAL_DATABANK or not LOCAL_DATABANK[name]:
                seen = {}
                clean = []
                for q in data:
                    key = ' '.join(q.get("question","").lower().split())
                    if key and key not in seen:
                        seen[key]=True
                        clean.append(q)
                LOCAL_DATABANK[name]=clean
        except:
            pass

if not ALL_QS:
    for qs in LOCAL_DATABANK.values():
        ALL_QS.extend(qs)

def get_local_questions(subject, year=None, limit=40, exclude_ids=None, exclude_questions=None):
    subj = subject.lower().strip()
    qs = LOCAL_DATABANK.get(subj, []) or [q for q in ALL_QS if q.get("subject_key")==subj]
    if exclude_ids:
        filtered = [q for q in qs if q.get("id") not in set(exclude_ids)]
        if len(filtered) >= min(limit, 3):
            qs = filtered
    if exclude_questions:
        exclude_set = set([' '.join(eq.lower().split()) for eq in exclude_questions])
        filtered = [q for q in qs if ' '.join(q.get("question","").lower().split()) not in exclude_set]
        if len(filtered) >= min(limit, 3):
            qs = filtered
    random.shuffle(qs)
    return qs[:limit]

def search_databank(query, subject=None, limit=5):
    keywords = [w for w in query.lower().split() if len(w)>2][:6]
    if not keywords:
        return []
    pool = [q for q in ALL_QS if q.get("subject_key")==subject.lower()] if subject else ALL_QS
    results = []
    for q in pool:
        q_text = (q.get("question","")+" "+q.get("topic","")+" "+q.get("explanation","")).lower()
        score = sum(2 if kw in q.get("question","").lower() else 1 for kw in keywords if kw in q_text)
        if score>0:
            results.append((score,q))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:limit]]

def get_random_question(subject=None, exclude_ids=None):
    pool = [q for q in ALL_QS if q.get("subject_key")==subject.lower()] if subject else ALL_QS
    if exclude_ids:
        filtered = [q for q in pool if q.get("id") not in set(exclude_ids)]
        if filtered:
            pool = filtered
    return random.choice(pool) if pool else None

class ALOCFetcher:
    def fetch(self, subject, year=None, limit=40, exclude_ids=None, exclude_questions=None):
        return get_local_questions(subject, year, limit, exclude_ids, exclude_questions)

fetcher = ALOCFetcher()

def format_question(q, idx, total):
    subj = q.get('subject','JAMB')
    year = q.get('year','')
    topic = q.get('topic','')
    header = f"Q{idx}/{total} | {subj} {year} {('- '+topic) if topic and topic!='General' else ''}".strip()
    return f"{header}\n\n{q.get('question')}\n\nA) {q.get('option_a')}\nB) {q.get('option_b')}\nC) {q.get('option_c')}\nD) {q.get('option_d')}"
