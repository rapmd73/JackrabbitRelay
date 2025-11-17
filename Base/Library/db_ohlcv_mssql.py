from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List
import time

import fast_mssql

#  Connection config
@dataclass
class MSSQLFeedConfig:
    server: str = "localhost"
    database: str = "BTQ_MarketData"
    username: str = "SA"
    password: str = "q?}33YIToo:H%xue$Kr*"
    driver: str = "{ODBC Driver 18 for SQL Server}"
    trust_server_certificate: bool = True

    def connection_string(self) -> str:
        trust = "yes" if self.trust_server_certificate else "no"
        return (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate={trust};"
        )

# OHLCV reader (candles)

class ReadOnlyOHLCV:
    """
    mode="global":
        Single table (global_table) with columns:
        (exchange, symbol, timeframe, timestamp, open, high, low, close, volume)

    mode="per_pair":
        One table per symbol, based on table_pattern, e.g. "{symbol}_klines".
    """

    def __init__(
        self,
        config: MSSQLFeedConfig,
        mode: str = "global",
        global_table: str = "ohlcv",
        schema: str = "dbo",
        table_pattern: str = "{symbol}_klines",
    ) -> None:
        if mode not in ("global", "per_pair"):
            raise ValueError("mode must be 'global' or 'per_pair'")
        self.config = config
        self.mode = mode
        self.global_table = global_table
        self.schema = schema
        self.table_pattern = table_pattern
        self._conn_str = config.connection_string()

    @staticmethod
    def _sym_compact(symbol: str) -> str:  # BTC-USDT -> BTCUSDT
        return symbol.replace("/", "").replace("-", "").replace("_", "")

    @staticmethod
    def _sym_underscore(symbol: str) -> str:  # BTC-USDT -> BTC_USDT
        return symbol.replace("/", "_").replace("-", "_")

    @staticmethod
    def _qv(s: str) -> str:
        return s.replace("'", "''")

    @staticmethod
    def _ident(s: str) -> str:
        # Quote as [name], escaping any closing bracket
        s = s.replace("]", "]]")
        return f"[{s}]"

    def _table_exists(self, schema: str, table: str) -> bool:
        q = (
            "SELECT 1 FROM sys.tables t "
            "JOIN sys.schemas s ON s.schema_id=t.schema_id "
            f"WHERE s.name='{self._qv(schema)}' AND t.name='{self._qv(table)}'"
        )
        rows = fast_mssql.fetch_data_from_db(self._conn_str, q)
        return bool(rows)

    def _table_name(self, exchange: str, symbol: str) -> str:
        """
        In per_pair mode try, in order:
          1) table_pattern(symbol)         -> DASHUSDT_klines
          2) table_pattern(sym_underscore) -> DASHUSDT_klines (same here)
          3) table_pattern(sym_compact)    -> DASHUSDT_klines
        First existing table wins.
        """
        if self.mode == "global":
            return f"{self._ident(self.schema)}.{self._ident(self.global_table)}"

        ex = (exchange or "").lower()

        sym_orig = symbol
        sym_us   = self._sym_underscore(symbol)
        sym_cmp  = self._sym_compact(symbol)

        cand_symbols: list[str] = []
        for s in (sym_orig, sym_us, sym_cmp):
            if s not in cand_symbols:
                cand_symbols.append(s)

        candidates: list[str] = []
        for s in cand_symbols:
            tbl = self.table_pattern.format(exchange=ex, symbol=s)
            if tbl not in candidates:
                candidates.append(tbl)

        for tbl in candidates:
            if self._table_exists(self.schema, tbl):
                return f"{self._ident(self.schema)}.{self._ident(tbl)}"

        # deterministic failure if none exist
        return f"{self._ident(self.schema)}.{self._ident(candidates[0])}"

    def get_ohlcv(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
        strict_gt: bool = False,
    ) -> List[dict]:
        """
        Return a list of dicts:
        [timestamp, open, high, low, close, volume]
        """
        if end is None:
            end = datetime.now(timezone.utc)

        fqtn = self._table_name(exchange, symbol)
        comp = ">" if strict_gt else ">="
        top_clause = f"TOP {int(limit)} " if limit else ""

        # NOTE: no .%f here; pure second precision to keep SQL literal simple
        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
        end_str   = end.strftime("%Y-%m-%d %H:%M:%S")

        if self.mode == "global":
            ex = self._qv(exchange)
            sym = self._qv(symbol)
            tf  = self._qv(timeframe)
            query = (
                f"SELECT {top_clause}"
                f"timestamp, [open], high, low, [close], volume "
                f"FROM {fqtn} "
                f"WHERE exchange='{ex}' AND symbol='{sym}' AND timeframe='{tf}' "
                f"AND timestamp {comp} '{start_str}' AND timestamp < '{end_str}' "
                f"ORDER BY timestamp ASC;"
            )
        else:
            tf = self._qv(timeframe)
            query = (
                f"SELECT {top_clause}"
                f"timestamp, [open], high, low, [close], volume "
                f"FROM {fqtn} "
                f"WHERE timeframe='{tf}' "
                f"AND timestamp {comp} '{start_str}' AND timestamp < '{end_str}' "
                f"ORDER BY timestamp ASC;"
            )

        # Uncomment for one-shot debugging if something still explodes
        print("DEBUG OHLCV SQL:", query)

        rows = fast_mssql.fetch_data_from_db(self._conn_str, query)
        cols = ["timestamp", "open", "high", "low", "close", "volume"]
        return [dict(zip(cols, r)) for r in rows]

# Trades reader (raw ticks)

class ReadOnlyTradesAgg(ReadOnlyOHLCV):
    """
    Simple reader for raw trades from dbo.trades.

    NOTE:
      For tick mode, each trade is exposed to Backtrader as a 1-tick "bar" with:
        open = high = low = close = price
      This is perfect for microstructure / tick strategies, but NOT for ATR/ASI/etc.
      For those, use candle mode (OHLCV).
    """

    @staticmethod
    def _qv(s: str) -> str:
        return s.replace("'", "''")

    def _retry_fetch(self, sql: str, retries: int = 4, base_delay: float = 0.05):
        for i in range(retries):
            try:
                return fast_mssql.fetch_data_from_db(self._conn_str, sql)
            except RuntimeError as e:
                msg = str(e).lower()
                if "deadlock" in msg or "1205" in msg:
                    time.sleep(base_delay * (2 ** i))
                    continue
                raise

    def get_ticks_by_id(
        self,
        exchange: str,
        symbol: str,
        last_id: int,
        limit: int = 1000
    ) -> list[dict]:
        """
        Fetch trades with id > last_id and return list of dicts:
        [id, timestamp, open, high, low, close, volume]
        """
        aliases = {
            symbol,
            symbol.replace("-", "/"),
            symbol.replace("/", "-"),
            symbol.replace("/", ""),
            symbol.replace("-", ""),
            symbol.replace("/", "_"),
        }
        syms = "', '".join(self._qv(s) for s in sorted(aliases))
        ex = self._qv(exchange.lower())

        sql = f"""
            SELECT TOP ({int(limit)}) t.id, t.[timestamp], t.price, t.quantity
            FROM dbo.trades AS t WITH (READPAST, ROWLOCK)
            WHERE t.exchange='{ex}'
              AND t.symbol IN ('{syms}')
              AND t.id > {int(last_id)}
            ORDER BY t.id ASC
            OPTION (MAXDOP 1, OPTIMIZE FOR UNKNOWN, RECOMPILE);
        """

        rows = self._retry_fetch(sql)
        out = []
        for rid, ts, price, qty in rows:
            out.append(
                {
                    "id": int(rid),
                    "timestamp": ts,
                    "open": float(price),
                    "high": float(price),
                    "low": float(price),
                    "close": float(price),
                    "volume": float(qty),
                }
            )
        return out


