from __future__ import annotations

import time

import requests

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class Blocked(Exception):
    """The site served a bot-protection challenge instead of the page."""


class Fetcher:
    """requests.Session with a polite delay between calls to the same host."""

    def __init__(self, delay: float = 1.5, timeout: float = 30):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
        self.delay = delay
        self.timeout = timeout
        self._last: dict[str, float] = {}

    def get(self, url: str) -> requests.Response | None:
        host = requests.utils.urlparse(url).netloc
        wait = self._last.get(host, 0) + self.delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        for attempt in range(3):
            try:
                r = self.s.get(url, timeout=self.timeout)
                self._last[host] = time.monotonic()
                if r.status_code == 404:
                    return None
                if r.status_code in (403, 503) and "Just a moment" in r.text[:2000]:
                    raise Blocked(f"{host} answered with a Cloudflare bot check; skipping it")
                r.raise_for_status()
                return r
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        return None
