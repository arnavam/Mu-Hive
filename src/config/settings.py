import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ig_project")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
