import os
import sys
from unittest.mock import MagicMock

# Set dummy environment variables BEFORE any service code is imported
os.environ["CORE_SERVICE_URL"] = "http://core:8000"
os.environ["INTERNAL_API_KEY"] = "test-secret"
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["MODEL_NAME"] = "test-model"
os.environ["OPENAI_API_BASE"] = "http://localhost/v1"
os.environ["EMBEDDING_MODEL"] = "all-MiniLM-L6-v2"
os.environ["CHROMA_SERVER_HOST"] = "localhost"
os.environ["CHROMA_SERVER_HTTP_PORT"] = "8000"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'
os.environ["INTERNAL_REQUIRE_SIGNATURE"] = "false"
os.environ["INTERNAL_SIGNING_SECRET"] = ""  # Ensure it's empty

# Mock heavy/expensive modules
sys.modules["langchain_huggingface"] = MagicMock()
sys.modules["langchain_chroma"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
