from shared.utils import get_azure_openai_client, msg, A, U, S


def test_msg():
    assert msg(A, "assistant")["role"] == "assistant"
    assert msg(S, "system")["role"] == "system"
    assert msg(U, "user")["role"] == "user"
