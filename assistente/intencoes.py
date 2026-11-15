"""Entende o que a pessoa pediu: transforma a frase reconhecida em uma intenção e um assunto."""

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Intencao:
    acao: str  # wikipedia | youtube | farmacia | horas | ajuda | sair | desconhecida
    assunto: str = ""


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem pontuação: 'Farmácia?' e 'farmacia' viram a mesma coisa."""
    sem_acento = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^\w\s]", " ", sem_acento.lower()).split())


# A ordem importa: a primeira regra que casar vence.
_REGRAS: list[tuple[str, re.Pattern[str]]] = [
    ("sair", re.compile(r"^(sair|tchau|encerrar|desligar|ate logo)\b")),
    ("ajuda", re.compile(r"^(ajuda|o que voce faz|comandos)\b")),
    ("horas", re.compile(r"\b(que horas sao|horas|horario)\b")),
    ("farmacia", re.compile(r"\bfarmacias?\b(?:.*?\b(?:em|de|perto de|no|na|do|da)\s+(?P<assunto>.+))?")),
    ("youtube", re.compile(r"\byoutube\b(?:\s+(?:com|sobre|de|para|e procure|procure|pesquise)?\s*(?P<assunto>.+))?")),
    ("youtube", re.compile(r"^(?:toque|tocar|toca|coloque|bote)\s+(?P<assunto>.+)")),
    (
        "wikipedia",
        re.compile(
            r"^(?:pesquis[ae]r?|procur[ae]r?|busc[ae]r?)\s+(?:na\s+wikipedia\s+)?(?:sobre\s+|por\s+)?(?P<assunto>.+)"
            r"|^(?:o que e|o que sao|quem foi|quem e|quem sao)\s+(?:o\s+|a\s+|os\s+|as\s+)?(?P<assunto2>.+)"
            r"|\bwikipedia\b\s*(?:sobre\s+)?(?P<assunto3>.*)"
        ),
    ),
]


def interpretar(frase: str) -> Intencao:
    texto = normalizar(frase)
    for acao, regra in _REGRAS:
        achou = regra.search(texto)
        if achou:
            grupos = achou.groupdict()
            assunto = next((v for v in grupos.values() if v), "")
            return Intencao(acao, assunto.strip())
    return Intencao("desconhecida", texto)
