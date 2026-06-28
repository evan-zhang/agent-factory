#!/usr/bin/env python3
"""Position monitor: update CSV in-place, output stop-loss decisions.

Usage:
  python position-monitor.py [--workdir DIR]

If --workdir is not provided, falls back to STOCK_PICKING_WORKDIR env var,
then to /Users/evan/.openclaw/gateways/life/domains/quant.
"""
import csv, json, subprocess, sys, os, datetime, argparse

def resolve_workdir():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default=None)
    args, _ = parser.parse_known_args()
    return (args.workdir
            or os.environ.get("STOCK_PICKING_WORKDIR")
            or "/Users/evan/.openclaw/gateways/life/domains/quant")

WORKDIR = resolve_workdir()
POSITIONS = os.path.join(WORKDIR, "data", "positions", "positions.csv")
# Fallback to legacy path
if not os.path.exists(POSITIONS):
    POSITIONS = os.path.join(WORKDIR, "data", "positions.csv")
TRADE_LOG = os.path.join(WORKDIR, "data", "trade_log.csv")
ENV_FILE = os.path.join(WORKDIR, ".env")

def get_quote(stock_code):
    cmd = f"source {ENV_FILE} && longbridge quote {stock_code} --format json 2>/dev/null"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
        return float(data.get("current_price", data.get("last_done", 0)))
    except:
        return None

def calc_trailing_stop(entry_price, profit_pct):
    if profit_pct > 20: return entry_price * 1.15
    if profit_pct > 15: return entry_price * 1.10
    if profit_pct > 10: return entry_price * 1.05
    if profit_pct > 5:  return entry_price
    return entry_price * 0.92

def main():
    if not os.path.exists(POSITIONS):
        print("NO_POSITIONS")
        return

    rows = []
    with open(POSITIONS, "r") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    open_rows = [r for r in rows if r.get("status") == "open"]
    if not open_rows:
        print("NO_OPEN")
        return

    actions = []
    now = datetime.datetime.now().isoformat(timespec="seconds")

    for row in open_rows:
        code = row["stock_code"]
        entry = float(row["entry_price"])
        hwm = float(row.get("high_water_mark") or entry)
        last_result = row.get("last_check_result", "normal")
        breach_ts = row.get("breach_timestamp", "")

        price = get_quote(code)
        if price is None:
            actions.append({"code": code, "action": "quote_failed"})
            continue

        profit_pct = (price - entry) / entry * 100
        trailing = calc_trailing_stop(entry, profit_pct)

        # Update high water mark
        if price > hwm:
            hwm = price
            row["high_water_mark"] = str(hwm)

        row["trailing_stop_price"] = f"{trailing:.2f}"

        # Stop loss check
        triggered = price <= trailing
        if triggered:
            if last_result == "breach_detected" and breach_ts:
                breach_time = datetime.datetime.fromisoformat(breach_ts)
                elapsed = (datetime.datetime.now() - breach_time).total_seconds()
                if elapsed >= 300:  # 5 min confirmed
                    row["last_check_result"] = "breach_confirmed"
                    row["breach_timestamp"] = now
                    actions.append({"code": code, "action": "STOP_LOSS", "price": price, "entry": entry, "qty": row.get("position_amount",""), "dry_run": row.get("dry_run","true")})
                else:
                    row["last_check_result"] = "breach_detected"
                    actions.append({"code": code, "action": "breach_waiting", "elapsed_s": int(elapsed)})
            else:
                row["last_check_result"] = "breach_detected"
                row["breach_timestamp"] = now
                actions.append({"code": code, "action": "breach_detected", "price": price, "trailing": trailing})
        else:
            row["last_check_result"] = "normal"
            row["breach_timestamp"] = ""
            actions.append({"code": code, "action": "normal", "price": price, "profit_pct": round(profit_pct,2), "trailing": trailing})

    # Write back
    with open(POSITIONS, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Output as JSON for the agent to consume
    print(json.dumps(actions, ensure_ascii=False))

if __name__ == "__main__":
    main()
