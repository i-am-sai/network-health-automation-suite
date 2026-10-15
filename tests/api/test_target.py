# tests/api/test_targets.py
import requests

BASE = "http://localhost:8000"

def test_create_target_returns_201_and_id():
    r = requests.post(f"{BASE}/targets", json={"url": "https://ebooks.heart.org", "is_cdn": False})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] > 0
    assert body["is_cdn"] is False

def test_get_target_returns_200_and_id():
    r = requests.get(f"{BASE}/targets")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] > 0
    assert body["is_cdn"] is False