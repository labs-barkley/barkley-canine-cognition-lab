# Deploy the DogGraph on your own VPS (permanent, ~5 €/mo)

One small server runs everything behind **https://doggraph.getbarkley.com**:
Neo4j Community (the graph) + the Streamlit app + Caddy (automatic HTTPS).
No more free-tier deletion, no more sleep, on-brand.

> Synthetic data only · research demonstrator · not a diagnostic tool · patent applications filed

---

## Phase 1 — Create the VPS
- Provider: **Hetzner Cloud** (recommended, EU, ~€4.5/mo) → CX22 (2 vCPU / 4 GB).
  DigitalOcean also works ($12/mo, 2 GB droplet).
- Image: **Ubuntu 24.04**. Add your SSH key (or use the emailed root password).
- Note the server's **public IPv4**.

## Phase 2 — Point the domain
Add a DNS **A record** on getbarkley.com:
```
doggraph   A   <VPS_PUBLIC_IP>   TTL 300
```
Wait until `ping doggraph.getbarkley.com` shows the VPS IP (usually minutes).

## Phase 3 — Install Docker
SSH in (`ssh root@<VPS_IP>`), then:
```bash
curl -fsSL https://get.docker.com | sh
```

## Phase 4 — Get the code + secrets
```bash
apt-get update && apt-get install -y git
git clone https://github.com/labs-barkley/barkley-canine-cognition-lab.git
cd barkley-canine-cognition-lab/neo4j-doggraph-demo/deploy
cp .env.example .env
nano .env          # set a long NEO4J_PASSWORD and paste your ANTHROPIC_API_KEY
```

## Phase 5 — Launch
```bash
docker compose up -d --build
docker compose ps                 # wait until neo4j is "healthy"
```

## Phase 6 — Seed the graph (once)
From the same `deploy/` folder:
```bash
set -a; . ./.env; set +a
cat ../schema.cypher          | docker compose exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD"
cat ../seed_synthetic.cypher  | docker compose exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD"
```

## Phase 7 — Verify
Open **https://doggraph.getbarkley.com** — Caddy issues the TLS cert automatically
on first hit (give it ~30 s). Ask a preset question; you should get a grounded answer.

---

## Operations
```bash
docker compose logs -f app        # app logs
docker compose restart app        # restart after a code change
git pull && docker compose up -d --build   # deploy new code
docker compose down               # stop (graph data persists in the neo4j_data volume)
```

Re-seeding is safe (the seed uses MERGE — idempotent). To wipe and reseed, remove
the `neo4j_data` volume: `docker compose down -v` then repeat Phases 5–6.

## Security notes (from the audit)
- Neo4j bolt is **not** published to the host — only the app reaches it over the
  private compose network. Only 80/443 are public (Caddy).
- Consider a firewall: `ufw allow 22,80,443/tcp && ufw enable`.
- Keep `.env` private (it is git-ignored). Never commit real keys.
