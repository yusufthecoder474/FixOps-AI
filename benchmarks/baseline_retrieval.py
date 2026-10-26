from dataclasses import dataclass
from time import perf_counter
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .knowledge import document_text
from .privacy import redact

@dataclass
class Hit:
    doc: dict
    score: float

@dataclass
class Result:
    hits: list[Hit]
    supported: bool
    reason: str
    latency_ms: float
    backend: str

# A conservative scope gate supplements (but cannot perfect) score thresholding.
OUTSIDE_SCOPE = re.compile(r'\b(bake|recipe|football|wedding|stock price|forgotten|reset.{0,20}password|restore.{0,30}backup)\b', re.I)
DOMAIN = re.compile(r'\b(http|[45]\d\d|cpu|processor|database|postgres|sql|memory|ram|oom\w*|dns|hostname|nxdomain|servfail|api|latency|p95|p99|service|gateway|proxy|upstream|disk|filesystem|storage|tls|ssl|certificate|authentication|authorization|permission|rate|quota|container|pod|pods|kubernetes|crashloopbackoff|imagepullbackoff|errimagepull|registry|readiness|probe|pool|connection|connections|transaction|transactions|lock|locks|deadlock|tcp|network|packet|volume|failedmount|endpoint|backend)\b', re.I)

class Retriever:
    def __init__(self, docs, backend='semantic', model_name='sentence-transformers/all-MiniLM-L6-v2', threshold=None):
        if backend not in ('semantic', 'tfidf'):
            raise ValueError('Unknown retrieval backend')
        self.docs, self.backend = docs, backend
        self.threshold = threshold if threshold is not None else (0.38 if backend == 'semantic' else 0.12)
        texts = [document_text(d) for d in docs]
        if backend == 'semantic':
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(model_name, trust_remote_code=False)
            self.matrix = self.encoder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        else:
            self.encoder = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words='english')
            self.matrix = self.encoder.fit_transform(texts)

    def search(self, query):
        start = perf_counter()
        if not query.strip() or len(query) > 3000:
            raise ValueError('Enter an incident description between 1 and 3000 characters.')
        cleaned = redact(query)
        if self.backend == 'semantic':
            vector = self.encoder.encode([cleaned], normalize_embeddings=True, show_progress_bar=False)
        else:
            vector = self.encoder.transform([cleaned])
        scores = cosine_similarity(vector, self.matrix)[0]
        order = np.argsort(-scores, kind='stable')[:3]
        hits = [Hit(self.docs[i], float(scores[i])) for i in order]
        in_scope = bool(DOMAIN.search(cleaned)) and not OUTSIDE_SCOPE.search(cleaned)
        supported = in_scope and hits[0].score >= self.threshold
        reason = ('Relevant procedures found; these are investigation hypotheses, not a confirmed diagnosis.' if supported
                  else 'Insufficient information in this knowledge base. Provide the affected component, error code and symptoms, or escalate to its owner.')
        return Result(hits, supported, reason, (perf_counter()-start)*1000, self.backend)
