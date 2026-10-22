"""Scam / abuse scoring. Layers: text rules -> URL analysis -> Safe Browsing -> optional AI."""
import re
import unicodedata
from dataclasses import dataclass, field

from django.conf import settings

from . import llm, safebrowsing
from .rules import ADVICE, HARD_BLOCK, RULES
from .urls_check import analyze, extract_urls

_INVISIBLE = re.compile("[\u200b\u200c\u200d\u2060\ufeff\u00ad]")
LINK_BONUS_CATEGORIES = {"credential_theft", "prize_scam", "delivery_scam", "government_scam", "payment_scam"}


@dataclass
class ScanResult:
    score: int
    level: str
    categories: list[str]
    reasons: list[dict]
    urls: list[dict]
    advice: list[str]
    hard_block: bool = False
    layers: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _INVISIBLE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _combine(weights: list[float]) -> int:
    """Noisy-OR: independent signals raise the score without ever exceeding 100."""
    remaining = 1.0
    for w in weights:
        remaining *= 1 - max(0.0, min(w, 100.0)) / 100
    return round((1 - remaining) * 100)


def level_for(score: int) -> str:
    if score >= settings.BLOCK_THRESHOLD:
        return "high"
    return "medium" if score >= 30 else "low"


def scan(text: str, *, use_ai: bool = True, use_safe_browsing: bool = True) -> ScanResult:
    clean = normalize(text)
    weights: list[float] = []
    reasons: list[dict] = []
    categories: list[str] = []
    layers = ["rules"]

    for code, category, weight, label, rx in RULES:
        if rx.search(clean):
            weights.append(weight)
            reasons.append({"code": code, "label": label, "category": category})
            if category not in categories:
                categories.append(category)

    urls = extract_urls(clean)
    url_reports = []
    for u in urls:
        report = analyze(u)
        url_reports.append(report)
        for code, weight, label in report["signals"]:
            weights.append(weight)
            reasons.append({"code": code, "label": label, "category": "link"})
    if urls:
        layers.append("urls")
        if any(c in LINK_BONUS_CATEGORIES for c in categories):
            weights.append(15)
            reasons.append({"code": "link_plus_pressure", "label": "Asks you to act through a link", "category": "link"})
        if "link" not in categories and any(r["category"] == "link" for r in reasons):
            categories.append("link")

    if use_safe_browsing and urls:
        bad = safebrowsing.flagged_urls(urls)
        if bad:
            layers.append("safe_browsing")
            weights.append(90)
            reasons.append({"code": "url_blocklisted", "label": "Google Safe Browsing lists a link as dangerous", "category": "link"})
            for r in url_reports:
                if r["url"] in bad:
                    r["signals"].append(("url_blocklisted", 90, "Listed as dangerous by Google Safe Browsing"))
            if "link" not in categories:
                categories.append("link")

    score = _combine(weights)

    # Borderline: ask the AI layer for a second opinion (only when a key is configured).
    if use_ai and 15 <= score <= 85:
        ai = llm.classify(clean)
        if ai:
            layers.append("ai")
            if ai["risk"] >= 30:
                weights.append(ai["risk"] * 0.8)
                reasons.append({"code": "ai_assessment", "label": ai["reason"] or "AI flagged this message", "category": ai["category"]})
                if ai["category"] not in categories and ai["category"] != "safe":
                    categories.append(ai["category"])
            score = _combine(weights)

    hard = any(c in HARD_BLOCK for c in categories)
    if hard:
        score = max(score, settings.BLOCK_THRESHOLD)

    advice = [ADVICE[c] for c in categories if c in ADVICE]
    return ScanResult(
        score=score,
        level=level_for(score),
        categories=categories,
        reasons=reasons,
        urls=[{"url": r["url"], "host": r["host"], "flags": [s[2] for s in r["signals"]]} for r in url_reports],
        advice=advice,
        hard_block=hard,
        layers=layers,
    )
