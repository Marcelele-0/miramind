from miramind.llm.langgraph.chatbot import chatbot
import sys
import json
import os

# Define the path where the output.wav should be saved inside frontend/public
OUTPUT_AUDIO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "output.wav")
OUTPUT_AUDIO_PATH = os.path.abspath(OUTPUT_AUDIO_PATH)

def process_chat_message(user_input_text: str, chat_history: list = []):
    """
    Processes a single chat message using the chatbot and saves the response audio.

    Args:
        user_input_text: The text message from the user.
        chat_history: A list of previous chat turns (optional, for continuity).

    Returns:
        A dictionary containing 'response_text' and 'audio_file_path' if successful.
    """
    state = {"chat_history": chat_history, "user_input": user_input_text}

    try:
        # Invoke the chatbot with the current state
        state = chatbot.invoke(state)

        response_text = state.get("response")
        audio_data = state.get("response_audio")

        if audio_data:
            os.makedirs(os.path.dirname(OUTPUT_AUDIO_PATH), exist_ok=True)
            with open(OUTPUT_AUDIO_PATH, "wb") as f:
                f.write(audio_data)
            print(f" Response audio saved to {OUTPUT_AUDIO_PATH}")
            return {
                "response_text": response_text,
                "audio_file_path": OUTPUT_AUDIO_PATH
            }
        else:
            print(" No audio generated.")
            return {
                "response_text": response_text,
                "audio_file_path": None
            }
    except Exception as e:
        print(f"Error processing chat message: {e}", file=sys.stderr)
        return {
            "response_text": "I'm sorry, I couldn't process that.",
            "audio_file_path": None
        }


if __name__ == "__main__":
    # This block allows run_chat.py to be called from the command line with JSON input
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.argv[1])
            user_input = input_data.get("text", "")
            # Assuming you might want to pass chat_history for continuity
            chat_history_from_input = input_data.get("chat_history", [])

            result = process_chat_message(user_input, chat_history_from_input)
            print(json.dumps(result)) # Print result as JSON for the calling process to parse
        except json.JSONDecodeError:
            print("Error: Invalid JSON input.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Original interactive mode (optional, useful for testing standalone)
        print(" Emotion-Aware Chatbot for Neurodivergent Kids")
        print("Type 'exit' to quit.\n")

        # In a real application, we will load/save chat history from a database or session
        current_chat_history = []

        while True:
            user_input = input("Child: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Chatbot: It was great talking to you. Bye!")
                break

            result = process_chat_message(user_input, current_chat_history)
            print("Chatbot:", result["response_text"])
            # Update chat history for subsequent turns (if your chatbot system needs it)
            current_chat_history.append({"human": user_input, "ai": result["response_text"]})

            # The audio saving is already handled within process_chat_message
            if result["audio_file_path"]:
                print(f" Audio saved to {result['audio_file_path']}")
