from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4


Day = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
Action = Literal["on", "off"]

DAYS: tuple[Day, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAY_LABELS: dict[Day, str] = {
    "mon": "周一",
    "tue": "周二",
    "wed": "周三",
    "thu": "周四",
    "fri": "周五",
    "sat": "周六",
    "sun": "周日",
}


@dataclass
class Rule:
    label: str
    action: Action
    hour: int
    minute: int
    days: list[Day]
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        return cls(
            id=str(data.get("id") or uuid4()),
            label=str(data.get("label") or "未命名规则"),
            action="on" if data.get("action") == "on" else "off",
            hour=max(0, min(23, int(data.get("hour", 9)))),
            minute=max(0, min(59, int(data.get("minute", 0)))),
            days=[d for d in data.get("days", []) if d in DAYS] or ["mon", "tue", "wed", "thu", "fri"],
            enabled=bool(data.get("enabled", True)),
            created_at=str(data.get("created_at") or datetime.now().isoformat(timespec="seconds")),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "action": self.action,
            "hour": self.hour,
            "minute": self.minute,
            "days": self.days,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }

    @property
    def action_label(self) -> str:
        return "开启" if self.action == "on" else "关闭"

    @property
    def time_label(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    @property
    def days_label(self) -> str:
        if self.days == ["mon", "tue", "wed", "thu", "fri"]:
            return "周一至周五"
        if self.days == list(DAYS):
            return "每天"
        return "、".join(DAY_LABELS[d] for d in self.days)


@dataclass
class AppConfig:
    adapter_instance_id: str | None = None
    adapter_name: str | None = None
    auto_start: bool = False
    calibrate_on_resume: bool = True
    rules: list[Rule] = field(default_factory=list)
    version: str = "1.1"

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        return cls(
            version=str(data.get("version", "1.1")),
            adapter_instance_id=data.get("adapter_instance_id"),
            adapter_name=data.get("adapter_name"),
            auto_start=bool(data.get("auto_start", False)),
            calibrate_on_resume=bool(data.get("calibrate_on_resume", True)),
            rules=[Rule.from_dict(item) for item in data.get("rules", [])],
        )

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "adapter_instance_id": self.adapter_instance_id,
            "adapter_name": self.adapter_name,
            "auto_start": self.auto_start,
            "calibrate_on_resume": self.calibrate_on_resume,
            "rules": [rule.to_dict() for rule in self.rules],
        }
