import requests
import json
import subprocess
from datetime import datetime
import re
import os
import wave
import pyaudio
from vosk import Model, KaldiRecognizer
from nova_memory import NovaMemory
import threading

class NovaLLM:
    def __init__(self, model="mistral", url="http://localhost:11434/api/generate"):
        self.model = model
        self.url = url
        self.memory = NovaMemory()
        self.memory_lock = threading.Lock()
        self.speech_lock = threading.Lock()

        self.FUNCTIONS = {
            "get_time": self.get_time,
            "get_date": self.get_date,
            "open_firefox": self.open_firefox
        }

        function_descriptions = "\n".join([
            f"- {name}({', '.join(f'{param}' for param in func.__code__.co_varnames[:func.__code__.co_argcount])})"
            for name, func in self.FUNCTIONS.items()
        ])

        self.history = [
            {
                "role": "system",
                "content": f"""
You are Nova, an offline virtual assistant with a friendly and confident personality.
You may speak with charm and warmth, but always reply in strict JSON.

You can call the following functions:
{function_descriptions}

Respond using one of these formats:

1. Function call:
{{
  "type": "function",
  "function": "function_name",
  "args": {{ "arg": "value" }}
}}

2. Text response:
{{
  "type": "text",
  "response": "your reply here"
}}

3. Memory instruction:
{{
  "type": "memory",
  "key": "something_to_remember",
  "value": "value"
}}

Always return valid JSON. Never return anything else. No markdown, no explanations.
"""
            }
        ]

        self.PIPER_MODEL = "piper_models/en_US-libritts-high.onnx"
        self.PIPER_CONFIG = "piper_models/en_US-libritts-high.onnx.json"
        self.VOSK_MODEL = "vosk_models/vosk-model-en-us-0.42-gigaspeech"

        self.SAMPLE_RATE = 16000
        self.CHUNK_SIZE = 4000

        if not os.path.exists(self.VOSK_MODEL):
            raise FileNotFoundError("Vosk model not found! Make sure to download it.")
        self.vosk_model = Model(self.VOSK_MODEL)
        self.recognizer = KaldiRecognizer(self.vosk_model, self.SAMPLE_RATE)

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, 
                                      rate=self.SAMPLE_RATE, input=True,
                                      frames_per_buffer=self.CHUNK_SIZE)
        self.stream.start_stream()

    def speak(self, text):
        if not os.path.exists(self.PIPER_MODEL) or not os.path.exists(self.PIPER_CONFIG):
            print("Missing Piper model or config.")
            return

        with self.speech_lock:
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
        print("🎙️ Nova is listening... Say something!")
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

                    response = self.chat(text)
                    print(f"LLM Response: {response}")
                    self.speak(response)

    def get_time(self, time="now"):
        return f"The current time is {datetime.now().strftime('%H:%M:%S')}."

    def get_date(self):
        from datetime import date
        return f"Today is {date.today().strftime('%A, %B %d, %Y')}."

    def open_firefox(self):
        try:
            subprocess.Popen(["firefox"])
            return "Opening Firefox... launching you into the webiverse!"
        except Exception as e:
            return f"Hmm, I tried but couldn't open Firefox: {e}"

    def chat(self, user_input):
        self.history.append({"role": "user", "content": user_input})
        prompt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in self.history)

        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }).json()["response"]

            self.history.append({"role": "assistant", "content": response})
            return self.handle_response(response)

        except Exception as e:
            return f"❌ Error talking to LLM: {e}"

    def handle_response(self, response):
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'{.*}', response, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(0))
                except:
                    return "❌ Error: Invalid JSON inside messy response."
            else:
                return "❌ Error: Invalid JSON response."

        response_type = result.get("type")

        if response_type == "function":
            func_name = result.get("function")
            args = result.get("args", {})
            if func_name in self.FUNCTIONS:
                return self.FUNCTIONS[func_name](**args)
            else:
                return f"⚠️ Unknown function '{func_name}'"

        elif response_type == "text":
            return result.get("response", "")

        elif response_type == "memory":
            key = result.get("key")
            value = result.get("value")
            if key and value:
                with self.memory_lock:
                    self.memory.remember(key, value)
                return f"Got it! I'll remember that {key} is {value}."
            else:
                return "⚠️ Memory format incomplete."

        else:
            return "⚠️ Invalid response type."
