"""Entidades de notificaciones push: el token de un dispositivo y el mensaje que se le envía."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PushToken:
    """El token de push de un dispositivo del usuario, para avisarle aunque la app esté cerrada."""

    owner_id: str
    token: str
    platform: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PushMessage:
    """Un aviso a enviar: título, cuerpo y datos para que la app sepa qué abrir al tocarlo."""

    title: str
    body: str
    data: dict[str, str] = field(default_factory=dict)
