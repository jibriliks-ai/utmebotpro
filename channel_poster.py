import random, json, os
from datetime import datetime
from config import CHANNEL_ID, UPGRADE_URL, PLANS

QUESTIONS = [
    "🧬 Biology: The xylem transports water. But what transports food in plants?\nA) Phloem B) Cambium C) Cortex\n\nReply with your answer in UTMEbot — instant explanation!",
    "⚗️ Chemistry: How many moles in 4g of NaOH? (Na=23, O=16, H=1)\nThink fast! Check answer with our 200% smart tutor.",
    "🔭 Physics: A ball drops from 20m. Velocity just before hitting ground? (g=10)\nSolve in 30s! Full mock inside bot.",
    "📖 English: 'Neither of the boys ___ coming.' — is/are? 90% fail this JAMB trap!",
    "➗ Maths: Solve: 2x + 3y = 12, x=3. Find y. Too easy? JAMB will twist it. Practice twisted version in bot.",
    "🌍 Economics: What causes inflation when too much money chases few goods?\nA) Demand-pull B) Cost-push",
]

HOOKS = [
    "Morning scholars! 🌅 1 question this morning = 1 mark closer to 300+\n\n{question}\n\n👉 Practice now: @UTMEbot | 💎 Premium ₦{monthly} monthly",
    "Afternoon challenge 🔥 Only 10% get this right in first try!\n\n{question}\n\nBeat the top scorer today!",
    "Evening revision 🌙 Don't sleep without solving 5 questions. Consistency > cramming.\n\n{question}\n\n💎 Upgrade: ₦{monthly} monthly | ₦{six_months} for 6 months (Save 50%) → {upgrade}",
    "🚀 Stop scrolling, start scoring! Your dream course is waiting.\n\n{question}\n\nAsk tutor anything — explains like human, Nigerian accent, slow & clear.",
    "👑 Leaderboard Alert: Top scorer this week: {score} pts! Can you beat him?\n\n{question}\n\nFull mock inside UTMEbot — professional JAMB simulation.",
]

USED_FILE = "used_channel_messages.json"

def load_used():
    try:
        with open(USED_FILE) as f:
            return json.load(f)
    except:
        return []

def save_used(used):
    with open(USED_FILE, 'w') as f:
        json.dump(used[-80:], f, indent=2)

def generate_channel_message():
    used = load_used()
    q = random.choice(QUESTIONS)
    # avoid repeat question in last 10
    for _ in range(5):
        if q not in used[-10:]:
            break
        q = random.choice(QUESTIONS)
    
    template = random.choice(HOOKS)
    # ensure uniqueness
    msg = template.format(
        question=q,
        monthly=PLANS["monthly"]["amount"],
        six_months=PLANS["six_months"]["amount"],
        upgrade=UPGRADE_URL,
        score=random.randint(295,340)
    )
    # Add unique timestamp hash to avoid exact duplicate detection
    msg = msg.strip()
    used.append(q + "|" + template[:20])
    save_used(used)
    # Final CTA
    msg += f"\n\n📲 @UTMEbot — Your 300+ Partner"
    return msg

async def post_to_channel(bot, message: str):
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")
    except Exception as e:
        # Fallback without markdown
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=message)
        except Exception as e2:
            print(f"Channel post failed: {e2}")