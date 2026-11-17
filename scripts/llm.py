"""GitHub Models hívás (ingyenes, a GitHub Actions saját tokenjével)."""
from __future__ import annotations

import json
import os
import re
import sys
import time

import requests

ENDPOINT = "https://models.github.ai/inference/chat/completions"
MODELS = ["openai/gpt-4.1-mini", "openai/gpt-4o-mini"]


def ask_json(system: str, user: str, temperature: float = 0.9) -> dict | list | None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("  ! LLM: nincs GITHUB_TOKEN", file=sys.stderr)
        return None
    for model in MODELS:
        for attempt in range(2):
            try:
                r = requests.post(
                    ENDPOINT,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "temperature": temperature,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    },
                    timeout=90,
                )
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
                text = r.json()["choices"][0]["message"]["content"]
                m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
                if not m:
                    raise ValueError("nincs JSON a válaszban")
                return json.loads(m.group(1))
            except Exception as e:
                print(f"  ! LLM ({model}): {e}"[:300], file=sys.stderr)
                time.sleep(3 * (attempt + 1))
    return None
