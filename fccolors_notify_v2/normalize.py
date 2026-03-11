from __future__ import annotations

import re
import unicodedata
from bs4 import BeautifulSoup


LOCATION_ALIASES = {
    "北野G": "北野グラウンド",
    "戸吹G": "戸吹グラウンド",
    "北野g": "北野グラウンド",
    "戸吹g": "戸吹グラウンド",
}


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return normalize_text(text)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def normalize_location(value: str) -> str:
    result = normalize_text(value)
    for source, target in LOCATION_ALIASES.items():
        result = result.replace(source, target)
    return result


def normalize_time(value: str) -> str:
    value = normalize_text(value)
    if not value:
        return ""
    value = (
        value.replace("〜", "-")
        .replace("～", "-")
        .replace("~", "-")
        .replace("－", "-")
        .replace("−", "-")
        .replace("ー", "-")
    )
    value = re.sub(r"\s+", "", value)
    match = re.match(r"^(\d{1,2})(?::(\d{2}))?-(\d{1,2})(?::(\d{2}))?$", value)
    if not match:
        return value
    sh, sm, eh, em = match.groups()
    return f"{int(sh)}:{(sm or '00').zfill(2)}-{int(eh)}:{(em or '00').zfill(2)}"
