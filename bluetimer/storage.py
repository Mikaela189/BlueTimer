from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import AppConfig


APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "BlueTimer"
CONFIG_PATH = APP_DIR / "config.json"
HISTORY_PATH = APP_DIR / "history.db"


class Storage:
    def __init__(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def load_config(self) -> AppConfig:
        if not CONFIG_PATH.exists():
            return AppConfig()
        try:
            return AppConfig.from_dict(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception:
            backup = CONFIG_PATH.with_suffix(".broken.json")
            CONFIG_PATH.replace(backup)
            return AppConfig()

    def save_config(self, config: AppConfig) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _init_db(self) -> None:
        with sqlite3.connect(HISTORY_PATH) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    rule_id TEXT,
                    rule_label TEXT,
                    action TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    detail TEXT
                )
                """
            )

    def add_history(
        self,
        action: str,
        success: bool,
        detail: str | None = None,
        rule_id: str | None = None,
        rule_label: str | None = None,
    ) -> None:
        with sqlite3.connect(HISTORY_PATH) as conn:
            conn.execute(
                """
                INSERT INTO history(timestamp, rule_id, rule_label, action, success, detail)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    rule_id,
                    rule_label,
                    action,
                    1 if success else 0,
                    detail,
                ),
            )

    def recent_history(self, limit: int = 100) -> list[dict]:
        with sqlite3.connect(HISTORY_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, timestamp, rule_id, rule_label, action, success, detail
                FROM history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
