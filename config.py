
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALOC_TOKEN = os.getenv("ALOC_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "2000"))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://utmebot.onrender.com")

SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","Commerce","CRS"]

JAMB_SYLLABUS_COMPLETE = {
    "English": {"title": "Use of English", "sections": ["Comprehension and Summary", "Lexis, Structure and Oral Forms", "Oral Forms", "Parts of Speech", "Structure"]},
    "Mathematics": {"title": "Mathematics", "sections": ["Number and Numeration", "Algebra", "Geometry and Trigonometry", "Calculus", "Statistics and Probability", "Mensuration"]},
    "Biology": {"title": "Biology", "sections": ["Variety of Organisms", "Cell Structure", "Life Processes", "Genetics and Evolution", "Ecology"]},
    "Chemistry": {"title": "Chemistry", "sections": ["Particulate Nature", "Periodic Table", "Chemical Bonding", "Stoichiometry", "Rates and Equilibrium", "Acids Bases Salts", "Redox", "Organic Chemistry"]},
    "Physics": {"title": "Physics", "sections": ["Mechanics", "Properties of Matter", "Heat", "Waves", "Electricity and Magnetism", "Atomic and Nuclear Physics"]},
    "Economics": {"title": "Economics", "sections": ["Basic Concepts", "Demand and Supply", "Production", "Market Structure", "National Income", "Public Finance", "International Trade"]},
    "Government": {"title": "Government", "sections": ["Basic Concepts", "Constitution", "Arms of Government", "Political Parties", "Nigerian Government"]},
    "Literature": {"title": "Literature", "sections": ["General Principles", "Poetry", "Drama", "Prose", "African Literature"]},
    "Commerce": {"title": "Commerce", "sections": ["Introduction", "Business Units", "Trade", "Finance", "Marketing"]},
    "CRS": {"title": "CRS", "sections": ["Old Testament", "New Testament", "Themes", "Personalities"]}
}
