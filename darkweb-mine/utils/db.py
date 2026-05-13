"""
暗网帝国 - 数据持久层 (SQLite)
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path


class EmpireDB:
    """帝国数据库 - 记录所有考古发现"""

    def __init__(self, db_path: str = "data/empire.db"):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS discoveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                category TEXT NOT NULL,
                source_url TEXT,
                raw_data TEXT,
                asset_type TEXT,
                asset_value TEXT,
                status TEXT DEFAULT 'new',
                confidence REAL DEFAULT 0.0,
                discovered_at TEXT NOT NULL,
                verified_at TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS scan_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                items_scanned INTEGER DEFAULT 0,
                items_found INTEGER DEFAULT 0,
                errors TEXT,
                status TEXT DEFAULT 'running'
            );

            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def add_discovery(self, module: str, category: str, raw_data: dict,
                      asset_type: str = "", asset_value: str = "",
                      source_url: str = "", confidence: float = 0.0,
                      discovered_at: str = ""):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO discoveries
            (module, category, source_url, raw_data, asset_type, asset_value,
             status, confidence, discovered_at)
            VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?)
        """, (
            module, category, source_url, json.dumps(raw_data, ensure_ascii=False),
            asset_type, asset_value, confidence,
            discovered_at if discovered_at else datetime.now().isoformat()
        ))
        self.conn.commit()
        return cur.lastrowid

    def start_scan(self, module: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO scan_log (module, started_at) VALUES (?, ?)",
            (module, datetime.now().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    def finish_scan(self, scan_id: int, found: int, scanned: int = 0, errors: str = ""):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE scan_log
            SET finished_at = ?, items_found = ?, items_scanned = ?, errors = ?, status = 'done'
            WHERE id = ?
        """, (datetime.now().isoformat(), found, scanned, errors, scan_id))
        self.conn.commit()

    def get_recent_discoveries(self, limit: int = 50):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM discoveries ORDER BY discovered_at DESC LIMIT ?",
            (limit,)
        )
        return cur.fetchall()

    def get_scan_stats(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT module, COUNT(*) as total, SUM(items_found) as total_found
            FROM scan_log WHERE status = 'done'
            GROUP BY module
        """)
        return cur.fetchall()

    def close(self):
        self.conn.close()
