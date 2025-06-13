from emotion_classifier.emotion_core import classify_emotion

def emotion_classifier_node(state: dict) -> dict:
    transcript = state.get("transcript", "")
    predicted_emotion = classify_emotion(transcript)

    return {
        **state,
        "emotion": predicted_emotion,
        "confidence": 1.0
    }
