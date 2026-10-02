import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FLUTTERWAVE_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "")
FLUTTERWAVE_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "")
FLUTTERWAVE_SECRET_HASH = os.getenv("FLW_SECRET_HASH", "")

BASE_URL = "https://utmebot.onrender.com"
UPGRADE_URL = "https://utmebot.onrender.com/upgrade"
WEBHOOK_URL = "https://utmebot.onrender.com/webhook/flutterwave"

CHANNEL_ID = "@UTMEbotChannel"
SUPPORT_HANDLE = "@UTMESUCCESS"
JAMB_SYLLABUS_BASE = "https://www.jamb.gov.ng/Elibrary"

SUBJECTS = ["English", "Mathematics", "Biology", "Chemistry", "Physics", "Economics", "Government", "Literature", "Geography", "Commerce", "Accounting", "CRS", "IRS"]

FREE_DAILY_LIMIT = 20
MOCK_LIMIT_FREE = 1

PLANS = {
    "monthly": {"amount": 2000, "name": "UTMEbot Premium Monthly", "days": 30},
    "six_months": {"amount": 6000, "name": "UTMEbot Premium 6 Months", "days": 180}
}

SYLLABUS_BRIEF = {
    "Biology": "Variety of organisms, Cell structure, Genetics, Ecology, Evolution. Focus on practical biology & diagrams.",
    "Chemistry": "Particulate nature, Periodic table, Chemical bonding, Acids/bases, Organic chemistry.",
    "Physics": "Mechanics, Waves, Optics, Electricity, Modern physics. Calculations are key.",
    "Mathematics": "Number theory, Algebra, Geometry, Trigonometry, Statistics & Calculus basics.",
    "English": "Lexis, Structure, Comprehension, Oral forms, Writing. JAMB tests comprehension speed.",
    "Economics": "Scarcity, Demand/Supply, National Income, Money & Inflation.",
    "Government": "Constitutions, Political systems, Nigerian government history.",
    "Literature": "Prose, Drama, Poetry, Literary terms. Read recommended texts.",
    "Geography": "Map work, Climate, Rocks, Population, Economic activities.",
}
