"""Uso:
python -m assistente            # por voz (microfone e alto-falante)
python -m assistente --texto    # digitando, sem microfone
python -m assistente --local "Av. Paulista, São Paulo"   # referência para a farmácia
"""

import argparse
from datetime import datetime

import requests

from .acoes import Acoes
from .intencoes import interpretar

AJUDA = (
    "Posso pesquisar na Wikipédia, abrir o YouTube, achar a farmácia mais próxima e dizer as horas. "
    "Experimente: 'o que é inteligência artificial', 'toque lofi no YouTube' ou 'farmácia mais próxima da Avenida Paulista'."
)


def responder(frase: str, acoes: Acoes, agora: datetime | None = None) -> tuple[str, bool]:
    """Devolve a resposta e se o assistente deve continuar."""
    intencao = interpretar(frase)
    try:
        match intencao.acao:
            case "sair":
                return "Até logo!", False
            case "ajuda":
                return AJUDA, True
            case "horas":
                return f"Agora são {(agora or datetime.now()):%H:%M}.", True
            case "wikipedia":
                return acoes.wikipedia(intencao.assunto), True
            case "youtube":
                return acoes.youtube(intencao.assunto), True
            case "farmacia":
                return acoes.farmacia(intencao.assunto), True
            case _:
                return "Não entendi. Diga 'ajuda' para ouvir o que eu sei fazer.", True
    except requests.RequestException:
        return "Não consegui acessar a internet agora. Tente de novo em instantes.", True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assistente")
    parser.add_argument("--texto", action="store_true", help="digitar em vez de falar")
    parser.add_argument("--local", help="endereço de referência para 'farmácia mais próxima'")
    args = parser.parse_args(argv)

    from .voz import Escuta, Fala

    fala = Fala()
    escuta = None
    if not args.texto:
        try:
            escuta = Escuta()
        except Exception as erro:  # sem SpeechRecognition, sem PyAudio ou sem microfone
            print(f"Microfone indisponível ({erro.__class__.__name__}); seguindo no modo texto.")

    acoes = Acoes.padrao(args.local)
    fala.dizer("Olá! Em que posso ajudar?")
    continuar = True
    while continuar:
        frase = escuta.ouvir() if escuta else input("Você: ")
        if not frase:
            continue
        resposta, continuar = responder(frase, acoes)
        fala.dizer(resposta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
