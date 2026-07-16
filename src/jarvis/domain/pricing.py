"""Catálogo de precios de modelos: la fuente de verdad para calcular el costo de cada llamada."""

from __future__ import annotations

from jarvis.domain.telemetry import ModelPrice


class UnknownModelError(KeyError):
    """Se pidió el precio de un modelo que no está registrado en el catálogo."""


class PricingCatalog:
    """Entrega el precio de un modelo. Las tarifas vienen de configuración, no se hardcodean."""

    def __init__(self, prices: dict[str, ModelPrice]) -> None:
        self._prices = dict(prices)

    def price_for(self, model: str) -> ModelPrice:
        """Devuelve el precio del modelo; lanza UnknownModelError si no está registrado."""
        try:
            return self._prices[model]
        except KeyError as error:
            raise UnknownModelError(model) from error
