from ai_client import AIClient


def test_extract_standard():
    assert AIClient._extract({"choices": [{"message": {"content": "hello"}}]}) == "hello"


def test_extract_think_strip():
    assert AIClient._extract({"choices": [{"message": {"content": "<think>secret</think>  visible "}}]}) == "visible"


def test_extract_closing_tag_leak():
    assert AIClient._extract({"choices": [{"message": {"content": "inner</think> answer"}}]}) == "answer"


def test_extract_list_content():
    assert AIClient._extract({"choices": [{"message": {"content": [{"text": "a"}, "b"]}}]}) == "ab"


def test_extract_dict_content():
    assert AIClient._extract({"choices": [{"message": {"content": {"text": "hi"}}}]}) == "hi"


def test_extract_bad_input():
    assert AIClient._extract(None) is None
    assert AIClient._extract({}) is None
    assert AIClient._extract({"choices": []}) is None


def test_is_loopback():
    from ai_client import _is_loopback

    assert _is_loopback("http://127.0.0.1:11434/v1") is True
    assert _is_loopback("https://api.example.com/v1") is False
    assert _is_loopback("http://0.0.0.0:8080") is False
