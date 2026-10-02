import os, json, random
from openai import OpenAI

DB_PATH = "database.json"
try:
    with open(DB_PATH) as f:
        PAST_QA = json.load(f)
except:
    PAST_QA = []

def search_db(question: str, subject: str):
    if not PAST_QA:
        return None
    q_lower = question.lower()
    candidates = [x for x in PAST_QA if subject.lower() in x.get("subject","").lower() or subject.lower()=="general"]
    if not candidates:
        candidates = PAST_QA
    # simple keyword match
    words = [w for w in q_lower.split() if len(w)>3][:4]
    best = None
    max_score = 0
    for item in candidates:
        score = sum(1 for w in words if w in item.get("question","").lower())
        if score>max_score:
            max_score=score
            best=item
    return best if max_score>0 else None

async def ask_tutor(question: str, subject: str, user_id: int) -> str:
    db_match = search_db(question, subject)
    context = ""
    if db_match:
        context = f"Past JAMB question found: Q: {db_match.get('question')} A: {db_match.get('answer')} Explanation: {db_match.get('explanation','')}"

    system_prompt = f"""
You are UTME Success Tutor — Nigeria's #1 JAMB expert. 200% smart.
Subject focus: {subject}
Context from past questions DB: {context}

Rules:
- Answer ONLY within JAMB syllabus for {subject} (if General, cover all UTME subjects).
- Give correct answer first, bold it.
- Then give step-by-step explanation, simple, with Nigerian examples where helpful.
- Use friendly, encouraging tone, like a senior tutor. Near human, not too fast, Nigerian accent style in text (use small pidgin warmth but keep professional).
- If question is outside JAMB, politely redirect.
- If DB match exists, reference it: "This has appeared in JAMB ..."
- Keep answer concise but thorough (max 400 words). Use bullet points, formulas.
- End with: "Want me to quiz you on this topic?"
"""

    # Try OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":system_prompt},{"role":"user","content":question}],
                temperature=0.6,
                max_tokens=700
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"OpenAI error: {e}")

    # Fallback
    if db_match:
        return (
            f"**Answer:** {db_match.get('answer')}\n\n"
            f"**Explanation:** {db_match.get('explanation','Let me break it down...')}\n\n"
            f"This is a key JAMB topic in {subject}. Practice similar questions in our mock!\n\n"
            f"Want me to quiz you on this?"
        )
    return (
        f"Great question on {subject}! 🔥\n\n"
        f"**{question}**\n\n"
        f"Here's the breakdown: This topic is important for JAMB. Focus on understanding the core concept, practice past questions, and remember the key formula/definition.\n\n"
        f"Add OPENAI_API_KEY for full AI brain explanation — meanwhile, ask me a more specific part and I'll explain step-by-step!"
    )