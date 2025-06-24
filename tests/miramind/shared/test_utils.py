from shared.utils import get_azure_openai_client, msg, A, U, S
from openai import AzureOpenAI
from dotenv import load_dotenv
import os


def test_msg():
    assert msg(A, "assistnat")["role"] == "assistnat"
    assert msg(S, "system")["role"] == "system"
    assert msg(U, "user")["role"] == "user"


def test_get_azure_openai():
    load_dotenv()
    my_client = get_azure_openai_client()
    messages = [msg(U, "Hi.")]
    my_client.chat.completions.create(
        model=os.environ.get("LANGUAGE_DETECTION_DEPLOYMENT", "gpt-4o"), messages=messages
    )
    assert isinstance(my_client, AzureOpenAI)
