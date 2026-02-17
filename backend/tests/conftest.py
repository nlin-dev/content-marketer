from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_anthropic_response():
    def _make(text: str):
        msg = MagicMock()
        block = MagicMock()
        block.text = text
        msg.content = [block]
        return msg
    return _make
