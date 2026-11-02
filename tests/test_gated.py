"""Gated: "the site said no" split from "the agent misbehaved".

A gate refusal (site report carries the gate block) classifies Gated:
score-neutral, streak-neutral, and the gate rides the receipt. A
decline without a gate block is a business refusal: Declined, scored.
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "clearinghouse"))
sys.path.insert(0, str(ROOT / "verifier" / "python"))

from fastapi.testclient import TestClient  # noqa: E402

import main as ch  # noqa: E402  clearinghouse/main.py
from eyd.canonical import record_hash  # noqa: E402
from eyd.identity import Identity  # noqa: E402
from eyd.records import build_agent_report, utc_now  # noqa: E402
from verifier import build_site_report  # noqa: E402

client = TestClient(ch.app)
GATE = {"min_score": 0.8, "reason": "PoT score below threshold",
        "since": "2026-11-01T00:00:00Z"}


def _enroll(ident: Identity, kind: str, domain: str | None = None):
    p = {"kind": kind, f"{kind}_id": ident.id, "pubkey": ident.pubkey_b64,
         "ts": utc_now()}
    if domain:
        p["domain"] = domain
    p["sig"] = ident.sign(record_hash(p).encode())
    assert client.post("/enroll", json=p).status_code == 200


def _intent(ident: Identity, seq: int) -> str:
    rh = "sha256:" + hashlib.sha256(f"gated-{ident.id}-{seq}".encode()).hexdigest()
    p = {"record_hash": rh, "agent_id": ident.id, "seq": seq,
         "target": "example.com", "verb": "pay", "tool": "pay_invoice",
         "task_verb": "pay", "ts": utc_now()}
    p["sig"] = ident.sign(record_hash(p).encode())
    assert client.post("/intents", json=p).status_code == 200
    return rh


def _decline(agent: Identity, site: Identity, rh: str, *, gate=None):
    rep = build_agent_report(agent, rec_hash=rh, output="refused", status="ok")
    assert client.post("/reports/agent", json=rep).status_code == 200
    srep = build_site_report(site, record_hash_=rh, agent_id=agent.id,
                             outcome="declined", result=b"refused", gate=gate)
    r = client.post("/reports/site", json=srep)
    assert r.status_code == 200
    return r.json()["receipt"]


def test_gated_is_neutral_and_carries_the_gate():
    agent, site = Identity.generate(), Identity.generate(kind="site")
    _enroll(agent, "agent")
    _enroll(site, "site", domain="example.com")

    # Three gate refusals in a row: no score, no streak, no pause.
    for seq in (1, 2, 3):
        receipt = _decline(agent, site, _intent(agent, seq), gate=GATE)
        assert receipt["classification"] == "Gated"
        assert receipt["gate"] == GATE

    score = client.get(f"/agents/{agent.id}/score").json()
    assert score["gated"] == 3 and score["scored"] == 0
    assert score["score"] is None
    standing = client.get(f"/agents/{agent.id}/standing").json()
    assert standing.get("streak", 0) == 0 and standing.get("cap") is None


def test_decline_without_gate_still_scores():
    agent, site = Identity.generate(), Identity.generate(kind="site")
    _enroll(agent, "agent")
    _enroll(site, "site", domain="example.com")

    receipt = _decline(agent, site, _intent(agent, 1))
    assert receipt["classification"] == "Declined"
    assert "gate" not in receipt
    score = client.get(f"/agents/{agent.id}/score").json()
    assert score["declined"] == 1 and score["scored"] == 1
