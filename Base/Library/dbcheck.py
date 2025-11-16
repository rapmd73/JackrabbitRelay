#!/usr/bin/env python3
import json
import fast_mssql

CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=BTQ_MarketData;"
    "UID=SA;"
    "PWD=<supersecretpassword>;"
    "TrustServerCertificate=yes;"
)

exchange = "binance"
symbol   = "BTCUSDT"
depth    = 20

sql = f"""
SELECT TOP (1) bids, asks
FROM dbo.orderbook_snapshots
WHERE exchange = '{exchange}'
  AND symbol   = '{symbol}'
  AND market_type = 'spot'
ORDER BY timestamp DESC;
"""

rows = fast_mssql.fetch_data_from_db(CONN_STR, sql)
if not rows:
    print("NO ROWS")
    raise SystemExit

bids_str, asks_str = rows[0]
bids = json.loads(bids_str) if bids_str else []
asks = json.loads(asks_str) if asks_str else []

print(f"raw bids: {bids}")
print(f"raw asks: {asks}")

bids = bids[:depth]
asks = asks[:depth]

print("\n  #        BidQty        BidPx        AskPx        AskQty      Spread")
print("---- ------------ ------------ ------------ ------------ ------------")
for i, (b, a) in enumerate(zip(bids, asks), start=1):
    bpx, bqty = float(b[0]), float(b[1])
    apx, aqty = float(a[0]), float(a[1])
    spread = apx - bpx
    print(f"{i:4} {bqty:12.5f} {bpx:12.5f} {apx:12.5f} {aqty:12.5f} {spread:12.5f}")
