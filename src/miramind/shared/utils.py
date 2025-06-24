from openai import AzureOpenAI
from dotenv import load_dotenv
import os


S, U, A = object(), object(), object()


def msg(role, message):
    role_dict = {S: "system", U: "user", A: "assistnat"}
    return_val = {"role": role_dict[role], "content": message}
    return return_val


def get_azure_openai_client():
    return AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT_URL"],
                       api_key=os.environ["AZURE_OPENAI_API_KEY"],
                       api_version=os.environ["AZURE_OPENAI_API_VERSION"])
    