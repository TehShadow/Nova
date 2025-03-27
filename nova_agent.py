import time
from system_stats import SystemStats
from nova_llm import NovaLLM  

class NovaAgent:
    def __init__(self, llm=None, interval=15):
        self.llm = llm or NovaLLM()
        self.stats = SystemStats()
        self.interval = interval
        self.previous_thought = None

    def generate_internal_prompt(self):
        system_status = {
            "cpu_usage": self.stats.get_cpu_usage(),
            "memory_usage": self.stats.get_memory_usage(),
            "disk_usage": self.stats.get_disk_usage(),
            "uptime": self.stats.get_uptime(),
            "cpu_temp": self.stats.get_cpu_temp(),
            "gpu_temp": self.stats.get_gpu_temp(),
            "gpu_usage": self.stats.get_gpu_usage(),
        }

        memory_context = self.llm.memory.summary()
        status_text = "\n".join(system_status.values())
        memory_text = "\n".join(memory_context)
        prev_thought = f"Previous thought: {self.previous_thought}\n" if self.previous_thought else ""

        internal_prompt = f"""
[internal system check]

Nova, you are thinking independently. Here is your world:

System Status:
{status_text}

User Memory:
{memory_text or 'No memory stored yet.'}

{prev_thought}Your task:
- Decide if anything needs to be done, warned about, or remembered.
- You may call a function, say something, remember a fact, or do nothing.

If everything is fine, respond with:
{{ "type": "text", "response": "All good for now." }}
"""
        return internal_prompt

    def run(self):
        print("🧠 Nova autonomous agent is active. Monitoring system and thinking...")
        while True:
            internal_prompt = self.generate_internal_prompt()
            result = self.llm.chat(internal_prompt)
            self.previous_thought = result
            if result and "all good" not in result.lower():
                print(f"Nova says: {result}")
                self.llm.speak(result)
            time.sleep(self.interval)