import pytest

from assistente.intencoes import Intencao, interpretar


@pytest.mark.parametrize(
    ("frase", "esperado"),
    [
        ("O que é inteligência artificial?", Intencao("wikipedia", "inteligencia artificial")),
        ("quem foi Santos Dumont", Intencao("wikipedia", "santos dumont")),
        ("Pesquise sobre buracos negros", Intencao("wikipedia", "buracos negros")),
        ("pesquisar na Wikipédia Machado de Assis", Intencao("wikipedia", "machado de assis")),
        ("abra o YouTube", Intencao("youtube", "")),
        ("abrir o youtube com aulas de python", Intencao("youtube", "aulas de python")),
        ("toque lofi para estudar", Intencao("youtube", "lofi para estudar")),
        ("farmácia mais próxima", Intencao("farmacia", "")),
        ("qual a farmácia mais perto da Avenida Paulista", Intencao("farmacia", "avenida paulista")),
        ("Que horas são?", Intencao("horas", "")),
        ("tchau", Intencao("sair", "")),
        ("ajuda", Intencao("ajuda", "")),
    ],
)
def test_entende_varias_formas_de_pedir(frase, esperado):
    assert interpretar(frase) == esperado


def test_frase_sem_comando():
    assert interpretar("bom dia, tudo bem?").acao == "desconhecida"
