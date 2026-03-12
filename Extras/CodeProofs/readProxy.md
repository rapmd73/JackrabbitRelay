## Section 1 - Non-Technical Description

This program connects to a service called Jackrabbit Relay and retrieves recent market information for a specified asset on a chosen exchange and account, then prints the current market quote and a short list of recent daily price records, followed by how long the retrieval took.

## Section 2 - Technical Analysis

The script starts by setting up Python 3 environment details and imports required modules: sys, os, json, time, and a module named JackrabbitProxy as JRP from a path appended to sys.path. It instantiates an object named proxy from JRP.JackrabbitProxy().

Immediately after creating the proxy, the script checks the number of command-line arguments via proxy.GetArgsLen(). If that reported length is greater than 3, it calls proxy.GetExchange(), proxy.GetAccount(), and proxy.GetAsset() to obtain strings for exchangeName, account, and asset respectively. If GetArgsLen() is not greater than 3, the program prints an error message "An exchange, (sub)account, and an asset must be provided." and exits with a nonzero status.

The program records the current time in sTime using time.time(). It then requests a ticker for the chosen asset by calling proxy.GetTicker(symbol=asset). The returned ticker object (or value) is printed to standard output, followed by a blank line.

Next, it requests OHLCV (open-high-low-close-volume) candle data for the asset by calling proxy.GetOHLCV(symbol=asset, timeframe='1d', limit=5). The call requests daily candles and asks for up to five data points. The script iterates over the returned ohlcv iterable; for each candle in that iterable it prints the candle on its own line. After printing the candles it prints another blank line.

Finally, the script computes the elapsed time by subtracting sTime from the current time and prints a line showing the elapsed seconds formatted with six significant digits (formatted as {time:.6}). No further actions are taken and the script ends.

Variables and calls used:
- proxy: instance of JackrabbitProxy used as the interface to obtain arguments and market data.
- proxy.GetArgsLen(): determines whether sufficient arguments were provided.
- proxy.GetExchange(), proxy.GetAccount(), proxy.GetAsset(): obtain strings identifying the exchange, account, and asset.
- sTime: timestamp recorded before market data requests.
- proxy.GetTicker(symbol=asset): retrieves the current market ticker for the asset; printed directly.
- proxy.GetOHLCV(symbol=asset, timeframe='1d', limit=5): retrieves up to five daily OHLCV candles for the asset; each returned candle is printed.
- The script prints elapsed time as a final output line.

Control flow:
- If argument length check fails, the program prints an error and exits.
- If the check passes, the program fetches and prints the ticker, fetches and prints up to five daily candles, then prints elapsed time.
