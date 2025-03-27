from Voice_rec import AI


if __name__ == "__main__":
    nova = AI()
    nova.speak("Hi, I am Nova, your Neural Optimized Virtual Assistant. How can I assist you today?")
    nova.recognize_speech_live()
