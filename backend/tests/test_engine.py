import os, pytest
os.chdir(os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from app.main import app
import app.db as d


@pytest.fixture()
def c(tmp_path):
    d.engine.dispose()
    if os.path.exists("kirana.db"): os.remove("kirana.db")
    with TestClient(app) as client:
        yield client


def cmd(c, t): return c.post("/api/voice/command", json={"transcript": t}).json()
def stock(c, n): return next(p["quantity"] for p in c.get("/api/products").json() if p["name"] == n)


def test_add_check_sell_undo(c):
    assert cmd(c, "Maggi ke 10 packet add karo")["status"] == "clarify"  # Maggi 70g vs 140g
    assert cmd(c, "chhota maggi ke 10 packet add karo")["status"] == "ok"
    assert stock(c, "Maggi 70g") == 30
    assert "30" in cmd(c, "chhota maggi kitna hai")["message"]
    assert cmd(c, "5 packet chhota maggi becha")["status"] == "ok"
    assert stock(c, "Maggi 70g") == 25
    assert cmd(c, "undo my last stock update")["status"] == "ok"
    assert stock(c, "Maggi 70g") == 30
    assert len(c.get("/api/transactions").json()) == 3  # history preserved


def test_rejections(c):
    assert cmd(c, "sell 50 packet chhota maggi")["status"] == "rejected"
    assert cmd(c, "sell 2 packet pizza")["reason"] == "unknown_product"
    assert cmd(c, "sell 2 kg chhota maggi")["reason"] == "unit_mismatch"
    assert stock(c, "Maggi 70g") == 20


def test_decimal_and_confirm(c):
    assert cmd(c, "2.5 kg chawal becha")["status"] == "ok" and stock(c, "Rice") == 5.5
    r = cmd(c, "chawal 150 kg add karo")
    assert r["status"] == "needs_confirmation"
    assert c.post(f"/api/voice/confirm/{r['token']}").json()["status"] == "ok"
    assert cmd(c, "low stock batao")["status"] == "ok"
