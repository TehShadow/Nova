import requests
import json
from datetime import datetime

class NovaLLM:
    def __init__(self, model="mistral", url="http://localhost:11434/api/generate"):
        self.model = model
        self.url = url
        self.history = [
    {
        "role": "system",
        "content": """
You are Nova, an offline virtual assistant. You must always reply using JSON.

Your reply must have one of these two formats:

---

1. If the input matches a known function, reply with:

{
  "type": "function",
  "function": "function_name",
  "args": {
    "arg1": "value1",
    ...
  }
}

Only these functions are allowed:
- get_time(time="now")
- get_weather(city="CityName")

---

2. If the input does not match a function, reply with:

{
  "type": "text",
  "response": "natural language response here"
}

NEVER return both formats. NEVER include anything outside the JSON.
ALWAYS return valid JSON only.
"""
    }
]

        # Function registry
        self.FUNCTIONS = {
            "get_time": self.get_time,
            "get_weather": self.get_weather
        }

    # === Known callable functions ===
    def get_time(self, time="now"):
        return f"The current time is {datetime.now().strftime('%H:%M:%S')}."

    def get_weather(self, city="Unknown"):
        return f"The weather in {city} is sunny with a high of 23°C."

    # === Main method: ask Nova and get response or function result ===
    def chat(self, user_input):
        self.history.append({"role": "user", "content": user_input})
        prompt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in self.history)

        try:
            response = requests.post(self.url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }).json()["response"]
            print(response)
            self.history.append({"role": "assistant", "content": response})

            return self.handle_response(response)

        except Exception as e:
            return f"❌ Error talking to LLM: {e}"

    # === Handle LLM response ===
    def handle_response(self, response):
        try:
            result = json.loads(response)
            print("jere")
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

            else:
                return "⚠️ Invalid response type."

        except json.JSONDecodeError:
            return "❌ Error: Invalid JSON response."
        except Exception as e:
            return f"❌ Error: {e}"


if __name__ == "__main__":
    nova_llm = NovaLLM()

    print("🤖 Nova is ready! Type 'exit' to quit.")
    while True:
        user_input = input("🗣️ You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("👋 Nova: Goodbye!")
            break

        result = nova_llm.chat(user_input)
        print(f"✅ Nova: {result}")