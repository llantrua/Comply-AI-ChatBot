import os
from dotenv import load_dotenv

load_dotenv()

# Configuration API
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DATA_DIR = os.getenv("DATA_DIR", "./data")

# Configuration modèles - DERNIÈRE VERSION
CLAUDE_MODEL = "claude-3-haiku-20240307"
MAX_TOKENS = 4000
TEMPERATURE = 0.1

# Configuration RAG optimisée
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MAX_CONTEXT_DOCS = 5

# Configuration spécifique Kiwi
KIWI_FILE_TYPES = {
    'kiwi-legal-all.json': 'legal_site',
    'faq.json': 'faq',
    'junior.json': 'junior_entreprises',
    'kiwi_rse': 'rse_formation'  # Pattern pour fichiers RSE
}
