from chatbot import chatbot

print("🤖 Emotion-Aware Chatbot for Neurodivergent Kids")
print("Type 'exit' to quit.\n")

state = {"chat_history": []}

while True:
    user_input = input("Child: ").strip()
    if user_input.lower() in {"exit", "quit"}:
        print("Chatbot: It was great talking to you. Bye! 👋")
        break

    state["user_input"] = user_input
    state = chatbot.invoke(state)
    print("Chatbot:", state["response"])
