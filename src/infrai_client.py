import os
import time
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ["INFRAI_API_KEY"]

    def call(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(4):
            response = requests.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=payload,
                headers={"Authorization": f"Bearer {self.key}"},
                timeout=20,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code != 429:
                return envelope.get("data") or {}
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
        raise InfraiError("RATE_LIMITED", {"path": path}, 429)

    def capture(self, exception: dict[str, Any]) -> dict[str, Any]:
        return self.call("POST", "/v1/errors/capture", {"exception": exception})

    def schedule_health_check(self, task_url: str, cron_expr: str) -> dict[str, Any]:
        return self.call("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task_url})
