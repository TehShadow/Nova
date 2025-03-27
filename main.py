from nova_llm import NovaLLM
from nova_agent import NovaAgent
import threading

if __name__ == "__main__":
    nova = NovaLLM()
    agent = NovaAgent(llm=nova)

    # Thread 1: Speech interface
    t1 = threading.Thread(target=nova.recognize_speech_live)

    # Thread 2: Background agent
    t2 = threading.Thread(target=agent.run)

    print("🚀 Starting Nova (voice + background agent)...")

    t1.start()
    t2.start()

    t1.join()
    t2.join()