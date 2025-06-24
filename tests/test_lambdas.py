import os
import json
import base64
import sys
import types

# Stub external deps if not installed
sys.modules.setdefault('boto3', types.SimpleNamespace(client=lambda *a, **k: None))
sys.modules.setdefault('requests', types.SimpleNamespace(post=lambda *a, **k: types.SimpleNamespace(raise_for_status=lambda: None, json=lambda: {}), get=lambda *a, **k: types.SimpleNamespace(raise_for_status=lambda: None, json=lambda: {})))

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "marktplaats-backend"))

import generate_listing_lambda as gl
import place_listing_lambda as pl


def test_generate_listing_lambda_success(monkeypatch):
    event = {"body": json.dumps({"image": base64.b64encode(b"data").decode()})}

    monkeypatch.setattr(gl, "extract_labels_and_text", lambda image: (["bike"], ["test"]))
    monkeypatch.setattr(gl, "generate_listing_with_bedrock", lambda labels, text: {
        "title": "Bike",
        "description": "A nice bike",
        "category": "Fietsen > Racefietsen",
        "attributes": {"color": "red"}
    })
    monkeypatch.setattr(gl, "fetch_marktplaats_categories", lambda: [])
    monkeypatch.setattr(gl, "flatten_categories", lambda cats: [{"name": "Fietsen > Racefietsen", "id": 123}])
    monkeypatch.setattr(gl, "match_category_name", lambda name, flat: {"match": "Fietsen > Racefietsen", "categoryId": 123})
    monkeypatch.setattr(gl, "fetch_category_attributes", lambda cid: [])
    monkeypatch.setattr(gl, "map_ai_attributes_to_marktplaats", lambda attrs, mp: [{"id": 1, "value": "red"}])

    resp = gl.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["title"] == "Bike"
    assert body["categoryId"] == 123
    assert body["attributes"] == [{"id": 1, "value": "red"}]


def test_place_listing_lambda_success(monkeypatch):
    event = {"body": json.dumps({"title": "Bike"})}
    monkeypatch.setattr(pl, "create_marktplaats_listing", lambda listing: {"ok": True})

    resp = pl.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    assert json.loads(resp["body"]) == {"ok": True}
