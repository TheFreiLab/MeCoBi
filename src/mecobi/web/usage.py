"""Anonymous daily usage totals: the public "structures built" counter and a private export.

Every finished build (a single GUI build or a queued job) adds one row's worth of counts to
``usage_daily`` in the job database, in the same transaction that marks the job finished or
failed, so each build is counted exactly once. Job records and result files are deleted
after 24 hours; these totals are not.

Nothing that identifies a person or a molecule is stored: no IP addresses, no SMILES, no
file names. Distinct users per day are counted by a hash of the submitter key with a random
salt that exists only in this process's memory and only for the current UTC day, so the
hashes cannot be reversed or linked across days. A server restart starts a new salt, so a
user active both before and after a restart on the same day is counted twice; the user
count is approximate.

Export the daily table (inside the container, or anywhere the job database is readable)::

    python -m mecobi.web.usage                 # CSV to stdout, default database
    python -m mecobi.web.usage --db path/to/jobs.db

In the Docker image ``python`` is not on the exec PATH; use the env's interpreter::

    docker exec mecobi /opt/conda/bin/python -m mecobi.web.usage
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import secrets
import sqlite3
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

# Same location the web app uses (app._DATA / "jobs.db").
DEFAULT_DB = Path(tempfile.gettempdir()) / "mecobi_data" / "jobs.db"

COLUMNS = ("day", "requests", "complexes", "structures", "complex_errors", "failed_requests",
           "users")

_salt_lock = threading.Lock()
_salt: tuple[str, bytes] | None = None   # (UTC day, salt) - today only, never written to disk


def ensure_schema(c: sqlite3.Connection) -> None:
    c.execute(
        """CREATE TABLE IF NOT EXISTS usage_daily(
            day TEXT PRIMARY KEY,
            requests INTEGER NOT NULL DEFAULT 0,
            complexes INTEGER NOT NULL DEFAULT 0,
            structures INTEGER NOT NULL DEFAULT 0,
            complex_errors INTEGER NOT NULL DEFAULT 0,
            failed_requests INTEGER NOT NULL DEFAULT 0,
            users INTEGER NOT NULL DEFAULT 0)"""
    )
    # Today's salted user hashes only (older days are deleted as soon as a new day starts).
    c.execute("CREATE TABLE IF NOT EXISTS usage_users(day TEXT, h TEXT, PRIMARY KEY(day, h))")


def today(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).date().isoformat()


def _user_hash(day: str, submitter: str) -> str:
    global _salt
    with _salt_lock:
        if _salt is None or _salt[0] != day:
            _salt = (day, secrets.token_bytes(32))
        salt = _salt[1]
    return hashlib.sha256(salt + submitter.encode("utf-8", "replace")).hexdigest()


def record(c: sqlite3.Connection, *, submitter: str | None, complexes: int, structures: int,
           complex_errors: int = 0, failed: bool = False, now: datetime | None = None) -> None:
    """Add one finished request to today's totals (call inside the caller's transaction)."""
    day = today(now)
    c.execute("INSERT OR IGNORE INTO usage_daily(day) VALUES (?)", (day,))
    c.execute(
        "UPDATE usage_daily SET requests=requests+1, complexes=complexes+?, "
        "structures=structures+?, complex_errors=complex_errors+?, "
        "failed_requests=failed_requests+? WHERE day=?",
        (max(0, int(complexes)), max(0, int(structures)), max(0, int(complex_errors)),
         1 if failed else 0, day),
    )
    c.execute("DELETE FROM usage_users WHERE day<>?", (day,))
    if submitter:
        added = c.execute("INSERT OR IGNORE INTO usage_users(day, h) VALUES (?,?)",
                          (day, _user_hash(day, submitter))).rowcount
        if added:
            c.execute("UPDATE usage_daily SET users=users+1 WHERE day=?", (day,))


def totals(c: sqlite3.Connection) -> dict:
    """The public numbers: structures built so far, and the first day counted."""
    row = c.execute("SELECT COALESCE(SUM(structures), 0), MIN(day) FROM usage_daily").fetchone()
    return {"structures_built": int(row[0]), "since": row[1]}


def daily(c: sqlite3.Connection) -> list[dict]:
    rows = c.execute(f"SELECT {', '.join(COLUMNS)} FROM usage_daily ORDER BY day").fetchall()
    return [dict(zip(COLUMNS, r)) for r in rows]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export MeCoBi's daily usage totals as CSV.")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"job database (default {DEFAULT_DB})")
    args = ap.parse_args(argv)
    if not args.db.exists():
        print(f"No job database at {args.db}", file=sys.stderr)
        return 1
    with sqlite3.connect(f"file:{args.db.as_posix()}?mode=ro", uri=True) as c:
        try:
            rows = daily(c)
        except sqlite3.OperationalError:
            rows = []   # a database from before usage counting
    w = csv.DictWriter(sys.stdout, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
