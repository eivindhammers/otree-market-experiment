#!/usr/bin/env python3
"""
Post-experiment analysis script for the CDA market experiment.

Reads the custom data export from the oTree admin interface and produces figures:
  1. Price evolution per round  (transaction prices + best bid/ask over time)
  2. Supply-demand diagram       (Smith mode only, with equilibrium and actual prices)

Usage
-----
  python analysis.py <custom_export.csv> [options]

How to get the export file
--------------------------
  oTree admin  →  Data  →  Custom export  →  download CSV
  (Works for singleAsset / sCDA sessions)

Options
-------
  --output DIR          Directory to save figures (default: figures/)
  --session CODE        Filter to a single session code
  --buyers SCHEDULES    Buyer value schedules, e.g. "110,95,80,65;105,90,75,60"
                        (auto-read from settings.py when run from the project root)
  --sellers SCHEDULES   Seller cost schedules, same format
"""

import argparse
import csv
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Parsing the custom export CSV
# ---------------------------------------------------------------------------

def parse_custom_export(filepath):
    """Return a dict of {TableName: DataFrame} from the mixed-header CSV."""
    raw = defaultdict(list)
    headers = {}
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or all(c == '' for c in row):
                continue
            if row[0] == 'TableName':
                # header row for the next table block
                table_name_col = row
                headers['current'] = row
            elif headers.get('current') and row[0] in ('Limits', 'Transactions', 'Orders', 'BidAsks', 'News'):
                raw[row[0]].append(dict(zip(headers['current'], row)))

    result = {}
    for name, rows in raw.items():
        df = pd.DataFrame(rows)
        # coerce obvious numeric columns
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass
        result[name] = df
    return result


# ---------------------------------------------------------------------------
# Load Smith schedules from settings.py (if available)
# ---------------------------------------------------------------------------

def load_schedules_from_settings():
    """Try to import smith_buyer_values and smith_seller_costs from settings.py."""
    if not os.path.exists('settings.py'):
        return None, None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('settings', 'settings.py')
        mod = importlib.util.load_from_spec(spec)
        spec.loader.exec_module(mod)
        configs = getattr(mod, 'SESSION_CONFIGS', [])
        for cfg in configs:
            if cfg.get('smith_mode'):
                buyers = cfg.get('smith_buyer_values')
                sellers = cfg.get('smith_seller_costs')
                if buyers and sellers:
                    return buyers, sellers
    except Exception as e:
        print(f'Note: could not auto-read schedules from settings.py ({e})')
    return None, None


def parse_schedule_arg(s):
    """Parse "110,95,80,65;105,90,75,60" into [[110,95,80,65],[105,90,75,60]]."""
    return [[float(v) for v in row.split(',')] for row in s.split(';')]


# ---------------------------------------------------------------------------
# Figure 1: price evolution per round
# ---------------------------------------------------------------------------

def plot_price_evolution(transactions, bidasks, session_filter, output_dir):
    if transactions.empty:
        print('No transaction data found – skipping price evolution plots.')
        return

    if session_filter:
        transactions = transactions[transactions['sessionID'] == session_filter]
        if not bidasks.empty:
            bidasks = bidasks[bidasks['sessionID'] == session_filter]

    periods = sorted(transactions['Period'].dropna().unique().astype(int))
    groups = sorted(transactions['group'].dropna().unique().astype(int))

    for group_id in groups:
        tx_g = transactions[transactions['group'] == group_id]
        ba_g = bidasks[bidasks['group'] == group_id] if not bidasks.empty else pd.DataFrame()

        n = len(periods)
        ncols = min(n, 3)
        nrows = int(np.ceil(n / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows), squeeze=False)
        fig.suptitle(f'Price evolution – group {group_id}', fontsize=14)

        for idx, period in enumerate(periods):
            ax = axes[idx // ncols][idx % ncols]
            tx_p = tx_g[tx_g['Period'] == period].copy()
            ba_p = ba_g[ba_g['Period'] == period].copy() if not ba_g.empty else pd.DataFrame()

            # bid/ask spread as step lines
            if not ba_p.empty and 'BATime' in ba_p.columns:
                ba_sorted = ba_p.sort_values('BATime')
                if 'bestBid' in ba_sorted.columns:
                    bid_data = ba_sorted.dropna(subset=['bestBid'])
                    if not bid_data.empty:
                        ax.step(bid_data['BATime'], bid_data['bestBid'],
                                where='post', color='steelblue', linewidth=1,
                                alpha=0.7, label='Best bid')
                if 'bestAsk' in ba_sorted.columns:
                    ask_data = ba_sorted.dropna(subset=['bestAsk'])
                    if not ask_data.empty:
                        ax.step(ask_data['BATime'], ask_data['bestAsk'],
                                where='post', color='tomato', linewidth=1,
                                alpha=0.7, label='Best ask')

            # transaction prices as scatter
            if not tx_p.empty and 'transactionTime' in tx_p.columns:
                ax.scatter(tx_p['transactionTime'], tx_p['price'],
                           color='black', s=30, zorder=5, label='Transaction')

            ax.set_title(f'Round {period}')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Price')
            if idx == 0:
                ax.legend(fontsize=7, loc='upper left')

        # hide unused subplots
        for idx in range(len(periods), nrows * ncols):
            axes[idx // ncols][idx % ncols].set_visible(False)

        plt.tight_layout()
        fname = os.path.join(output_dir, f'price_evolution_group{group_id}.png')
        fig.savefig(fname, dpi=150)
        plt.close(fig)
        print(f'  Saved {fname}')


# ---------------------------------------------------------------------------
# Figure 2: supply-demand diagram (Smith mode)
# ---------------------------------------------------------------------------

def build_step_curve(values, ascending=True):
    """
    Build (x, y) arrays for a step supply/demand curve.
    values: flat list of individual unit values or costs.
    ascending=True  → supply curve (costs sorted low→high)
    ascending=False → demand curve (values sorted high→low)
    """
    sorted_vals = sorted(values, reverse=(not ascending))
    xs, ys = [], []
    for i, v in enumerate(sorted_vals):
        xs.extend([i, i + 1])
        ys.extend([v, v])
    return np.array(xs), np.array(ys)


def find_equilibrium(buyer_values_flat, seller_costs_flat):
    """
    Find competitive equilibrium price and quantity by intersection of
    the step supply and demand curves.
    Returns (eq_price, eq_quantity) or (None, None) if not found.
    """
    demand_sorted = sorted(buyer_values_flat, reverse=True)   # high→low
    supply_sorted = sorted(seller_costs_flat)                  # low→high

    max_q = min(len(demand_sorted), len(supply_sorted))
    eq_q = 0
    for q in range(max_q):
        if demand_sorted[q] >= supply_sorted[q]:
            eq_q = q + 1
        else:
            break

    if eq_q == 0:
        return None, None

    # Equilibrium price: midpoint of last matched pair's values
    eq_price = (demand_sorted[eq_q - 1] + supply_sorted[eq_q - 1]) / 2
    return eq_price, eq_q


def plot_supply_demand(buyer_schedules, seller_schedules, transactions, session_filter, output_dir):
    if not buyer_schedules or not seller_schedules:
        print('No Smith schedule data available – skipping supply-demand plot.')
        print('  Provide schedules via --buyers / --sellers or run from the project root.')
        return

    buyer_flat = [v for sched in buyer_schedules for v in sched]
    seller_flat = [c for sched in seller_schedules for c in sched]

    eq_price, eq_qty = find_equilibrium(buyer_flat, seller_flat)

    fig, ax = plt.subplots(figsize=(8, 5))

    # Supply curve
    sx, sy = build_step_curve(seller_flat, ascending=True)
    ax.step(sx, sy, where='post', color='tomato', linewidth=2, label='Supply (marginal cost)')

    # Demand curve
    dx, dy = build_step_curve(buyer_flat, ascending=False)
    ax.step(dx, dy, where='post', color='steelblue', linewidth=2, label='Demand (marginal value)')

    # Equilibrium
    if eq_price is not None:
        ax.axhline(eq_price, color='gray', linestyle='--', linewidth=1, alpha=0.8,
                   label=f'Equilibrium price ≈ {eq_price:.1f}')
        ax.axvline(eq_qty, color='gray', linestyle=':', linewidth=1, alpha=0.8,
                   label=f'Equilibrium qty = {eq_qty}')

    # Actual transaction prices per round
    if not transactions.empty:
        if session_filter:
            tx = transactions[transactions['sessionID'] == session_filter].copy()
        else:
            tx = transactions.copy()
        periods = sorted(tx['Period'].dropna().unique().astype(int))
        cmap = plt.cm.viridis
        colours = cmap(np.linspace(0.2, 0.9, len(periods)))
        for period, colour in zip(periods, colours):
            tx_p = tx[tx['Period'] == period]
            if tx_p.empty:
                continue
            mean_price = tx_p['price'].mean()
            ax.axhline(mean_price, color=colour, linestyle='-', linewidth=1.2, alpha=0.7,
                       label=f'Round {period} mean price ({mean_price:.1f})')

    ax.set_xlabel('Quantity')
    ax.set_ylabel('Price')
    ax.set_title('Supply and demand (Smith mode)')
    ax.legend(fontsize=8, loc='upper right')

    plt.tight_layout()
    fname = os.path.join(output_dir, 'supply_demand.png')
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f'  Saved {fname}')


# ---------------------------------------------------------------------------
# Figure 3: summary – mean transaction price per round
# ---------------------------------------------------------------------------

def plot_price_summary(transactions, session_filter, output_dir):
    if transactions.empty:
        return
    if session_filter:
        transactions = transactions[transactions['sessionID'] == session_filter]

    groups = sorted(transactions['group'].dropna().unique().astype(int))
    fig, ax = plt.subplots(figsize=(7, 4))
    cmap = plt.cm.tab10
    colours = cmap(np.linspace(0, 0.9, len(groups)))

    for group_id, colour in zip(groups, colours):
        tx_g = transactions[transactions['group'] == group_id]
        summary = tx_g.groupby('Period')['price'].agg(['mean', 'std', 'count']).reset_index()
        summary = summary.sort_values('Period')
        ax.errorbar(summary['Period'], summary['mean'], yerr=summary['std'],
                    fmt='o-', color=colour, capsize=3, label=f'Group {group_id}')

    ax.set_xlabel('Round')
    ax.set_ylabel('Mean transaction price')
    ax.set_title('Mean transaction price per round')
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    if len(groups) > 1:
        ax.legend(fontsize=8)

    plt.tight_layout()
    fname = os.path.join(output_dir, 'price_summary.png')
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f'  Saved {fname}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='CDA experiment analysis')
    parser.add_argument('export_csv', help='Custom export CSV from oTree admin')
    parser.add_argument('--output', default='figures', help='Output directory (default: figures/)')
    parser.add_argument('--session', default=None, help='Filter to a session code')
    parser.add_argument('--buyers', default=None,
                        help='Buyer value schedules, e.g. "110,95,80,65;105,90,75,60"')
    parser.add_argument('--sellers', default=None,
                        help='Seller cost schedules, e.g. "25,40,55,70;30,45,60,75"')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f'Reading {args.export_csv} ...')
    tables = parse_custom_export(args.export_csv)

    transactions = tables.get('Transactions', pd.DataFrame())
    bidasks = tables.get('BidAsks', pd.DataFrame())

    if transactions.empty:
        print('WARNING: no Transactions found in export file.')
    else:
        print(f'  {len(transactions)} transaction rows across '
              f'{transactions["Period"].nunique()} round(s)')

    # Smith schedules: CLI > settings.py > None
    buyer_schedules, seller_schedules = None, None
    if args.buyers and args.sellers:
        buyer_schedules = parse_schedule_arg(args.buyers)
        seller_schedules = parse_schedule_arg(args.sellers)
        print('Using schedules from command-line arguments.')
    else:
        buyer_schedules, seller_schedules = load_schedules_from_settings()
        if buyer_schedules:
            print('Auto-loaded Smith schedules from settings.py.')

    print('\nGenerating figures ...')
    plot_price_evolution(transactions.copy(), bidasks.copy(), args.session, args.output)
    plot_price_summary(transactions.copy(), args.session, args.output)
    plot_supply_demand(buyer_schedules, seller_schedules, transactions.copy(), args.session, args.output)

    print('\nDone.')


if __name__ == '__main__':
    main()
