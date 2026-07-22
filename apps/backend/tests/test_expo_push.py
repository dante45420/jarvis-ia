"""Test del envío de push por Expo: arma el payload correcto y lo manda en lote. Sin red real."""

from __future__ import annotations

import json

import httpx

from jarvis.adapters.expo_push import ExpoPushSender
from jarvis.domain.notifications import PushMessage


async def test_send_posts_expo_payload_for_each_token() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"data": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        sender = ExpoPushSender(client)
        message = PushMessage(title="Jarvis", body="¿Generamos hoy?", data={"topic_id": "t1"})
        await sender.send(["ExponentPushToken[a]", "ExponentPushToken[b]"], message)

    assert captured["url"] == "https://exp.host/--/api/v2/push/send"
    body = captured["body"]
    assert isinstance(body, list)
    assert [item["to"] for item in body] == ["ExponentPushToken[a]", "ExponentPushToken[b]"]
    assert body[0]["title"] == "Jarvis"
    assert body[0]["data"] == {"topic_id": "t1"}
