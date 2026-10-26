import json
import sqlite3
from datetime import datetime, timezone
from .privacy import query_summary

class History:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, timestamp TEXT, query_summary TEXT, backend TEXT, sources TEXT, supported INTEGER)')
        try:
            path.chmod(0o600)
        except OSError:
            pass  # Windows users should rely on their profile's filesystem ACLs.

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def add(self, query, result):
        with self.connect() as db:
            db.execute('INSERT INTO history(timestamp,query_summary,backend,sources,supported) VALUES(?,?,?,?,?)',
                       (datetime.now(timezone.utc).isoformat(), query_summary(query), result.backend,
                        json.dumps([h.doc['id'] for h in result.hits]), int(result.supported)))
            db.execute('DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY id DESC LIMIT 100)')

    def recent(self):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute('SELECT timestamp,query_summary,backend,sources,supported FROM history ORDER BY id DESC LIMIT 20')]
