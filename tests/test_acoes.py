import pytest
import requests

from assistente.acoes import Acoes, distancia_metros, formatar_distancia


class Resposta:
    def __init__(self, dados, status=200):
        self._dados, self.status_code = dados, status

    def json(self):
        return self._dados

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(self.status_code)


class HttpFalso:
    """Responde por trecho de URL e guarda o que foi pedido."""

    def __init__(self, rotas):
        self.rotas, self.pedidos = rotas, []

    def _responder(self, url, **kwargs):
        self.pedidos.append((url, kwargs))
        chave = "farmacias" if kwargs.get("params", {}).get("amenity") == "pharmacy" else url
        for trecho, resposta in self.rotas.items():
            if trecho in chave:
                return resposta(kwargs) if callable(resposta) else resposta
        raise AssertionError(f"URL inesperada: {url}")

    get = post = _responder


@pytest.fixture
def abertos():
    return []


def acoes_com(rotas, abertos):
    return Acoes(http=HttpFalso(rotas), abrir=abertos.append, pausa_s=0)


def test_distancia_sao_paulo_rio_de_janeiro():
    assert distancia_metros(-23.5505, -46.6333, -22.9068, -43.1729) == pytest.approx(361_000, rel=0.01)


def test_formata_distancia():
    assert formatar_distancia(234) == "230 metros"
    assert formatar_distancia(1530) == "1,5 quilômetros"


def test_farmacia_escolhe_a_mais_proxima_e_abre_no_mapa(abertos):
    origem = {"lat": "-23.5505", "lon": "-46.6333"}
    farmacias = [
        {"lat": "-23.5530", "lon": "-46.6333", "name": "Drogaria Longe"},
        {"lat": "-23.5510", "lon": "-46.6333", "name": "Farmácia Perto"},
        {"lat": "-23.5520", "lon": "-46.6333", "name": ""},
    ]
    acoes = acoes_com({"farmacias": Resposta(farmacias), "nominatim": Resposta([origem])}, abertos)

    resposta = acoes.farmacia("Praça da Sé")

    assert resposta == "A farmácia mais próxima de Praça da Sé é Farmácia Perto, a 60 metros."
    assert abertos == ["https://www.openstreetmap.org/?mlat=-23.5510&mlon=-46.6333#map=18/-23.5510/-46.6333"]


def test_farmacia_amplia_o_raio_ate_achar(abertos):
    raios = []

    def por_raio(kwargs):
        oeste, norte, leste, sul = map(float, kwargs["params"]["viewbox"].split(","))
        raios.append(round((norte - sul) / 2 * 111_320))
        return Resposta([] if len(raios) < 3 else [{"lat": "-23.56", "lon": "-46.63", "name": "Farmácia Distante"}])

    acoes = acoes_com({"farmacias": por_raio, "nominatim": Resposta([{"lat": "-23.5505", "lon": "-46.6333"}])}, abertos)
    assert "Farmácia Distante" in acoes.farmacia("Sé")
    assert raios == [500, 1000, 2000]


def test_farmacia_sem_resultados(abertos):
    acoes = acoes_com({"farmacias": Resposta([]), "nominatim": Resposta([{"lat": "0", "lon": "0"}])}, abertos)
    assert acoes.farmacia("Lugar Ermo") == "Não achei farmácias num raio de 5 km de Lugar Ermo."
    assert abertos == []


def test_local_desconhecido(abertos):
    acoes = acoes_com({"nominatim": Resposta([])}, abertos)
    assert acoes.farmacia("Xyzlândia") == "Não consegui localizar Xyzlândia."


def test_farmacia_sem_local_usa_o_padrao(abertos):
    acoes = acoes_com({"nominatim": Resposta([])}, abertos)
    acoes.farmacia("")
    assert acoes.http.pedidos[0][1]["params"]["q"] == "Praça da Sé, São Paulo"


def test_youtube_monta_a_busca(abertos):
    acoes = acoes_com({}, abertos)
    assert acoes.youtube("lofi & jazz") == "Abrindo o YouTube com resultados para lofi & jazz."
    assert abertos == ["https://www.youtube.com/results?search_query=lofi+%26+jazz"]


def test_wikipedia_le_a_primeira_frase_e_abre_o_artigo(abertos):
    rotas = {
        "w/api.php": Resposta(["python", ["Python"], [""], ["https://pt.wikipedia.org/wiki/Python"]]),
        "page/summary/Python": Resposta(
            {
                "extract": "Python é uma linguagem de programação de alto nível. Foi lançada em 1991.",
                "content_urls": {"desktop": {"page": "https://pt.wikipedia.org/wiki/Python"}},
            }
        ),
    }
    acoes = acoes_com(rotas, abertos)
    assert acoes.wikipedia("python") == "Python é uma linguagem de programação de alto nível."
    assert abertos == ["https://pt.wikipedia.org/wiki/Python"]


def test_wikipedia_sem_resultado(abertos):
    acoes = acoes_com({"w/api.php": Resposta(["xyz", [], [], []])}, abertos)
    assert acoes.wikipedia("xyzzy") == "Não encontrei nada sobre xyzzy na Wikipédia."
