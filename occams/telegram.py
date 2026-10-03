"""The Telegram transport, ported in shape from the donor. A ``Transport``
sends a card and returns a message id; ``DryRunTransport`` collects cards
for tests and the console; ``TelegramTransport`` reaches the Bot API with a
token that lives in ``TELEGRAM_BOT_TOKEN`` and nowhere else (R5; M0.17).
No test constructs the live one with a token."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Protocol


class TransportError(RuntimeError):
    pass


class Transport(Protocol):
    def send(self, text: str) -> str: ...


@dataclass
class DryRunTransport:
    sent: list[str] = field(default_factory=list)

    def send(self, text: str) -> str:
        self.sent.append(text)
        return f"dry-{len(self.sent)}"


@dataclass
class TelegramTransport:
    chat_id: str
    base_url: str = "https://api.telegram.org"

    def send(self, text: str) -> str:
        import urllib.request

        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise TransportError("TELEGRAM_BOT_TOKEN is not set; the transport has no default and no parameter (R5)")
        body = json.dumps({"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/bot{token}/sendMessage", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            out = json.loads(resp.read().decode("utf-8"))
        if not out.get("ok"):
            raise TransportError(f"telegram refused: {out.get('description')}")
        return str(out["result"]["message_id"])
