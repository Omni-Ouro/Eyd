"""Omni-Ouro playground — the business side of the EyD beta.

This is what a business installs: the verifier SDK (verifier/python)
in front of three agent-facing actions, checked against the hosted
EyD Clearing House. The human site (omni-ouro.com) is untouched; this
service lives beside it at eyd.omni-ouro.com and is the playground
agents are told to test against.

  GET  /search    open to all — EyD agents that show up still get receipts
  POST /deck      EyD required, any score   (request the pitch deck)
  POST /meeting   EyD required, PoT >= 0.8  (request a meeting)

Everything is sandboxed: requests are recorded on the board below,
nothing is emailed and no calendar invite is ever sent.

Run: PLAYGROUND_PORT=8002 python playground/main.py
Env: CLEARINGHOUSE_URL, CLEARINGHOUSE_PUBLIC_URL (advertised to
     agents in challenge headers when it differs), PLAYGROUND_DOMAIN
     (default localhost),
     PLAYGROUND_PUBLIC_URL (revocation-push callback base),
     PLAYGROUND_KEY_FILE (site identity, persisted).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verifier" / "python"))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402

from eyd.identity import Identity  # noqa: E402
from fastapi_integration import gated  # noqa: E402
from verifier import EyDSite  # noqa: E402

COMPANY = "Omni-Ouro"
PRODUCTS = [
    ("Eyro", "Accountability for AI agents, enforced by the operating system — "
             "the execution layer where the model has no tool access."),
    ("Coven", "Coordination for fleets of agents working the same problem."),
    ("CovenGo", "Coven on the go: lightweight agent coordination."),
    ("Glove", "Egress control — decides what an agent may reach."),
    ("Eyro Mini", "The Eyro execution layer as dedicated hardware."),
    ("EySight", "Native app: watch what your agents are doing."),
    ("DuePulse", "Native app: keep agent work on schedule."),
]
GATES = {
    "search": {"eyd_required": False, "min_score": None},
    "deck": {"eyd_required": True, "min_score": None},
    "meeting": {"eyd_required": True, "min_score": 0.8},
}
GATE_CHANGE_TTL = 900  # dashboard gate changes auto-expire after 15 min


def _site_identity() -> Identity:
    key_file = Path(os.environ.get(
        "PLAYGROUND_KEY_FILE",
        str(Path(__file__).resolve().parent / ".keys" / "site.json")))
    if key_file.exists():
        return Identity.load(key_file)
    ident = Identity.generate(kind="site")
    ident.save(key_file)
    return ident


def make_app(*, clearinghouse_url: str = "http://127.0.0.1:8787",
             identity: Identity | None = None, domain: str = "localhost",
             callback_url: str | None = None,
             public_clearinghouse_url: str | None = None) -> FastAPI:
    site_identity = identity or _site_identity()
    site = EyDSite(site_identity, clearinghouse_url=clearinghouse_url,
                   domain=domain, callback_url=callback_url,
                   public_clearinghouse_url=public_clearinghouse_url)
    site.enroll()
    app = FastAPI(title=f"{COMPANY} — EyD playground")
    app.state.site = site
    app.state.requests: list[dict] = []
    # Dashboard-adjustable gates: copied so runtime changes never touch
    # the module defaults, and stamped when they change (the stamp is
    # what rides Gated receipts as the gate's `since`).
    from eyd.records import utc_now as _now
    app.state.gates = {k: {**v, "since": _now()} for k, v in GATES.items()}

    def _effective(action: str) -> dict:
        """The gate as it stands now: a dashboard change older than
        GATE_CHANGE_TTL has expired back to the code defaults."""
        import time as _time
        gate = app.state.gates[action]
        changed = gate.get("changed_epoch")
        if changed and _time.time() - changed > GATE_CHANGE_TTL:
            gate = {**GATES[action], "since": _now()}
            app.state.gates[action] = gate
        return gate

    def board(agent, action, result, record_hash=None):
        from eyd.records import utc_now
        app.state.requests.append(
            {"ts": utc_now(), "agent": agent, "action": action,
             "result": result, "record_hash": record_hash})

    # The whole gate — attestation, per-action score check, Passport
    # standing, reporting — is the verifier SDK's @gated decorator.
    # What a business writes is the three handlers below.

    @app.get("/", response_class=HTMLResponse)
    def home():
        rows = "".join(
            f"<tr><td>{r['ts']}</td><td>{(r['agent'] or 'anonymous')[:26]}</td>"
            f"<td>{r['action']}</td><td>{r['result']}</td></tr>"
            for r in reversed(app.state.requests[-15:]))
        return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{COMPANY} — EyD playground</title>
<style>body{{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem}}
table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ddd;padding:.3rem .5rem;text-align:left}}
code{{background:#f2f2f2;padding:.1rem .3rem}}</style></head><body>
<h1>{COMPANY} — EyD beta playground</h1>
<p>This is a real business endpoint running the EyD verifier SDK against the
hosted <b>EyD Clearing House</b>. Point an EyD agent at it and test:</p>
<table><tr><th>Action</th><th>Gate</th></tr>
<tr><td><code>GET /search</code></td><td>open — EyD agents still earn receipts</td></tr>
<tr><td><code>POST /deck</code></td><td>EyD required, any PoT score</td></tr>
<tr><td><code>POST /meeting</code></td><td>EyD required, PoT score &ge; {_effective('meeting')['min_score']} (live value; dashboard changes auto-expire after 15 min)</td></tr></table>
<p>Everything is sandboxed: requests are recorded, nothing is emailed, no
calendar invite is sent. Site identity: <code>{site_identity.id}</code> ·
Clearinghouse: <code>{site.clearinghouse_url}</code></p>
<h2>Recent requests</h2>
<table><tr><th>time (UTC)</th><th>agent</th><th>action</th><th>result</th></tr>
{rows or '<tr><td colspan="4">No requests yet — be the first.</td></tr>'}
</table></body></html>"""

    @app.post("/revocation-notice")
    async def revocation_notice(request: Request):
        """Push from the clearinghouse: an agent's Passport standing
        changed. Drop its sessions now, not at expiry."""
        payload = await request.json()
        dropped = site.drop_sessions(payload.get("agent_id", ""))
        board(payload.get("agent_id"), "—",
              f"revocation notice: {dropped} session(s) dropped")
        return {"dropped_sessions": dropped}

    @app.get("/dashboard/data")
    def dashboard_data(agent: str | None = None):
        """Everything the business dashboard shows: current gates, this
        site's request list (filterable by agent), each request joined
        to the receipt the Clearing House issued for it, and — for one
        agent — that agent's full receipt history at the Clearing
        House, this site and every other."""
        # Join against the Clearing House's receipts, not just the ones
        # this process happened to see issued: a site report often
        # lands before the agent's report, so the receipt is minted
        # after our report() returned.
        by_hash = {r.get("record_hash"): r for r in site.receipts}
        for r in site.clearinghouse_receipts():
            if r.get("site_id") == site_identity.id:
                by_hash[r.get("record_hash")] = r
        rows = []
        for req in app.state.requests:
            if agent and req.get("agent") != agent:
                continue
            receipt = by_hash.get(req.get("record_hash") or "")
            rows.append({**req,
                         "classification": (receipt or {}).get("classification"),
                         "receipt": receipt})
        history = None
        if agent:
            history = site.clearinghouse_receipts(agent)
        return {"company": COMPANY, "site_id": site_identity.id,
                "clearinghouse": site.clearinghouse_url,
                "gates": {k: _effective(k) for k in app.state.gates}, "requests": rows,
                "agent_history": history,
                "scores_seen": site.scores}

    @app.post("/dashboard/gates")
    async def dashboard_gates(request: Request):
        """Adjust a gate at runtime: the next request is checked
        against the new value, and Gated receipts stamp the change.
        This is a test playground, so a change is a test change: it
        auto-expires back to the defaults after GATE_CHANGE_TTL
        seconds, so no tester inherits another tester's moved gate
        for long. (A production install puts this endpoint behind
        the business's own login instead.)"""
        payload = await _json_body(request)
        action = payload.get("action")
        import time as _time
        from eyd.records import utc_now
        if payload.get("reset"):
            app.state.gates = {k: {**v, "since": utc_now()}
                               for k, v in GATES.items()}
            return {"gates": app.state.gates}
        if action not in app.state.gates:
            return {"error": "unknown action"}
        gate = app.state.gates[action]
        if "min_score" in payload:
            gate["min_score"] = payload["min_score"]  # float 0..1, null = any
        if "eyd_required" in payload:
            gate["eyd_required"] = bool(payload["eyd_required"])
        gate["since"] = utc_now()
        gate["changed_epoch"] = _time.time()
        return {"gates": app.state.gates}

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard():
        return _DASHBOARD_HTML.replace("__SITE__", site_identity.id)

    # Fulfilled playground results are fixed-shape confirmations, so
    # the site honestly attests they match the model expectation
    # registered for the action (vector two) — signed, so the claim
    # itself is evidence.
    @app.get("/search")
    @gated(site, eyd_required=False, on_event=board, expectation_match=True)
    async def search(request: Request, q: str = ""):
        return _action_body("search", {"need": q})

    @app.post("/deck")
    @gated(site, min_score=lambda: _effective("deck")["min_score"],
           on_event=board, info_url=callback_url, expectation_match=True,
           gate_since=lambda: _effective("deck")["since"])
    async def deck(request: Request):
        return _action_body("deck", await _json_body(request))

    @app.post("/meeting")
    @gated(site, min_score=lambda: _effective("meeting")["min_score"],
           on_event=board, info_url=callback_url, expectation_match=True,
           gate_since=lambda: _effective("meeting")["since"])
    async def meeting(request: Request):
        return _action_body("meeting", await _json_body(request))

    return app


def _action_body(action: str, data: dict) -> dict:
    if action == "search":
        q = (data.get("need") or "").lower()
        hits = [f"{name} — {desc}" for name, desc in PRODUCTS
                if not q or q in name.lower() or q in desc.lower()]
        return {"company": COMPANY, "query": data.get("need", ""),
                "results": hits or [f"{n} — {d}" for n, d in PRODUCTS]}
    if action == "deck":
        return {"company": COMPANY, "request": "pitch deck",
                "status": "sent",
                "deliverable": "Omni-Ouro pitch deck (sandbox copy) — "
                               "recorded on the playground board; nothing was emailed"}
    return {"company": COMPANY, "request": "meeting", "status": "recorded",
            "note": "Sandbox: your request is on the playground board. "
                    "No calendar invite was sent."}


async def _json_body(request: Request) -> dict:
    try:
        return json.loads(await request.body() or b"{}")
    except Exception:
        return {}


_DASHBOARD_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Omni-Ouro — EyD business dashboard</title>
<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}
table{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem}td,th{border-bottom:1px solid #ddd;padding:.3rem .5rem;text-align:left;vertical-align:top}
code,pre{background:#f2f2f2;padding:.1rem .3rem}pre{padding:.6rem;overflow:auto;max-width:520px}
input{padding:.3rem .4rem}button{padding:.35rem .8rem;cursor:pointer}
.badge{font-weight:600}.mut{color:#667}</style></head><body>
<h1>Omni-Ouro — EyD business dashboard</h1>
<p class="mut">Site <code>__SITE__</code> · Demo build: this page ships
unauthenticated because the playground is a sandbox. A production install
puts it behind the business's own login, like any admin page.</p>

<h2>Gates — adjust PoT requirements</h2>
<p class="mut">This is a test playground: anyone may move a gate, the
change applies to every agent on the next request, and it
<b>auto-expires back to defaults after 15 minutes</b> — the
<code>since</code> stamp below (and on later Gated receipts) shows when
it was last moved. A production install puts this page behind the
business's own login instead.</p>
<p><button onclick="resetGates()">Reset gates to defaults now</button> <span id="gmsg"></span></p>
<table id="gates"><tr><th>Action</th><th>EyD required</th><th>Min PoT score (blank = any)</th><th>Since</th><th></th></tr></table>

<h2>Requests — every agent, any time</h2>
<p><input id="agentq" size="34" placeholder="agent_id (blank = all agents)">
<button onclick="load()">Query</button></p>
<table id="reqs"><tr><th>Time (UTC)</th><th>Agent</th><th>Action</th><th>Result</th><th>Classification</th><th>Receipt</th></tr></table>
<div id="hist"></div>

<script>
async function load(){
  const a = document.getElementById('agentq').value.trim();
  const d = await (await fetch('/dashboard/data' + (a ? '?agent='+encodeURIComponent(a) : ''))).json();
  document.getElementById('gates').innerHTML =
    '<tr><th>Action</th><th>EyD required</th><th>Min PoT score (blank = any)</th><th>Since</th><th></th></tr>' +
    Object.entries(d.gates).map(([k,g]) =>
      `<tr><td><code>${k}</code></td><td>${g.eyd_required ? 'yes' : 'no (open)'}</td>` +
      `<td><input id="ms-${k}" type="number" step="0.05" min="0" max="1" value="${g.min_score ?? ''}" placeholder="any"></td>` +
      `<td>${g.since || ''}</td><td><button onclick="save('${k}')">Save</button></td></tr>`).join('');
  document.getElementById('reqs').innerHTML =
    '<tr><th>Time (UTC)</th><th>Agent</th><th>Action</th><th>Result</th><th>Classification</th><th>Receipt</th></tr>' +
    (d.requests.slice().reverse().map(r =>
      `<tr><td>${r.ts}</td><td><code>${(r.agent||'anonymous').slice(0,13)}…</code></td><td>${r.action}</td>` +
      `<td>${r.result}</td><td class="badge">${r.classification || '—'}</td>` +
      `<td>${r.receipt ? `<details><summary>view</summary><pre>${JSON.stringify(r.receipt,null,1)}</pre></details>` : '—'}</td></tr>`).join('')
     || '<tr><td colspan="6">No requests yet.</td></tr>');
  document.getElementById('hist').innerHTML = d.agent_history ?
    `<h2>Clearing House history for <code>${a}</code> (all sites)</h2>` +
    (d.agent_history.map(r =>
      `<div><span class="badge">${r.classification}</span> ${r.ts} · site <code>${(r.site_id||'—').slice(0,13)}…</code> · score after: ${r.score_after ?? '—'}</div>`).join('')
     || '<p>No receipts at the Clearing House for this agent.</p>') : '';
}
async function save(action){
  const v = document.getElementById('ms-'+action).value;
  const r = await fetch('/dashboard/gates', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action, min_score: v === '' ? null : parseFloat(v)})});
  const d = await r.json();
  document.getElementById('gmsg').textContent = d.error ? d.error : 'saved';
  load();
}
async function resetGates(){
  const r = await fetch('/dashboard/gates', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({reset: true})});
  const d = await r.json();
  document.getElementById('gmsg').textContent = d.error ? d.error : 'reset to defaults';
  load();
}
load();
</script></body></html>"""


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PLAYGROUND_PORT", "8002"))
    app = make_app(
        clearinghouse_url=os.environ.get("CLEARINGHOUSE_URL", "http://127.0.0.1:8787"),
        public_clearinghouse_url=os.environ.get("CLEARINGHOUSE_PUBLIC_URL"),
        domain=os.environ.get("PLAYGROUND_DOMAIN", "localhost"),
        callback_url=os.environ.get("PLAYGROUND_PUBLIC_URL",
                                    f"http://localhost:{port}"))
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=port)
