# Section 1 - Non-Technical Description

This program looks up price summaries for many trading symbols on a chosen exchange or broker, computes how close the latest price is to that symbol's recent high and low, and prints a short line for each symbol showing the symbol name and two percentages indicating closeness to the high and to the low.

# Section 2 - Technical Analysis

The program starts by importing several modules and creating a signal interceptor object for running concurrent child tasks. It constructs a relay object (JackrabbitRelay) from which it obtains the exchange name, account, framework type, available markets, and other settings. It also determines a title and numeric precision based on the relay framework.

Main workflow:
- It sets a list of day windows (unused later) and determines a search filter string (default "ALL" or taken from command-line arguments).
- It iterates over all market symbols listed in relay.Markets. For each symbol it:
  - Skips symbols with leading periods, symbols containing ".d" or spaces, or symbols flagged as inactive (for ccxt/mimic frameworks).
  - Skips symbols that do not contain the search substring if a search filter is provided.
  - For each remaining symbol, it starts a child process via interceptor.StartProcess that calls GetChildOHLCV with arguments: exchange name, account, symbol, and a chosen timeframe.
  - It throttles launching children so the number of concurrent children does not exceed the CPU count by sleeping while too many children exist.
- After launching tasks for all symbols, it waits until all child processes have finished.

GetChildOHLCV behavior (executed in child tasks):
- It constructs a JackrabbitRelay instance for the provided exchange/account/asset triple.
- It calls GetOHLCV on that relay for the given symbol/timeframe with a limit of 5000 bars. If the call fails or returns fewer than 2 bars, the child returns early.
- It computes the highest high and lowest low across the returned OHLCV set and takes the close of the last bar.
- It builds a small dictionary containing 'high', 'low', and 'close'.
- It constructs identifiers (id and mid) based on exchange.account.asset and obtains two locker objects using JRRsupport.Locker with those IDs.
- It locks, serializes the data dictionary as JSON text, stores it into the memory locker (mdata.Put) with a TTL of 86400 seconds, and unlocks.

Back in the main process after children complete:
- The program loops again over relay.Markets (applying the same search filter).
- For each symbol it constructs the same id and mid and obtains lockers, locks, retrieves the stored JSON string (mdata.Get), erases that memory key (mdata.Erase), and unlocks.
- It tries to parse the stored string expecting a JSON structure where the actual OHLC data is under key 'DataStore' (the code attempts json.loads(data['DataStore']...)). If parsing fails, it skips that symbol.
- If parsing succeeds, it extracts numeric values for high, low, and close from the parsed object.
- It calls closeness_to_high_low(h, l, c), which:
  - Computes the total range r = high - low and raises an exception if r is zero.
  - Computes distances from close to high and low: dist_to_h = high - close and dist_to_l = close - low.
  - Converts those distances into percentages of the range: pct_to_h = (dist_to_h / r) * 100 and pct_to_l = (dist_to_l / r) * 100.
  - Returns (pct_to_h, pct_to_l).
- The main loop prints a formatted line for each symbol: the symbol truncated/padded to 30 characters, then the percent-to-high and percent-to-low formatted with two decimal places and a percent sign.

The program runs main() when executed as a script and prints "Terminated" on KeyboardInterrupt. Auxiliary functions include WriteLog (which timestamps a message and appends it to a file) and ProcessDay (which parses and aggregates lists of timestamped "Fear/Greed/Strength" entries into averages for a given day window), though ProcessDay and WriteLog are not invoked by the main flow shown. The program uses an external Discord webhook URL variable (DiscordWH) but does not use it in the displayed execution path.
