import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)

@dataclass(frozen=True)
class Settings:
    model: str = field(default_factory=lambda: os.getenv('FIXOPS_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'))
    semantic_threshold: float = field(default_factory=lambda: float(os.getenv('FIXOPS_SEMANTIC_THRESHOLD', '0.38')))
    tfidf_threshold: float = field(default_factory=lambda: float(os.getenv('FIXOPS_TFIDF_THRESHOLD', '0.12')))
    history_path: Path = field(default_factory=lambda: Path(os.getenv('FIXOPS_HISTORY_PATH', str(ROOT / 'var/history.sqlite3'))))
    api_key: str = field(default_factory=lambda: os.getenv('FIXOPS_LLM_API_KEY', ''), repr=False)
    api_url: str = field(default_factory=lambda: os.getenv('FIXOPS_LLM_URL', 'https://api.openai.com/v1/chat/completions'))
    llm_model: str = field(default_factory=lambda: os.getenv('FIXOPS_LLM_MODEL', ''))

    def __post_init__(self):
        if not 0 < self.semantic_threshold <= 1 or not 0 < self.tfidf_threshold <= 1:
            raise ValueError('Retrieval thresholds must be in (0, 1].')
