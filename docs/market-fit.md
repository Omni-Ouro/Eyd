# Market fit

## The sites blocking agents today are the market

A growing number of major businesses and platforms have moved to block
or restrict third-party AI personal agents (Meta's Muse, xAI's Grok,
OpenAI's Dots, Instinct, Perplexity, and others) from their websites,
accounts, and checkout systems (reported by CNBC). The pattern in every
row is the same: the block exists because the site cannot tell a
verified, accountable agent from an anonymous bot. EyD is the thing
they would admit instead.

| Sector | Companies blocking / restricting agents | Why they block (their stated reasons) | The EyD scenario |
|---|---|---|---|
| Financial services & banking | JPMorgan Chase; Charles Schwab | Security and privacy on customer accounts; fear of bots moving customer funds to higher-yield accounts | The bank keeps the blanket block for anonymous agents but opens a gated path: the agent carries EyD, actions are pre-committed and receipted, and a `Deviated` action (task said *check balance*, agent tried *transfer*) lands on a signed record and tanks the agent's score |
| Retail & e-commerce | Amazon (also sued Perplexity; promotes its own Alexa for Shopping / "Buy for Me"); Kohl's; Neiman Marcus; TheRealReal; Tapestry (Coach, Kate Spade); Adidas; eBay; Zillow | Lack of bot identification and security risk on checkout; no accountability for automated purchases | The retailer admits EyD agents to a checkout endpoint gated on PoT score — a fresh or misbehaving agent gets `PoT score unknown` / `below threshold`, a proven one checks out; every purchase pairs the agent's signed intent with the store's signed report |
| Travel & transportation | Delta Air Lines; United Airlines; Cars.com; Amtrak | Automated booking prohibited; robots and spiders barred from booking services | The airline opens booking to EyD-carrying agents only: booking attempts are receipted before execution, mis-bookings show up as mismatched hashes, and a bad streak pauses the agent's credential everywhere, not just on one site |
| Directories & local data | Yelp | Free agent access blocked; only bots whose developers pay for the official data licensing program get in | The paywall becomes a trust wall too: licensed developers' agents carry EyD, so licensed access is also *accountable* access — abuse is attributable to a key and a score, not just an IP |

None of these companies said "agents are bad." They said unidentified,
unaccountable agents are unacceptable — JPMorgan cites security,
Amazon cites bot identification, Yelp already runs a paid licensing
gate. Each has already built the wall; EyD is the door in it, because
a gate needs something to check: an identity, a behaviour score, and
a signed record of what the agent actually did.

## Product-market-fit work done during the hackathon

| What I did | What it tested | Signal / what changed |
|---|---|---|
| Built the SDK as a library the framework imports — killed the proxy and MCP-server builds | Whether developers accept interception vs. a small import | Library survived contact with real agent code; proxy/MCP builds deleted |
| Published a hosted Clearing House v0.1.0 with agent and business installs | Whether a stranger can test it end-to-end with no demo driver | Fresh agent enrolls, gets refused, earns score, admitted at 0.857 — verified repeatedly from clean clones |
| Ran the business SDK on my own company's domain (`eyd.omni-ouro.com`) | Whether a real business puts this in front of real endpoints | Playground live with three differently gated actions — the same pattern Delta or Kohl's would run on booking/checkout |
| Ran ServiceNow's AI Passport conformance vectors unmodified | Whether an incumbent identity standard's ecosystem accepts the interop | Verifier 81/81, caller 74/74, re-validated Nov 1 |
| Made Passport-alone insufficient by default; combined tier pauses on bad streaks | Whether identity-only gating is the gap, not the product | Behaviour governs: a well-identified agent that acts badly loses access automatically |
| Added turnkey gates (`@gated` FastAPI, `eydGate` Express) after the raw verifier SDK | Whether integration effort blocked adoption | Business install dropped to a decorator + ~150 lines (the playground itself) |
| Added the model-expectation vector (vector two) | Whether sites would attest more than a hash match | Sites sign `expectation_match`; accumulated category-labeled sketches form a per-site corpus of expected action shapes — the long-term data asset |
| External review pass (fresh-install test) | Whether the repo works for someone who isn't me | One fresh-install failure fixed; two overstated claims tightened (`81857b2`) |

## Input from professionals in the field

| Person | Their input | What it changed (or confirmed) |
|---|---|---|
| Nicolas Moreno (Zarel) | A "below threshold" refusal reported as Declined, and Declined counts in the score — so a site raising its gate lowers the score of an agent that keeps trying, and three in a row pause its Passport. And the receipt doesn't carry the gate: which threshold, set by whom, since when. "That's the lender's decision from the credit report." | New **Gated** classification: gate refusals are score- and streak-neutral, and the signed gate block (`min_score`, reason, `since`) rides the Gated receipt. Implemented, tested, and live on the hosted beta |
| Daniel Seilitz | Sustained discussion of the subject on LinkedIn | Pressure-tested the premise in public, with practitioners, before it was a pitch |
| Peter Evans-Greenwood | "Govern the event, not the technology." | The framing EyD is built on — don't govern the agent or the model; record the event and get the counterparty to attest to the same event. Cited at the top of the README |
| ServiceNow | Published the AI Passport spec and repo and asked the community to engage with it | EyD's Passport support: the clearinghouse reads Passports as an identity credential alongside EyD, checked against ServiceNow's own conformance vectors (verifier 81/81, caller 74/74) |
