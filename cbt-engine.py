"""
cbt_engine.py - ALOC Live Fetcher - v17.1
5 free mock Qs daily locked + 2 tutor free, 3 referrals = 1 week premium
"""
import random, time, requests, os
from collections import defaultdict

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

class ALOCFetcher:
    def __init__(self, token=ALOC_ACCESS_TOKEN):
        self.token=token
        self.base_v2="https://questions.aloc.com.ng/api/v2"
        self.base_old="https://questions.aloc.ng/api/v2"
        self.session=requests.Session()
        self.session.headers.update({"Accept":"application/json","User-Agent":"UTME-Bot-v17.1"})
        if token: self.session.headers.update({"AccessToken": token})

    def fetch(self, subject, year, limit=40):
        aloc_code=ALOC_CODE.get(subject.lower(), subject.lower())
        key=(aloc_code, str(year))
        if key in CACHE and time.time()-CACHE_TIME.get(key,0)<21600:
            return CACHE[key]
        urls=[
            f"{self.base_v2}/q/{limit}?subject={aloc_code}&year={year}&type=utme",
            f"{self.base_old}/q/{limit}?subject={aloc_code}&year={year}&type=utme",
        ]
        for url in urls:
            try:
                r=self.session.get(url, timeout=12)
                if r.status_code==200:
                    qs=self.parse(r.json(), subject, year)
                    if qs:
                        CACHE[key]=qs
                        CACHE_TIME[key]=time.time()
                        print(f"ALOC FETCHED {subject} {year} -> {len(qs)}")
                        return qs
            except Exception as e:
                print(f"ALOC err {url}: {e}")
                continue
        print(f"ALOC FAILED {subject} {year}")
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
            if not qtext or len(qtext)<10: continue
            if "Q552" in qtext: continue
            if qtext.startswith("[Mathematics") and "Q" in qtext[:30]: continue
            if qtext in ["Correct","B","C","D"]: continue
            oa=it.get("option_a") or (it.get("option") or {}).get("a") or ""
            ob=it.get("option_b") or (it.get("option") or {}).get("b") or ""
            oc=it.get("option_c") or (it.get("option") or {}).get("c") or ""
            od=it.get("option_d") or (it.get("option") or {}).get("d") or ""
            if isinstance(it.get("options"), list) and len(it["options"])>=4:
                oa,ob,oc,od=it["options"][:4]
            if str(oa).strip()=="Correct" and str(ob).strip()=="B": continue
            ans=str(it.get("answer","") or it.get("correct_option","")).strip().upper()
            if ans.lower() in ["a","b","c","d"]: ans=ans.upper()
            qid=it.get("id") or f"{subject}_{year}_{idx}_{random.randint(1000,9999)}"
            res.append({
                "id":str(qid),"subject":SUBJECT_DISPLAY.get(subject.lower(),subject.title()),
                "subject_key":subject.lower(),"year":str(it.get("year",year)),
                "topic":it.get("topic","General"),"question":qtext,
                "option_a":str(oa),"option_b":str(ob),"option_c":str(oc),"option_d":str(od),
                "answer":ans or "A","explanation":it.get("explanation","") or it.get("solution","")
            })
        return res

fetcher = ALOCFetcher()

def format_question(q, idx, total):
    return f"Q{idx}/{total} | {q.get('subject')} | {q.get('year')} | {q.get('topic','General')}\n\n{q.get('question')}\n\nA: {q.get('option_a')}\nB: {q.get('option_b')}\nC: {q.get('option_c')}\nD: {q.get('option_d')}"
