"""As funções que os comandos de voz disparam.

A rede (requests) e o navegador (webbrowser.open) entram como parâmetros, para que os
testes possam trocar os dois por versões falsas sem abrir nada de verdade.
"""

import math
import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote, quote_plus

import requests

USER_AGENT = "assistente-virtual-estudo/1.0 (projeto de estudo)"
Abrir = Callable[[str], object]


@dataclass
class Acoes:
    http: requests.Session
    abrir: Abrir = webbrowser.open
    local_padrao: str = "Praça da Sé, São Paulo"
    # A política de uso do Nominatim pede no máximo uma requisição por segundo.
    pausa_s: float = 1.0

    @classmethod
    def padrao(cls, local_padrao: str | None = None) -> "Acoes":
        sessao = requests.Session()
        sessao.headers["User-Agent"] = USER_AGENT
        return cls(http=sessao, local_padrao=local_padrao or cls.local_padrao)

    # Wikipedia --------------------------------------------------------------------
    def wikipedia(self, assunto: str) -> str:
        """Lê o resumo do artigo e abre a página no navegador."""
        if not assunto:
            return "Sobre o que você quer pesquisar?"
        busca = self.http.get(
            "https://pt.wikipedia.org/w/api.php",
            params={"action": "opensearch", "search": assunto, "limit": 1, "format": "json"},
            timeout=10,
        )
        busca.raise_for_status()
        titulos = busca.json()[1]
        if not titulos:
            return f"Não encontrei nada sobre {assunto} na Wikipédia."
        titulo = titulos[0]
        resumo = self.http.get(f"https://pt.wikipedia.org/api/rest_v1/page/summary/{quote(titulo.replace(' ', '_'))}", timeout=10)
        resumo.raise_for_status()
        dados = resumo.json()
        self.abrir(dados.get("content_urls", {}).get("desktop", {}).get("page", f"https://pt.wikipedia.org/wiki/{quote(titulo)}"))
        # Só a primeira frase: um parágrafo inteiro é longo demais para ouvir.
        primeira_frase = dados.get("extract", "").split(". ")[0].rstrip(".")
        return f"{primeira_frase}." if primeira_frase else f"Abri o artigo sobre {titulo}."

    # YouTube ----------------------------------------------------------------------
    def youtube(self, assunto: str) -> str:
        if assunto:
            self.abrir(f"https://www.youtube.com/results?search_query={quote_plus(assunto)}")
            return f"Abrindo o YouTube com resultados para {assunto}."
        self.abrir("https://www.youtube.com")
        return "Abrindo o YouTube."

    # Farmácia ---------------------------------------------------------------------
    def geocodificar(self, local: str) -> tuple[float, float] | None:
        resposta = self.http.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": local, "format": "json", "limit": 1, "countrycodes": "br"},
            timeout=10,
        )
        resposta.raise_for_status()
        resultados = resposta.json()
        if not resultados:
            return None
        return float(resultados[0]["lat"]), float(resultados[0]["lon"])

    def farmacias_ao_redor(self, lat: float, lon: float, raio_m: int) -> list[dict]:
        """Farmácias do OpenStreetMap dentro de um quadrado de lado 2·raio em volta do ponto."""
        dlat = raio_m / 111_320
        dlon = raio_m / (111_320 * math.cos(math.radians(lat)))
        resposta = self.http.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "amenity": "pharmacy",
                "format": "json",
                "limit": 40,
                "bounded": 1,
                "viewbox": f"{lon - dlon},{lat + dlat},{lon + dlon},{lat - dlat}",
            },
            timeout=10,
        )
        resposta.raise_for_status()
        return resposta.json()

    def farmacia(self, local: str) -> str:
        """Acha a farmácia mais próxima do local, pela distância em linha reta, e abre no mapa."""
        local = local or self.local_padrao
        origem = self.geocodificar(local)
        if origem is None:
            return f"Não consegui localizar {local}."
        lat, lon = origem

        # Começa com um raio pequeno e só amplia se não achar nada: a busca devolve no
        # máximo 40 resultados sem ordem de distância, então um raio grande demais
        # poderia deixar a mais próxima de fora.
        for raio in (500, 1000, 2000, 5000):
            time.sleep(self.pausa_s)
            encontradas = self.farmacias_ao_redor(lat, lon, raio)
            if encontradas:
                break
        else:
            return f"Não achei farmácias num raio de 5 km de {local}."

        mais_proxima = min(encontradas, key=lambda f: distancia_metros(lat, lon, float(f["lat"]), float(f["lon"])))
        distancia = distancia_metros(lat, lon, float(mais_proxima["lat"]), float(mais_proxima["lon"]))
        nome = mais_proxima.get("name") or "uma farmácia sem nome no mapa"
        plat, plon = mais_proxima["lat"], mais_proxima["lon"]
        self.abrir(f"https://www.openstreetmap.org/?mlat={plat}&mlon={plon}#map=18/{plat}/{plon}")
        return f"A farmácia mais próxima de {local} é {nome}, a {formatar_distancia(distancia)}."


def distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em linha reta sobre a superfície da Terra (fórmula de haversine)."""
    raio_terra = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * raio_terra * math.asin(math.sqrt(a))


def formatar_distancia(metros: float) -> str:
    if metros < 1000:
        return f"{round(metros / 10) * 10:.0f} metros"
    return f"{metros / 1000:.1f} quilômetros".replace(".", ",")
