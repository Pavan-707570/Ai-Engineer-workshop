from __future__ import annotations

import tiktoken


def estimate_tokens(text: str) -> int:
    cleaned = (text or "").strip()
    if not cleaned:
        return 0

    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return max(1, len(encoding.encode(cleaned)))
    except Exception:
        return max(1, len(cleaned.split()))
