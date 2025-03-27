import os
import json
import wave
import pyaudio
from vosk import Model, KaldiRecognizer
import subprocess
from llm_server import NovaLLM 

class AI:
    def __init__(self):
        # Paths
        self.PIPER_MODEL = "piper_models/en_US-libritts-high.onnx"
        self.PIPER_CONFIG = "piper_models/en_US-libritts-high.onnx.json"
        self.VOSK_MODEL = "vosk_models/vosk-model-en-us-0.42-gigaspeech"

        # Audio settings
        self.SAMPLE_RATE = 16000
        self.CHUNK_SIZE = 4000

        # Initialize Vosk
        if not os.path.exists(self.VOSK_MODEL):
            raise FileNotFoundError("Vosk model not found! Make sure to download it.")
        self.vosk_model = Model(self.VOSK_MODEL)
        self.recognizer = KaldiRecognizer(self.vosk_model, self.SAMPLE_RATE)

        # Initialize audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, 
                                      rate=self.SAMPLE_RATE, input=True,
                                      frames_per_buffer=self.CHUNK_SIZE)
        self.stream.start_stream()

        # Initialize Nova LLM backend
        self.llm = NovaLLM()

    def speak(self, text):
        if not os.path.exists(self.PIPER_MODEL) or not os.path.exists(self.PIPER_CONFIG):
            print("Missing Piper model or config.")
            return

        try:
            print(f"Nova says: {text}")
            process = subprocess.Popen(
                ["piper", "--model", self.PIPER_MODEL, "--output_file", "output.wav"],
                stdin=subprocess.PIPE
            )
            process.communicate(input=text.encode())

            if not os.path.exists("output.wav") or os.path.getsize("output.wav") == 0:
                print("❌ Piper failed to generate audio.")
                return

            subprocess.run(["play", "output.wav"])

        except Exception as e:
            print(f"Error during TTS synthesis: {e}")

            
    def recognize_speech_live(self):
        print("Listening continuously... Say something!")
        while True:
            data = self.stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                if text:
                    print(f"Recognized: {text}")
                    if text.lower() in ["exit", "quit", "stop listening"]:
                        self.speak("Okay, shutting down.")
                        break

                    response = self.llm.chat(text)
                    print(f"LLM Response: {response}")
                    self.speak(response)