from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from tzlocal import get_localzone

from .models import DAYS, Rule


ActionCallback = Callable[[Rule | None, str], None]


def check_rule_conflict(rules: list[Rule], new_rule: Rule) -> str | None:
    for rule in rules:
        if rule.id == new_rule.id:
            continue
        if not rule.enabled or not new_rule.enabled:
            continue
        if rule.hour != new_rule.hour or rule.minute != new_rule.minute:
            continue
        if set(rule.days) & set(new_rule.days) and rule.action != new_rule.action:
            return rule.label or rule.id
    return None


def latest_due_rule(rules: list[Rule], now: datetime | None = None, lookback_days: int = 7) -> Rule | None:
    now = now or datetime.now()
    latest: tuple[datetime, Rule] | None = None
    for days_back in range(lookback_days + 1):
        date = now.date() - timedelta(days=days_back)
        day_key = DAYS[date.weekday()]
        for rule in rules:
            if not rule.enabled or day_key not in rule.days:
                continue
            fired_at = datetime.combine(date, now.time()).replace(
                hour=rule.hour,
                minute=rule.minute,
                second=0,
                microsecond=0,
            )
            if fired_at > now:
                continue
            if latest is None or fired_at > latest[0]:
                latest = (fired_at, rule)
    return latest[1] if latest else None


class RuleScheduler:
    def __init__(self, callback: ActionCallback) -> None:
        self._callback = callback
        self._timezone = get_localzone()
        self._scheduler = BackgroundScheduler(timezone=self._timezone)
        self._rules: list[Rule] = []

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def reload(self, rules: list[Rule]) -> None:
        self._rules = list(rules)
        self._scheduler.remove_all_jobs()
        for rule in self._rules:
            self.add_rule(rule)

    def add_rule(self, rule: Rule) -> None:
        if not rule.enabled:
            return
        trigger = CronTrigger(
            day_of_week=",".join(rule.days),
            hour=rule.hour,
            minute=rule.minute,
            timezone=self._timezone,
        )
        self._scheduler.add_job(
            func=self._run_rule,
            trigger=trigger,
            id=rule.id,
            replace_existing=True,
            kwargs={"rule_id": rule.id},
            misfire_grace_time=60,
        )

    def calibrate_now(self) -> Rule | None:
        rule = latest_due_rule(self._rules)
        if rule:
            self._callback(rule, "calibrate")
        return rule

    def _run_rule(self, rule_id: str) -> None:
        rule = next((item for item in self._rules if item.id == rule_id), None)
        if rule:
            self._callback(rule, "schedule")
