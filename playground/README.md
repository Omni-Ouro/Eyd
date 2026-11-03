# Omni-Ouro playground — the business install

A real business endpoint running the **EyD verifier SDK** against the
hosted EyD Clearing House. This is what a business installs to gate
agent traffic on PoT scores; Omni-Ouro runs it on its own domain
(`eyd.omni-ouro.com`) as the public playground for the beta.

| Endpoint | Gate |
|---|---|
| `GET /search` | open — EyD agents that show up still earn receipts |
| `POST /deck` | EyD required, any PoT score (request the pitch deck) |
| `POST /meeting` | EyD required, PoT score ≥ 0.8 (request a meeting) |

Everything is sandboxed: requests land on the board at `/`, nothing is
emailed, no calendar invite is sent. Agents without EyD, or below the
gate, get one of the five refusal reasons and a Gated receipt (score-neutral; the gate rides the receipt).

## What "installing" means for a business

```python
from verifier import EyDSite
from fastapi_integration import gated

site = EyDSite(my_site_identity,
               clearinghouse_url="https://clearinghouse.omni-ouro.com",
               domain="eyd.example.com", callback_url="https://eyd.example.com")
site.enroll()

@app.post("/meeting")
@gated(site, min_score=0.8)          # EyD + PoT >= 0.8, or a refusal + Gated receipt
async def meeting(request: Request):
    return {"status": "recorded"}   # the decorator reports it fulfilled
```

[main.py](main.py) is the full working version: the SDK's `@gated`
decorator (attestation, sessions, per-action score and Passport
checks, reporting) over three small handlers, plus revocation push
handling and a request board. Node/TypeScript sites use the mirror
SDK in [../verifier/ts/](../verifier/ts/) with its `eydGate` Express
middleware.

## Business dashboard (`/dashboard`)

What the business operates day to day, in [main.py](main.py):

- **Adjust PoT requirements at runtime** — per-action minimum score,
  saved from the page; the next request is checked against the new
  value (`@gated` accepts a callable `min_score`), and the change is
  stamped — that stamp is the `since` on later Gated receipts.
- **Query any agent's requests** — this site's full request list,
  filterable by `agent_id`, each row joined to the Proof Receipt the
  Clearing House issued for it (viewable in place).
- **Full Clearing House history for one agent** — every receipt that
  agent holds, across all sites, via
  `EyDSite.clearinghouse_receipts(agent_id)`.

Demo build: the page is unauthenticated because the playground is a
sandbox. A production install puts it behind the business's own
login, like any admin page.

## Run it

```bash
CLEARINGHOUSE_URL=https://clearinghouse.omni-ouro.com \
PLAYGROUND_DOMAIN=eyd.omni-ouro.com \
PLAYGROUND_PUBLIC_URL=https://eyd.omni-ouro.com \
python playground/main.py        # PLAYGROUND_PORT, default 8002
```

The site identity persists at `PLAYGROUND_KEY_FILE`
(default `playground/.keys/site.json`, gitignored): the business's
`site_id` is derived from that key, and the private key never leaves
the box.
