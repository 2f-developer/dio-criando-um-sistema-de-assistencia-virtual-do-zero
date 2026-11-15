# Assistente virtual por voz

Assistente em português feito para o desafio "Criando um Sistema de Assistência Virtual do Zero", da formação Machine Learning Specialist da DIO. O desafio pede:

1. um módulo de **texto para fala** (text to speech);
2. um módulo de **fala para texto** (speech to text);
3. comandos de voz que disparem funções automatizadas, como **pesquisar na Wikipédia**, **abrir o YouTube** e **mostrar a farmácia mais próxima**.

Os exemplos de referência do curso são [Text-to-Speech-DIO](https://github.com/diegobrunoDIO/Text-to-Speech-DIO) e [Speech-to-text-ML-DIO](https://github.com/diegobrunoDIO/Speech-to-text-ML-DIO).

## O que ele faz

```
Assistente: Olá! Em que posso ajudar?
Você: o que é fotossíntese
Assistente: Fotossíntese é o processo pelo qual plantas, algas e algumas bactérias captam parte da energia da luz e a guardam em substâncias orgânicas.
Você: farmácia mais próxima da Avenida Paulista, 1000
Assistente: A farmácia mais próxima de avenida paulista 1000 é Drogasil, a 60 metros.
```

| Diga algo como | O que acontece |
| --- | --- |
| "o que é…", "quem foi…", "pesquise sobre…" | lê a primeira frase do artigo da Wikipédia e abre a página |
| "abra o YouTube", "toque lofi para estudar" | abre o YouTube, já com a busca quando houver assunto |
| "farmácia mais próxima", "…da Avenida Paulista" | encontra a farmácia mais perto e abre o ponto no mapa |
| "que horas são" | diz a hora |
| "ajuda", "tchau" | explica os comandos / encerra |

## Como funciona

**Fala para texto.** `assistente/voz.py` usa a biblioteca **SpeechRecognition**, a principal do curso: ajusta o ruído ambiente, escuta o microfone e transcreve com o reconhecimento do Google em pt-BR.

**Texto para fala.** Usa o **pyttsx3**, que fala sem internet, usando o motor de voz do sistema (eSpeak no Linux, SAPI no Windows). Tudo que é falado também aparece escrito.

**Entender o pedido (PLN).** `assistente/intencoes.py` normaliza a frase (minúsculas, sem acento, sem pontuação) e aplica regras que separam a **intenção** do **assunto**. "Qual a farmácia mais perto da Avenida Paulista?" vira `farmacia` + `avenida paulista`. A normalização faz o reconhecimento de voz funcionar mesmo quando a transcrição vem sem acento ou com pontuação diferente.

**Farmácia mais próxima de verdade.** O endereço é convertido em coordenadas pelo Nominatim (OpenStreetMap). Em seguida, o assistente busca farmácias num raio de 500 m, ampliando para 1, 2 e 5 km só se não achar nenhuma, e escolhe a mais próxima calculando a distância em linha reta (fórmula de haversine). Não é a primeira que a API devolve: é a mais perto. As chamadas respeitam o limite de uma por segundo do Nominatim.

**Sem internet ou sem microfone**, o assistente avisa e continua funcionando: sem microfone, passa para o modo digitado.

## Rodando

Com Python 3.10 ou mais novo:

```bash
pip install -e '.[voz]'            # inclui SpeechRecognition, PyAudio e pyttsx3
python -m assistente               # por voz
python -m assistente --texto       # digitando
python -m assistente --local "Rua Augusta, São Paulo"   # referência para "farmácia mais próxima"
```

No Linux, o PyAudio e o pyttsx3 precisam de dois pacotes do sistema: `sudo apt install portaudio19-dev espeak-ng`. Sem eles, `pip install -e .` instala só o modo texto.

## Testes

```bash
pip install -e '.[dev]'
pytest
```

Os 26 testes não usam rede, microfone nem navegador: a sessão HTTP e a função que abre páginas são injetadas, e os testes passam versões falsas que registram o que seria aberto. Eles cobrem doze formas diferentes de pedir as coisas, a escolha da farmácia mais próxima (inclusive quando a mais perto não é a primeira da lista), a ampliação do raio, local desconhecido, a busca no YouTube, o resumo da Wikipédia e as respostas sem internet. O GitHub Actions roda lint e testes a cada push.
