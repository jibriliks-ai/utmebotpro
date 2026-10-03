"""
cbt_engine.py — loads every questions_*.json in this folder,
deduplicates, and exposes the interface ssmain.py expects.
Never crashes: prints detailed diagnostics instead.
"""
import json
import random
import traceback
from pathlib import Path
from collections import defaultdict

ALL_QS = []
LOCAL_DATABANK = defaultdict(list)
AVAILABLE_SUBJECTS = []
_seen = set()
LOAD_REPORT = {}   # filename -> count loaded


def _fp(q):
    return "|".join([
        str(q.get("subject_key", "")).lower(),
        str(q.get("question", "")).strip().lower()[:200],
    ])


def _normalize(q):
    options = q.get("options") or []

    def pick(i, key):
        v = q.get(key)
        if v and str(v).strip():
            return str(v).strip()
        if i < len(options):
            return str(options[i]).strip()
        return ""

    ans = (q.get("answer_letter") or q.get("answer") or "")
    ans = str(ans).strip().upper()[:1]

    return {
        "id": str(q.get("id") or q.get("source_id") or ""),
        "subject": str(q.get("subject", "")).strip(),
        "subject_key": str(q.get("subject_key", "")).strip().lower(),
        "year": q.get("year", ""),
        "topic": q.get("topic", "General"),
        "question": str(q.get("question", "")).strip(),
        "option_a": pick(0, "option_a"),
        "option_b": pick(1, "option_b"),
        "option_c": pick(2, "option_c"),
        "option_d": pick(3, "option_d"),
        "option_e": pick(4, "option_e"),
        "answer": ans,
        "answer_text": str(q.get("answer_text", "")).strip(),
        "explanation": str(q.get("explanation", "")).strip(),
    }


def _add(q):
    if not q["question"]:
        return False
    if not q["option_a"] or not q["option_b"]:
        return False
    if q["answer"] not in "ABCDE":
        return False
    fp = _fp(q)
    if fp in _seen:
        return False
    _seen.add(fp)
    ALL_QS.append(q)
    key = q["subject_key"] or q["subject"].lower().replace(" ", "_")
    LOCAL_DATABANK[key].append(q)
    return True


def _load(path):
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except Exception as e:
        print(f"[cbt_engine] ⚠️  cannot read {path}: {e}")
        return 0
    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[cbt_engine] ❌ {path} is not valid JSON: {e}")
        return 0
    if not isinstance(data, list):
        print(f"[cbt_engine] ❌ {path} is not a JSON array")
        return 0
    n = 0
    for item in data:
        if isinstance(item, dict):
            try:
                if _add(_normalize(item)):
                    n += 1
            except Exception as e:
                print(f"[cbt_engine] skip one item: {e}")
    LOAD_REPORT[path.name] = n
    return n


def _bootstrap():
    try:
        files = sorted(Path(".").glob("questions_*.json"))
        if not files:
            print("[cbt_engine] ⚠️  no files matching questions_*.json in this folder")
            print(f"[cbt_engine] current folder: {Path('.').resolve()}")
            print(f"[cbt_engine] contents: {[p.name for p in Path('.').iterdir()]}")
        for f in files:
            n = _load(str(f))
            print(f"[cbt_engine] {f.name}: +{n} questions")

        for k, v in LOCAL_DATABANK.items():
            if v:
                AVAILABLE_SUBJECTS.append(k)
        AVAILABLE_SUBJECTS.sort()

        print(f"[cbt_engine] ✅ TOTAL: {len(ALL_QS)} questions across {len(AVAILABLE_SUBJECTS)} subjects")
        for k in AVAILABLE_SUBJECTS:
            print(f"   {k}: {len(LOCAL_DATABANK[k])}")
    except Exception as e:
        print(f"[cbt_engine] ❌ bootstrap error: {e}")
        traceback.print_exc()


_bootstrap()


def format_question(q, i, total):
    lines = [f"Q{i}/{total}", q.get("question", "")]
    for L in ("A", "B", "C", "D", "E"):
        opt = q.get(f"option_{L.lower()}")
        if opt:
            lines.append(f"{L}) {opt}")
    return "\n".join(lines)


def search_databank(query, subject=None, limit=5):
    q = (query or "").lower().strip()
    if not q:
        return []
    pool = LOCAL_DATABANK.get(subject) if subject else None
    if not pool:
        pool = ALL_QS
    words = [w for w in q.split() if len(w) > 2]
    if not words:
        return []
    scored = []
    for item in pool:
        text = item.get("question", "").lower()
        score = sum(1 for w in words if w in text)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def get_random_question(subject=None):
    pool = LOCAL_DATABANK.get(subject) if subject else None
    if not pool:
        pool = ALL_QS
    return random.choice(pool) if pool else None


class _Fetcher:
    def fetch(self, subject, year=None, limit=40):
        key = (subject or "").lower()
        pool = LOCAL_DATABANK.get(key, [])
        if not pool:
            pool = [q for q in ALL_QS if key and key in q["subject"].lower()]
        if not pool:
            return []
        return random.sample(pool, min(limit, len(pool)))


fetcher = _Fetcher()
