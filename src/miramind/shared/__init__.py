from openai import AzureOpenAI
from dotenv import load_dotenv
import os


class s:
    pass

S = s()


class a:
    pass

A = a()


class u:
    pass

U = u()


def msg(role, message):
    role_str = None
    if isinstance(role, s):
        role_str = "system"
    elif isinstance(role, a):
        role_str = "assistant"
    elif isinstance(role, u):
        role_str = "user"

    return_val = {"role": role_str, "content": message}
    return return_val


class MyClient:
    @staticmethod
    def get():
        load_dotenv()
        return AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT_URL"],
                           api_key=os.environ["AZURE_OPENAI_API_KEY"],
                           api_version=os.environ["AZURE_OPENAI_API_VERSION"])
    