"""Texto para fala (pyttsx3, offline) e fala para texto (SpeechRecognition).

As bibliotecas de áudio são opcionais: sem elas, o assistente funciona digitando e lendo.
"""


class Fala:
    def __init__(self, velocidade: int = 175) -> None:
        try:
            import pyttsx3

            self._motor = pyttsx3.init()
            self._motor.setProperty("rate", velocidade)
            for voz in self._motor.getProperty("voices"):
                if "pt" in str(voz.languages).lower() or "brazil" in voz.name.lower() or "pt" in voz.id.lower():
                    self._motor.setProperty("voice", voz.id)
                    break
        except Exception:  # sem pyttsx3 ou sem motor de voz no sistema (espeak, SAPI, NSSpeech)
            self._motor = None

    @property
    def disponivel(self) -> bool:
        return self._motor is not None

    def dizer(self, texto: str) -> None:
        print(f"Assistente: {texto}")
        if self._motor:
            self._motor.say(texto)
            self._motor.runAndWait()


class Escuta:
    """Ouve o microfone e transcreve com o reconhecimento de fala do Google (pt-BR)."""

    def __init__(self, idioma: str = "pt-BR") -> None:
        import speech_recognition as sr

        self._sr = sr
        self._reconhecedor = sr.Recognizer()
        self._microfone = sr.Microphone()  # precisa do PyAudio
        self._idioma = idioma
        with self._microfone as fonte:
            self._reconhecedor.adjust_for_ambient_noise(fonte, duration=0.8)

    def ouvir(self) -> str | None:
        print("(ouvindo...)")
        with self._microfone as fonte:
            try:
                audio = self._reconhecedor.listen(fonte, timeout=6, phrase_time_limit=8)
            except self._sr.WaitTimeoutError:
                return None
        try:
            texto = self._reconhecedor.recognize_google(audio, language=self._idioma)
        except self._sr.UnknownValueError:
            return None
        print(f"Você: {texto}")
        return texto
