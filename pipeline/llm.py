"""MiniMax M3 LLM client — OpenAI 兼容 (api.minimaxi.com/v1)。

零第三方依賴（純 stdlib），CI 裝機快、失敗面少。
特性：3 次重試（指數退避）· 耗時/tokens 記賬（餵畀 trace）。
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

API_URL = os.environ.get("MINIMAX_API_URL", "https://api.minimaxi.com/v1/chat/completions")
MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")
API_KEY = os.environ["MINIMAX_API_KEY"]


class LLMError(Exception):
    pass


def chat(
    system: str,
    user: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> tuple[str, dict]:
    """打一次 chat completion。

    返回 (content, usage)。usage: {prompt_tokens, completion_tokens, reasoning_tokens, seconds}
    溫度按 agent 崗位定：分析/風控 0.1-0.3 · 辯論 0.5 · 主筆 0.7-0.8。
    """
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    last_err = None
    for attempt in range(1, 4):
        t0 = time.time()
        try:
            req = urllib.request.Request(
                API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            content = data["choices"][0]["message"]["content"]
            u = data.get("usage", {})
            usage = {
                "prompt_tokens": u.get("prompt_tokens", 0),
                "completion_tokens": u.get("completion_tokens", 0),
                "reasoning_tokens": u.get("completion_tokens_details", {}).get("reasoning_tokens", 0),
                "seconds": round(time.time() - t0, 1),
            }
            return content, usage

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            last_err = LLMError(f"HTTP {e.code}: {body}")
            # 401/403 = key 問題，唔使重試
            if e.code in (401, 403):
                raise last_err
        except Exception as e:  # noqa: BLE001
            last_err = LLMError(str(e))

        if attempt < 3:
            time.sleep(5 * attempt)

    raise LLMError(f"3 次重試都失敗：{last_err}")