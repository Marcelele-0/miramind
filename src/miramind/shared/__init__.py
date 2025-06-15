from openai import AzureOpenAI
from dotenv import load_dotenv
import os


class MyClient:
    @staticmethod
    def get():
        load_dotenv()
        return AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT_URL"],
                           api_key=os.environ["AZURE_OPENAI_API_KEY"],
                           api_version=os.environ["AZURE_OPENAI_API_VERSION"])
    