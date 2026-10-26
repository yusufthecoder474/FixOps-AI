"""Raw questions are transient. Persist only a fixed vocabulary projection."""
import re

# Broad categories intentionally lose detail; never serialize raw query text.
TERMS = ('http', '500', 'cpu', 'database', 'timeout', 'memory', 'oom', 'dns',
         'api', 'latency', '503', '502', '504', 'disk', 'tls', 'certificate',
         '401', '403', '429', 'container', 'readiness', 'pool', 'lock',
         'network', 'volume', 'storage', 'postgres', 'kubernetes')

def query_summary(query):
    words = set(re.findall(r'\b[a-z0-9]+\b', query.lower()))
    return ' '.join(term for term in TERMS if term in words) or 'unclassified incident'

def redact(query):
    """Best-effort in-memory cleanup; not relied on to secure stored history."""
    query = re.sub(r'-----BEGIN[\s\S]*?-----END[^\n]*-----', '[REDACTED]', query)
    query = re.sub(r'(?i)\b(?:authorization|password|passwd|secret|token|api[_ -]?key)\b\s*[:=]\s*[^\n,;]+', '[REDACTED]', query)
    query = re.sub(r'(?i)\b(?:bearer|basic)\s+\S+', '[REDACTED]', query)
    query = re.sub(r'\b\w+://\S+', '[URL REMOVED]', query)
    query = re.sub(r'\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b', '[EMAIL REMOVED]', query)
    return re.sub(r'\b[A-Za-z0-9_./+=-]{32,}\b', '[REDACTED]', query)
