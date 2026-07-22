"""Productor de podcast: guion (en lote) → voz → audio alojado. Un episodio por llamada de IA.

Las historias seleccionadas se tejen en UN guion (batching), no una llamada por historia. El
estilo (narrador o diálogo) y la duración salen del pedido; la duración fija el largo objetivo.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from jarvis.domain.llm import Message
from jarvis.modules.heraldo.dissection import Completer
from jarvis.modules.heraldo.domain import PodcastStyle
from jarvis.modules.heraldo.jsonio import extract_json_object
from jarvis.modules.heraldo.news import StorySeed
from jarvis.modules.heraldo.podcast import AudioStorage, Episode, SpeechSynthesizer
from jarvis.modules.heraldo.prompts import CHILEAN_REGISTER, SUBSTANCE

_WORDS_PER_MINUTE = 160


class PodcastService:
    """Arma el episodio: escribe el guion, lo convierte en voz y aloja el audio."""

    def __init__(
        self, completer: Completer, synthesizer: SpeechSynthesizer, storage: AudioStorage
    ) -> None:
        self._completer = completer
        self._synthesizer = synthesizer
        self._storage = storage

    async def compose(
        self,
        seeds: list[StorySeed],
        style: PodcastStyle,
        minutes: int,
        now: datetime,
        episode_id: str,
        voice: str | None = None,
        instruction: str = "",
    ) -> Episode:
        """Produce un episodio completo a partir de las historias seleccionadas."""
        draft = await self._write_script(seeds, style, minutes, now, instruction)
        audio = await self._synthesizer.synthesize(draft.script, style, voice)
        url = await self._storage.store(f"episodes/{episode_id}.wav", audio)
        return _to_episode(episode_id, draft, url, minutes, seeds)

    async def _write_script(
        self,
        seeds: list[StorySeed],
        style: PodcastStyle,
        minutes: int,
        now: datetime,
        instruction: str,
    ) -> _ScriptDraft:
        """Pide el guion al modelo en una sola llamada y lo valida."""
        prompt = _script_prompt(seeds, style, minutes, instruction)
        text = await self._completer.complete("podcast_script", prompt, now)
        return _ScriptDraft.model_validate_json(extract_json_object(text))


class _ScriptDraft(BaseModel):
    """El guion tal como lo devuelve el modelo: título, texto hablado y el ángulo tratado."""

    title: str = ""
    script: str = ""
    angle: str = ""


def _to_episode(
    episode_id: str, draft: _ScriptDraft, url: str, minutes: int, seeds: list[StorySeed]
) -> Episode:
    """Arma el episodio con el guion, el audio alojado y las fuentes de las historias."""
    return Episode(
        id=episode_id,
        title=draft.title,
        script=draft.script,
        audio_url=url,
        duration_minutes=minutes,
        sources=_sources(seeds),
        angle=draft.angle,
    )


def _sources(seeds: list[StorySeed]) -> tuple[str, ...]:
    """Une y ordena las fuentes de todas las historias del episodio."""
    return tuple(sorted({source for seed in seeds for source in seed.sources}))


def _script_prompt(
    seeds: list[StorySeed], style: PodcastStyle, minutes: int, instruction: str
) -> list[Message]:
    """Arma el prompt que teje las historias en un guion con sustancia, estilo y largo pedidos."""
    target = minutes * _WORDS_PER_MINUTE
    floor = int(target * 0.9)
    system = (
        f"Escribes guiones de podcast amenos y fáciles de escuchar. {CHILEAN_REGISTER} {SUBSTANCE} "
        f"{_style_hint(style)} Escribe AL MENOS {floor} palabras, apuntando a ~{target} "
        f"(~{minutes} min); no termines antes de desarrollar bien cada punto. Teje las historias "
        "en un solo guion con hilo narrativo, con apertura y cierre. Responde SOLO con JSON: "
        '{"title": "título atractivo", "script": "el guion hablado", '
        '"angle": "en 4 a 8 palabras, el ángulo específico que trató este episodio"}.'
    )
    return [Message("system", system), Message("user", _user_block(seeds, instruction))]


def _user_block(seeds: list[StorySeed], instruction: str) -> str:
    """Antepone la instrucción del tema (onboarding + ángulos a evitar) a las historias."""
    stories = _seeds_block(seeds)
    return f"{instruction}\n\nHistorias:\n{stories}" if instruction.strip() else stories


def _style_hint(style: PodcastStyle) -> str:
    """Instrucción de estilo según narrador único o diálogo de dos voces."""
    if style is PodcastStyle.DIALOGUE:
        return "Formato: diálogo entre dos presentadores (rotula 'A:' y 'B:')."
    return "Formato: un solo narrador."


def _seeds_block(seeds: list[StorySeed]) -> str:
    """Renderiza las historias como texto compacto para el modelo."""
    return "\n".join(f"[{seed.id}] {seed.title}: {seed.snippet}" for seed in seeds)
