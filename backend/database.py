"""
database.py — TenderShield AI
Simple SQLite persistence layer.
Stores tenders and bidder evaluation results for audit trail.
"""

import sqlite3
from datetime import datetime

DB_PATH = "tendershield.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row   # allows dict-style access
    return conn


def create_tables():
    """Create all tables on startup. Safe to call multiple times."""
    conn = get_connection()
    c    = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS tenders (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        tender_ref  TEXT,
        filename    TEXT,
        rules_json  TEXT,
        uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS bidders (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        tender_id       INTEGER,
        name            TEXT,
        turnover        REAL,
        experience      INTEGER,
        bid_amount      REAL,
        total_score     REAL,
        status          TEXT,
        risk_level      TEXT,
        flags_json      TEXT,
        evaluated_at    TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tender_id) REFERENCES tenders(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        tender_id   INTEGER,
        action      TEXT,
        details     TEXT,
        actor       TEXT DEFAULT 'TenderShield AI',
        timestamp   TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()


def save_tender(filename: str, rules_json: str) -> int:
    """Save a tender and return its ID."""
    conn = get_connection()
    c    = conn.cursor()
    c.execute(
        "INSERT INTO tenders (filename, rules_json) VALUES (?, ?)",
        (filename, rules_json)
    )
    tender_id = c.lastrowid
    conn.commit()
    conn.close()
    return tender_id


def save_bidder_result(tender_id: int, result: dict) -> int:
    """Save a bidder evaluation result."""
    import json
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""
        INSERT INTO bidders (tender_id, name, turnover, experience,
                             bid_amount, total_score, status, risk_level, flags_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tender_id,
        result.get("name", ""),
        result.get("turnover", 0),
        result.get("experience", 0),
        result.get("bid_amount", 0),
        result.get("score", 0),
        result.get("status", ""),
        result.get("risk", ""),
        json.dumps(result.get("flags", []))
    ))
    bid_id = c.lastrowid
    conn.commit()
    conn.close()
    return bid_id


def log_action(tender_id: int, action: str, details: str = ""):
    """Write an audit log entry."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (tender_id, action, details) VALUES (?, ?, ?)",
        (tender_id, action, details)
    )
    conn.commit()
    conn.close()


def get_audit_log(tender_id: int) -> list:
    """Retrieve audit log for a tender."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT action, details, actor, timestamp FROM audit_log WHERE tender_id=? ORDER BY timestamp",
        (tender_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_tenders() -> list:
    """Retrieve all historical tenders."""
    conn = get_connection()
    rows = conn.execute("SELECT id, filename, uploaded_at, rules_json FROM tenders ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bidders_for_tender(tender_id: int) -> list:
    """Retrieve all evaluated bidders for a specific tender."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM bidders WHERE tender_id=? ORDER BY total_score DESC", (tender_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Auto-create tables when this module is imported
create_tables()
