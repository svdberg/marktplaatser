import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "marktplaats_backend"))

import marktplaats_auth as auth


def test_get_authorization_url():
    os.environ["MARKTPLAATS_CLIENT_ID"] = "client-id"
    url = auth.get_authorization_url("http://localhost/callback", "abc", "default")
    assert "client_id=client-id" in url
    assert "redirect_uri=http://localhost/callback" in url
    assert url.startswith(auth.AUTH_BASE_URL)


@patch("marktplaats_backend.marktplaats_auth.requests.post")
def test_exchange_code_for_tokens(mock_post):
    os.environ["MARKTPLAATS_CLIENT_ID"] = "client-id"
    os.environ["MARKTPLAATS_CLIENT_SECRET"] = "secret"
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "token", "refresh_token": "ref"}
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    tokens = auth.exchange_code_for_tokens("code", "http://localhost/callback")

    assert tokens["access_token"] == "token"
    mock_post.assert_called_once()
