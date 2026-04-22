import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# PostgreSQL Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mu_hive")
