from monitor.ai_companion_engine import ask_ai

if __name__ == "__main__":

    print("🧠 AI Chat Test Started\n")

    while True:
        question = input("You: ")

        if question.lower() in ["exit", "quit"]:
            break

        reply = ask_ai(question)

        print("\nAI:", reply)
        print("-" * 50)
