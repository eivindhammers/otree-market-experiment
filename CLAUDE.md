# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
otree devserver

# Create a session (not typically needed in dev)
otree create_session <session_config_name> <num_participants>

# Reset the database
otree resetdb
```

There is no test suite. The virtual environment is in `./venv/`.

## Architecture Overview

This is a **Continuous Double Auction (CDA)** market experiment built on oTree v6. It implements real-time order-book trading using oTree's live pages (WebSocket-based). The experiment was designed following Smith (1962) and Palan et al. (2020).

### Four Apps

| App | URL slug | Description |
|-----|----------|-------------|
| `singleAsset` | `sCDA` | Single asset, no private info |
| `nAssets` | `nCDA` | Multiple assets (A–D), no private info |
| `singleAssetInfo` | `sCDAInfo` | Single asset + private information partitions |
| `nAssetsInfo` | `nCDAInfo` | Multiple assets + private information partitions |

All four apps share the same page sequence and architecture; the Info variants add an information-partition layer on top. All logic lives in each app's `__init__.py`.

### Data Model

```
Session
 └─ Subsession  (tracks offerID, orderID, transactionID, assetID counters)
     └─ Group   (one group = all players; owns market state, order book, timers)
         └─ Player  (endowment, holdings, trading stats, payoff)

ExtraModel tables (exported via custom_export()):
  Limit        – all limit orders with order-book snapshots
  Order        – all orders (limit + market)
  Transaction  – executed trades
  BidAsks      – best-bid/ask snapshots for timing analysis
  News         – order rejections and status messages
  AssetsPartitions  (Info apps) – coin-jar partition amounts
  AssetsInRound     (nAssets*)  – which assets are available each round
```

### Real-Time Trading Flow

The `Market` page is an oTree **live page**. The browser calls `liveSend()` → server dispatches `live_method()` → server calls `send_to_group()` to broadcast updates. No page reloads during trading. Key JS entry points:

- `_static/sCDAstatic/scriptSAssetMarket.js` — `sendOffer()`, `sendAcc()`, `liveRecv()` for single-asset
- `_static/nCDAstatic/scriptnAssetsMarket.js` — same, asset-aware, for multi-asset
- `_static/scriptMarket.js` — shared order-book display, highlighting, cancellation UI
- `_static/chart.js` — Highcharts price/bid-ask chart (also used in admin report)

### Role System

- **Basic apps:** observer vs trader
- **Smith mode** (`smith_mode=True`): buyer vs seller with induced demand/supply schedules
- **Info apps:** I0 (uninformed) through I3 (three levels of informed), plus observers
- Roles can be fixed or re-randomised each round (`randomise_types`)

### Payoff Calculation

- **Standard:** `payoff = max(base_payment + multiplier × wealthChange, min_payment)`
- **Smith mode:** `payoff = base_payment + payoff_scale × (private_value − cost + cash_change)`
- One round is drawn randomly at the end for final payout (`finalPayoff`).

### Configuration

Session parameters are set in `settings.py` under `SESSION_CONFIGS` and can be overridden at session creation:

| Parameter | Effect |
|-----------|--------|
| `market_time` | Trading duration in seconds |
| `randomise_types` | Re-draw roles each round |
| `short_selling` / `margin_buying` | Allow negative positions |
| `num_trial_rounds` | Unpaid practice rounds |
| `fixed_asset_value` | Override random buyback value |
| `smith_mode` | Enable induced supply/demand |

### Parameter Files (`_parameters/`)

- `assetsPartitions.csv` — coin-jar partition amounts per asset (used by Info apps)
- `assetsInRound.csv` — maps round number → available asset IDs (used by nAssets apps)

### Templates

Shared HTML fragments live in `_templates/` (instructions, payoff explanations, final results, admin report). Each app has its own `templates/<AppName>/` directory for page-specific HTML.

## Deployment

- **Local:** `otree devserver` with SQLite (`db.sqlite3`)
- **Production:** Render.com or Heroku with PostgreSQL (`psycopg2` is already a dependency); set `DATABASE_URL` and `OTREE_PRODUCTION=1` environment variables
- Admin interface at `/demo` (dev) or `/SessionStart` (prod); customised via `vars_for_admin_report()` and `_templates/admin_report.html`
