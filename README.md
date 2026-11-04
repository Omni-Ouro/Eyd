# EyD

**Agents act on your behalf. Nobody can prove what they did.**

[![Demo video](https://img.shields.io/badge/demo%20video-2%3A59-blue)](https://www.youtube.com/watch?v=5X7RR0bsljE)
[![Live playground](https://img.shields.io/badge/live-eyd.omni--ouro.com-brightgreen)](https://eyd.omni-ouro.com)
[![Clearing House](https://img.shields.io/badge/clearinghouse-omni--ouro.com-brightgreen)](https://clearinghouse.omni-ouro.com)
[![Tests](https://github.com/Omni-Ouro/Eyd/actions/workflows/test.yml/badge.svg)](https://github.com/Omni-Ouro/Eyd/actions/workflows/test.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

## Submission overview — Meta Global AI Developer Hackathon 2026

- **Track & problem statement:** Startup · **Push the Frontier**
- **Provenance:** Built from scratch during the hackathon window,
  Oct 26 – Nov 4, 2026. The commit history starts Oct 26; no code
  predates it.
- **Demo video (2:59):** https://www.youtube.com/watch?v=5X7RR0bsljE
- **Live deployment:** Clearing House
  https://clearinghouse.omni-ouro.com · business playground and
  dashboard https://eyd.omni-ouro.com — the dashboard is open in the
  browser, no install or account.
- **Meta AI runtime models:** open-weight Muse Spark
  (`meta-models/muse-spark-open-1026`, served via Baseten) runs the
  Clearing House expectation vector; Muse (`muse-wonder-1.0` via the
  Meta model gateway) drives the acting demo agents. Details:
  [Meta AI tooling](#meta-ai-tooling).
- **Bonus category targeted:** Best Agentic Use-Case.
- **Keyless verification (no API key needed):** `pytest` (56 tests),
  and the hosted-beta walk `python examples/beta_agent.py` against the
  live deployment above. The judge console's live model calls need a
  model gateway token (see `.env.example`).

> "Govern the event, not the technology." — Peter Evans-Greenwood

EyD doesn't govern the agent or the model; it records the event and
gets the counterparty to attest to the same event.

EyD is a small library and a small window. The agent framework imports
it, and it sits in the tool-call path: every call the agent makes is
signed under the agent's own Ed25519 key and reported to a
clearinghouse before it goes out. The counterparty site reports its
side after. The clearinghouse pairs the two, classifies the result
(Expected, Unexpected, Declined, Gated, Unverified, Deviated), and issues a signed Proof
Receipt to both parties. Agents that don't route through EyD get no receipt.
Sites that gate on EyD only admit agents that do.

Built for the Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026),
Startup track. Design doc: [EYD_DESIGN.md](EYD_DESIGN.md). Proof format:
[spec/PROOF_v0.md](spec/PROOF_v0.md). Market fit:
[docs/market-fit.md](docs/market-fit.md). Build disclosure:
[How this repo was built](#how-this-repo-was-built).

## Try the live deployment

- **Demo video (2:59):** https://www.youtube.com/watch?v=5X7RR0bsljE
- **Live hosted Clearing House:** https://clearinghouse.omni-ouro.com
  (`/` returns the service name, version, Clearing House id, and the
  expectation model in use)
- **Live hosted business playground:** https://eyd.omni-ouro.com —
  a real business install of the verifier SDK, with its operator
  dashboard at https://eyd.omni-ouro.com/dashboard (open, no account:
  adjust gates, query agents, read receipts right in the browser)
- **Run the judge console locally:** see
  [Run the demo locally](#run-the-demo-locally) below.

Prerequisites: Python ≥ 3.11 (Node ≥ 18 only for the TypeScript
verifier). Commands below are bash — macOS/Linux, or Git Bash/WSL on
Windows.

## Test the beta (hosted)

EyD Clearing House **v0.1.0** runs hosted, and Omni-Ouro runs the
business SDK on its own domain as a public playground — test against
both, no demo driver needed:

- **Clearing House:** https://clearinghouse.omni-ouro.com — `/` names the service, version, and public key.
- **Playground business:** https://eyd.omni-ouro.com — `/search` open, `/deck` needs EyD, `/meeting` needs PoT ≥ 0.8. Sandboxed: nothing is emailed, ever.

**As an agent** — install the SDK and act (five minutes, no API key):

```bash
git clone https://github.com/Omni-Ouro/Eyd.git && cd Eyd
pip install -e .
python examples/beta_agent.py
```

It enrolls, searches, gets a meeting refused while its score is
unknown, earns a score with clean actions, and gets the meeting.
Your identity persists, so the score you build is still there tomorrow.

**As a business** — the verifier SDK in front of your endpoints.
[playground/](playground/) is Omni-Ouro's working install (~150 lines):

```python
from verifier import EyDSite
from fastapi_integration import gated

site = EyDSite(identity, clearinghouse_url="https://clearinghouse.omni-ouro.com",
               domain="eyd.example.com", callback_url="https://eyd.example.com")
site.enroll()

@app.post("/meeting")
@gated(site, min_score=0.8)   # EyD + PoT >= 0.8, or a refusal + Gated receipt
async def meeting(request: Request):
    return {"status": "recorded"}   # the decorator reports it fulfilled
```

Node/Express instead: `eydGate` from `eyd-verifier/express` — see
[verifier/ts/](verifier/ts/).

Hosted honesty: the public Clearing House is the single-node v0.1.0
below, run with persistence on and its demo-data endpoints (`/seed`,
`/boost`) admin-locked — nobody can add score history to it except
through real paired actions. Seeded history
stays a local-demo fixture, labeled as such everywhere.

## Quickstart (the SDK alone)

```bash
pip install -e ".[dev]"
eyd init            # generate your agent's Ed25519 identity
eyd id              # print agent_id
eyd verify-local    # walk and verify the local action chain
pytest              # canonicalization vectors, records, chain
```

One test cross-checks the TypeScript verifier; it skips unless Node
is present and the TS package is built:
`npm --prefix verifier/ts install && npm --prefix verifier/ts run build`.

## What we built (this repo, Apache-2.0, all new Oct 26 – Nov 4)

- **EyD SDK** (`eyd/`) — a library the framework imports: `@eyd.tool`
  decorator, `eyd.wrap()`, `eyd.hook(framework)`, verb registration,
  identity, canonicalization, Action Records, local hash chain,
  reporting with offline queue, CLI (`init`/`enroll`/`run`/`verify-local`).
  `eyd run` only opens the window attached to the local chain.
- **Proof format v0** (`spec/PROOF_v0.md`) — records, reports, receipts,
  canonicalization (RFC 8785) + test vectors, attestation.
- **AI Passport interoperability** (`passport-interop/`, [AI_PASSPORT.md](AI_PASSPORT.md)) — the clearinghouse also reads ServiceNow AI Passports as an identity credential alongside EyD (Passport alone never suffices by default; Passport + EyD is the combined tier). ServiceNow's published test vectors pass against our check unmodified: verifier 81/81, caller 74/74.
- **EyD Clearing House** (`clearinghouse/`) — single-node pairing,
  classification, receipts, PoT score, fork detection. Gate refusals
  classify **Gated** — score- and streak-neutral, with the gate itself
  (threshold, reason, since when) bound into the receipt — apart from
  **Declined**, a business refusal that counts. The same code
  runs locally and as the hosted beta (see Deploy).
- **Model expectation (vector two, advisory)** — at intent time the
  Clearing House asks a model, from the declared action alone (verb,
  tool, target — never arguments, never result content), what a
  successful result should look like, labeled with a category from a
  fixed taxonomy, and pre-registers that sketch
  against the record. It is bound into the signed receipt; the site
  attests, in its signed report, whether its result matched. It never
  changes a classification or score — it is evidence, not a referee —
  and over time the accumulated, category-labeled sketches form a
  per-site corpus of expected action shapes: training data for a cheap
  local decision model to eventually take over the labeling.
- **Verifier / site SDK** (`verifier/python/`, `verifier/ts/`) — attestation, sessions,
  reporting, offline `verify_receipt`, site score gating. Python and TypeScript
  implementations with cross-compatible keys and signatures; turnkey gates for
  FastAPI (`@gated`) and Express (`eydGate`).
- **Demo site** (`demo-site/`) — one business, three independently gated
  actions (search / quote / pay), runtime gate controls, tamper toggle.
- **Judge console** (`console/`) — the demo page: pick an agent, set the
  site's gates, click a task, watch the refusal or the receipt land.
- **EyD window** (`eyd-ui/window.py`) — live action list and receipt viewer (local web view).
- **Demo agents** (`agent-demo/`) — one Meta-model agent ([agent.py](agent-demo/agent.py)) behind six console identities: bare, low-score EyD, EyD + Passport, Passport-only, newcomer, and the Bad Agent. A's tools are undecorated; the rest carry `@eyd.tool` under different keys; model code identical. The console drives it, one model call per click.

## What EyD proves and what it doesn't

The precise claim: **proof of agreement plus deviation, not proof of
honesty.**

What a receipt proves: two parties independently signed the same
event — the agent reported its intent before acting and hashed what
came back; the counterparty site reported its side; the hashes pair,
or the mismatch is on the record. And when the framework exposes the
task, the receipt proves the agent's action matched the verb the task
implied — or that it Deviated.

What it does not prove: that either party is honest. A colluding
agent and site can mint Expected receipts together. EyD's counters
are structural, not magical:

- **Corroboration is labeled.** Enrollment declares `operator_id`
  (and `integrator_id` when a vendor integrates on a customer's
  behalf). Receipts carry `corroboration: independent |
  same_operator | same_integrator`, and same-operator or
  same-integrator receipts count for less toward the PoT score —
  two reports from the same operator are a single report signed
  twice. Stated limit: registration declares who operates a signer;
  it cannot prove who holds the key. Independence is earned across
  many unrelated counterparties, not asserted by one.
- **Score provenance is visible.** The score endpoint and the
  console break a score down by verb, so a score built only on
  ungated actions reads as what it is — and it still fails any gate
  a cautious site sets.
- **No content is evidence.** Task text and tool arguments never
  leave the device; the ledger holds hashes, verbs, and outcomes.

## Run the demo locally

```bash
pip install -e ".[clearinghouse]"
ISSUER_URL=http://localhost:8010 python passport-demo/issuer.py &   # demo Passport issuer :8010
CLEARINGHOUSE_KEY_FILE=.tmp-ch-key.json PASSPORT_ISSUER=http://localhost:8010 \
  PASSPORT_JWKS_URL=http://localhost:8010/jwks python clearinghouse/main.py &  # :8787
SITE_PORT=8001 python demo-site/main.py &                          # one site, three gated actions
CONSOLE_PORT=8080 python console/server.py &                       # judge console
# open http://127.0.0.1:8080 and drive the demo
```

## Deploy (droplet)

The hosted beta is two services — EyD Clearing House v0.1.0 and the
Omni-Ouro playground — behind Caddy on one droplet; the judge console
is a local demo and is not part of it. Runbook:
[deploy/README.md](deploy/README.md). Locally, the whole console
stack also starts in one command (`scripts/start-all.sh`,
`scripts/stop-all.sh` to stop; console binds localhost unless
`HOST=0.0.0.0` is set).

## Meta AI tooling

EyD uses Meta models in three distinct places; no other model's output
is a runtime dependency, and no classification or score ever depends on
a model.

- **Muse Spark, open weights (in the product).** The Clearing House's
  expectation vector ([clearinghouse/expectations.py](clearinghouse/expectations.py))
  runs `meta-models/muse-spark-open-1026` — open-weight Muse Spark,
  served through **Baseten** — at intent time. From the declared verb,
  tool, and target alone (never arguments, never result content), it
  pre-registers a one-sentence expected-outcome sketch against the
  Action Record; the sketch is bound into the signed Proof Receipt and
  the site attests whether its result matched. The hosted beta's `/`
  endpoint reports this model live (`expectation_model`). Advisory
  only: if the gateway is unreachable, expectations fail open and
  receipts still issue.
- **Muse (in the demo).** The acting agents in the judge console and
  [agent-demo/agent.py](agent-demo/agent.py) are live Meta-model tool
  calls (`muse-wonder-1.0` via the Meta model gateway). The tool calls
  being signed, gated, and classified — including the Bad Agent routing
  a payment task to an email tool and being classified Deviated — are
  the model's own choices, not scripted responses.
- **Muse Wonder 1.0 (to build it).** The development coding agent was
  Meta's `muse-wonder-1.0` in an agentic coding harness, under human
  direction; see [How this repo was built](#how-this-repo-was-built)
  for the full disclosure of what was human and what was model.

## Evaluation and benchmarks

Measured results, all reproducible from this repo:

| Evaluation | Result | How to reproduce |
|---|---|---|
| ServiceNow AI Passport conformance, verifier role | **81/81** (re-run 2026-11-01) | `passport-interop/` against ServiceNow's published suite |
| ServiceNow AI Passport conformance, caller role | **74/74** (re-run 2026-11-01) | same harness, caller adapter |
| Python test suite | **56 passed** | `pytest` (also runs in CI) |
| TypeScript verifier suite | **16 passed** | `npm --prefix verifier/ts test` |
| Judge console end-to-end validation | **0 failures** | `python scripts/validate_console.py` on a fresh stack: real model calls through refusal, Gated, Expected, Unexpected, and Deviated paths |
| Canonicalization | spec vector in [spec/PROOF_v0.md](spec/PROOF_v0.md) verified in tests | `pytest tests/test_canonical.py` |

The console validation script doubles as the evaluation harness: it
drives the live system (real model, real gates, real Clearing House)
and asserts the classification and score after every action, rather
than mocking the path it claims to test.

## Market fit

The market signal is the wall going up: JPMorgan Chase and Charles
Schwab block third-party agents from customer accounts; Amazon,
Kohl's, Neiman Marcus, TheRealReal, Tapestry, Adidas, eBay and Zillow
restrict agent checkout or browsing; Delta and United bar automated
booking; Yelp admits only licensed bots. None of them said agents are
bad — they said unidentified, unaccountable agents are unacceptable.
Each has already built the wall; EyD is the door in it, because a gate
needs something to check: an identity, a behaviour score, and a signed
record of what the agent actually did. Full table, the
product-market-fit work done during the hackathon, and input from
professionals in the field (Nicolas Moreno of Zarel, Daniel Seilitz,
Peter Evans-Greenwood, ServiceNow): [docs/market-fit.md](docs/market-fit.md).

## What we didn't build (third-party / hosted)

- The Meta models and any agent framework built on them (the SDK hooks
  into its tool-call path; used, not built here).
- `cryptography` (Ed25519/SHA-256 primitives), FastAPI/uvicorn, pytest.
- The multi-tenant **PoT Clearinghouse** tier (webhooks, market data) and
  **Eyro** governance/audit — operated by Omni-Ouro, not in this repo.
  `clearinghouse/` here is the single-node v0.1.0: local testing and the
  hosted beta are the same code.
- Seeded demo history in `fixtures/` is **demo data**, labeled as such everywhere.

## How this repo was built

Commits carry a `Co-Authored-By: Claude Code` trailer: the
development harness was Claude Code, running Meta's
`muse-wonder-1.0` model — no Anthropic model wrote this code.
Planning documents (e.g. AI_PASSPORT.md) were drafted with help from
Claude in chat; all code was written in the harness described above.
The models the product itself calls are Meta's: the expectation vector
runs `meta-models/muse-spark-open-1026` (open-weight Muse Spark via
Baseten), and the demo agents run on the same Meta model gateway.

## License
Apache-2.0 — see [LICENSE](LICENSE).
