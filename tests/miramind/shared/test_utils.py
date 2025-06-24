from shared.utils import get_azure_openai_client
from openai import AzureOpenAI


def test_get_azure_openai():
    my_clint = get_azure_openai_client()
    assert isinstance(my_clint, AzureOpenAI)
