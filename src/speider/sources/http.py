"""Polite HTTP: identify ourselves, go slowly, keep a raw copy of what we fetched."""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

USER_AGENT = "speider/0.1 (hobby project; https://github.com/joachimmilling/speider)"


class Fetcher:
    def __init__(self, raw_dir: str | Path | None = None, delay: float = 0.6):
        self.raw_dir = Path(raw_dir) if raw_dir else None
        self.delay = delay
        self._last = 0.0

    def get_json(self, url: str, save_as: str | None = None):
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
        self._last = time.monotonic()
        if self.raw_dir and save_as:
            target = self.raw_dir / save_as
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        return json.loads(body)
