from miramind.shared.utils import A, S, U, get_azure_openai_client, msg


def test_msg():
    assert msg(A, "assistant")["role"] == "assistant"
    assert msg(S, "system")["role"] == "system"
    assert msg(U, "user")["role"] == "user"
