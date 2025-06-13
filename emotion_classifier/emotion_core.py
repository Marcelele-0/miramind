import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=openai_api_key)

# Classifing emotions for the first phase of project. Later we will incrase temperature and delete hardcoded emotions
emotion_prompt = PromptTemplate.from_template("""
You are an expert in understanding the emotional tone of children's messages.

Classify the primary emotion of the following text. Choose only from:
["happy", "curious", "tired", "anxious", "upset", "overstimulated", "stressed", "sad", "lonely", "neutral"]

Text: "{input}"

Answer with only the emotion.
""")

def classify_emotion(text: str) -> str:
    prompt = emotion_prompt.format(input=text)
    response = llm.predict(prompt)
    return response.strip().lower()
