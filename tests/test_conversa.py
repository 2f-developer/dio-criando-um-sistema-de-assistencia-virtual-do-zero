from datetime import datetime

import requests

from assistente.__main__ import responder
from assistente.acoes import Acoes


class SemRede:
    def get(self, *args, **kwargs):
        raise requests.ConnectionError("offline")

    post = get


def test_horas_e_saida():
    acoes = Acoes(http=SemRede(), abrir=lambda url: None)
    assert responder("que horas são", acoes, agora=datetime(2026, 1, 1, 9, 5)) == ("Agora são 09:05.", True)
    assert responder("tchau", acoes) == ("Até logo!", False)


def test_sem_internet_responde_com_educacao():
    acoes = Acoes(http=SemRede(), abrir=lambda url: None)
    resposta, continuar = responder("o que é fotossíntese", acoes)
    assert "internet" in resposta
    assert continuar


def test_frase_desconhecida():
    acoes = Acoes(http=SemRede(), abrir=lambda url: None)
    assert responder("bom dia", acoes)[0].startswith("Não entendi")
