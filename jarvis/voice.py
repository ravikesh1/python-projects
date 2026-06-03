"""Optional voice I/O for JARVIS.

Speech-to-text via SpeechRecognition (Google Web Speech) and text-to-speech via
pyttsx3 (offline). These pull in extra system/audio dependencies, so they are an
optional extra: install with ``uv sync --extra voice`` (or ``pip install
'jarvis[voice]'``). Imports are lazy so the text CLI works without them.
"""

from __future__ import annotations

VOICE_INSTALL_HINT = (
    "Voice mode needs extra packages. Install them with:\n"
    "    uv sync --extra voice\n"
    "and ensure your OS has microphone/audio support (PortAudio, espeak, etc.)."
)


class VoiceIO:
    """Thin wrapper around a microphone (STT) and a speech engine (TTS)."""

    def __init__(self) -> None:
        try:
            import pyttsx3  # noqa: F401
            import speech_recognition as sr  # noqa: F401
        except ImportError as exc:  # pragma: no cover - depends on env
            raise RuntimeError(VOICE_INSTALL_HINT) from exc

        import pyttsx3
        import speech_recognition as sr

        self._sr = sr
        self._recognizer = sr.Recognizer()
        self._engine = pyttsx3.init()

    def speak(self, text: str) -> None:
        """Say ``text`` aloud (blocking)."""
        if not text:
            return
        self._engine.say(text)
        self._engine.runAndWait()

    def listen(self, timeout: float | None = None, phrase_time_limit: float = 15.0) -> str:
        """Capture one utterance from the default microphone and transcribe it.

        Returns the recognised text, or an empty string if nothing intelligible
        was heard.
        """
        with self._sr.Microphone() as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.4)
            try:
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            except self._sr.WaitTimeoutError:
                return ""

        try:
            return self._recognizer.recognize_google(audio)
        except self._sr.UnknownValueError:
            return ""
        except self._sr.RequestError:
            # Network/transcription backend unavailable.
            return ""
