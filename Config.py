
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALOC_TOKEN = os.getenv("ALOC_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY")
PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE", "1500"))

# JAMB Official Subjects - Complete Syllabus
SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","Commerce","CRS"]

JAMB_SYLLABUS = {
    "English": ["Comprehension", "Lexis and Structure", "Oral Forms", "Parts of Speech", "Structure"],
    "Mathematics": ["Number and Numeration", "Algebra", "Geometry", "Calculus", "Statistics", "Mensuration"],
    "Biology": ["Variety of Organisms", "Cell Structure", "Genetics", "Ecology", "Physiology", "Reproduction"],
    "Chemistry": ["Particulate Nature", "Periodic Table", "Chemical Bonding", "Acids Bases Salts", "Organic Chemistry", "Rates and Equilibrium"],
    "Physics": ["Mechanics", "Gravitational Field", "Waves", "Heat", "Electricity", "Magnetism and Optics"],
    "Economics": ["Principles", "Demand and Supply", "Market Structure", "National Income", "Public Finance"],
    "Government": ["Basic Concepts", "Constitution", "Arms of Government", "Political Parties", "Nigerian Government"],
    "Literature": ["Literary Principles", "Poetry", "Drama", "Prose", "African Literature"],
    "Commerce": ["Introduction", "Business Units", "Trade", "Finance", "Marketing"],
    "CRS": ["Old Testament", "New Testament", "Themes", "Personalities"]
}
