"""Ingyenes MI-hívás: először a GitHub Models, ha elérhető; utána a Pollinations."""
from __future__ import annotations

import json
import os
import re
import sys
import time

import requests

GITHUB = "https://models.github.ai/inference/chat/completions"
POLLINATIONS = "https://text.pollinations.ai/openai"
_dead: set[str] = set()
_last_poll = 0.0


def _extract(text: str):
    m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    if not m:
        raise ValueError("nincs JSON a válaszban")
    return json.loads(m.group(1))


def _github(messages, temperature):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("nincs GITHUB_TOKEN")
    r = requests.post(
        GITHUB,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
        json={"model": "openai/gpt-4.1-mini", "temperature": temperature, "messages": messages},
        timeout=90,
    )
    if "json" not in r.headers.get("content-type", ""):
        _dead.add("github")  # a fiókon nem érhető el – ebben a futásban nem próbáljuk újra
        raise RuntimeError(f"nem elérhető ({r.status_code} {r.text[:40]!r})")
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _pollinations(messages, temperature):
    global _last_poll
    for attempt in range(4):
        wait = 46 - (time.time() - _last_poll)
        if wait > 0:
            time.sleep(wait)
        r = requests.post(POLLINATIONS, json={"model": "openai", "messages": messages}, timeout=180)
        _last_poll = time.time()
        if r.status_code == 402 or r.status_code == 429:
            continue
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    raise RuntimeError("folyamatos korlátozás")


def ask_json(system: str, user: str, temperature: float = 0.9, providers=("github", "pollinations")):
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    for name in providers:
        if name in _dead:
            continue
        fn = _github if name == "github" else _pollinations
        for attempt in range(2):
            try:
                return _extract(fn(messages, temperature))
            except Exception as e:
                print(f"  ! MI ({name}): {e}"[:240], file=sys.stderr)
                if name in _dead:
                    break
    return None
