"""
Third-Party API Integration with Strict Time Limit (Timeout) and Resilient Fallback
- Calls ZenQuotes / Quotable API with timeout=2.0 seconds.
- If timeout or network failure occurs, seamlessly falls back to local curated cache.
"""

import time
import requests

FALLBACK_QUOTES = [
    {
        "quote": "Any sufficiently advanced technology is indistinguishable from magic.",
        "author": "Arthur C. Clarke",
        "category": "Technology & Engineering"
    },
    {
        "quote": "The best way to predict the future is to invent it.",
        "author": "Alan Kay",
        "category": "Innovation"
    },
    {
        "quote": "Scientists investigate that which already is; Engineers create that which has never been.",
        "author": "Albert Einstein",
        "category": "Engineering"
    },
    {
        "quote": "Simplicity is prerequisite for reliability.",
        "author": "Edsger W. Dijkstra",
        "category": "Software Architecture"
    }
]

def fetch_third_party_quote(timeout_sec: float = 2.0) -> dict:
    start_time = time.time()
    url = "https://zenquotes.io/api/random"
    headers = {'User-Agent': 'PraveenPortfolioEngine/1.0'}

    try:
        response = requests.get(url, headers=headers, timeout=timeout_sec)
        latency_ms = round((time.time() - start_time) * 1000, 1)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return {
                    "quote": data[0].get('q'),
                    "author": data[0].get('a'),
                    "category": "Live Telemetry Feed",
                    "latency_ms": latency_ms,
                    "status_code": 200,
                    "is_fallback": False,
                    "source": "ZenQuotes Live External API",
                    "timeout_limit_sec": timeout_sec
                }
    except requests.exceptions.Timeout:
        latency_ms = round((time.time() - start_time) * 1000, 1)
        fallback_item = FALLBACK_QUOTES[int(time.time()) % len(FALLBACK_QUOTES)]
        return {
            "quote": fallback_item["quote"],
            "author": fallback_item["author"],
            "category": fallback_item["category"],
            "latency_ms": latency_ms,
            "status_code": 408,
            "is_fallback": True,
            "fallback_reason": f"Time limit exceeded ({timeout_sec}s threshold). Engaged offline cached engineering quote.",
            "source": "Local Curated Fallback Cache",
            "timeout_limit_sec": timeout_sec
        }
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 1)
        fallback_item = FALLBACK_QUOTES[int(time.time()) % len(FALLBACK_QUOTES)]
        return {
            "quote": fallback_item["quote"],
            "author": fallback_item["author"],
            "category": fallback_item["category"],
            "latency_ms": latency_ms,
            "status_code": 503,
            "is_fallback": True,
            "fallback_reason": f"External API connection failed ({str(e)[:50]}). Engaged offline cache.",
            "source": "Local Curated Fallback Cache",
            "timeout_limit_sec": timeout_sec
        }

    fallback_item = FALLBACK_QUOTES[0]
    return {
        "quote": fallback_item["quote"],
        "author": fallback_item["author"],
        "category": fallback_item["category"],
        "latency_ms": round((time.time() - start_time) * 1000, 1),
        "status_code": 200,
        "is_fallback": True,
        "fallback_reason": "Non-200 response from external provider.",
        "source": "Local Curated Fallback Cache",
        "timeout_limit_sec": timeout_sec
    }
