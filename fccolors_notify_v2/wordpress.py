from __future__ import annotations

import hashlib
import logging
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from .models import SourceArticle
from .normalize import html_to_text

logger = logging.getLogger(__name__)
TIMEOUT = 30


def normalize_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    path = (parsed.path or "/").rstrip("/") or "/"
    return urlunparse(("http", parsed.netloc.lower(), path, "", "", ""))


def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def extract_article_links(category_html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(category_html, "html.parser")
    links: list[str] = []
    for link in soup.find_all("a", href=re.compile(r"/post-\d+")):
        href = link.get("href")
        if not href:
            continue
        url = normalize_url(urljoin(base_url, href))
        if url not in links:
            links.append(url)
    return links


def extract_entry_html(article_html: str) -> str:
    soup = BeautifulSoup(article_html, "html.parser")
    content = soup.find("div", class_="entry-content")
    if content is not None:
        return str(content)
    body = soup.find("body")
    return str(body) if body else article_html


def extract_title(article_html: str) -> str:
    soup = BeautifulSoup(article_html, "html.parser")
    for selector in (".entry-title", "h1", "title"):
        if selector.startswith("."):
            node = soup.select_one(selector)
        else:
            node = soup.find(selector)
        if node is not None:
            text = node.get_text(strip=True)
            if text:
                return text
    return "Unknown"


def compute_hash(value: str) -> str:
    normalized = re.sub(r"\s+", " ", (value or "").strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def is_schedule_article(title: str, category: str) -> bool:
    normalized = (title or "").strip()
    if not normalized:
        return False
    blocked_tokens = ("募集", "体験会", "大募集", "選手クラス")
    if any(token in normalized for token in blocked_tokens):
        return False
    if category == "weekday":
        if "休日" in normalized:
            return False
        return "平日" in normalized
    if "平日" in normalized:
        return False
    return "休日" in normalized


def fetch_category_articles(category: str, category_url: str) -> list[SourceArticle]:
    category_html = fetch_html(category_url)
    result: list[SourceArticle] = []
    for url in extract_article_links(category_html, category_url):
        try:
            article_html = fetch_html(url)
        except requests.RequestException as exc:
            logger.warning("Failed to fetch article %s: %s", url, exc)
            continue
        content_html = extract_entry_html(article_html)
        content_text = html_to_text(content_html)
        title = extract_title(article_html)
        if not is_schedule_article(title, category):
            logger.info("Skipping non-schedule article: %s", title)
            continue
        result.append(
            SourceArticle(
                category=category,
                url=url,
                title=title,
                content_html=content_html,
                content_text=content_text,
                content_hash=compute_hash(content_html),
            )
        )
    return result
