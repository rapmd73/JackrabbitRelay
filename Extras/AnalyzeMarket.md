# Section 1 - Non-Technical Description

This program connects to a trading data provider configured by the environment, examines every market the provider exposes, and for each market prints a one-line summary that shows how high and low the market has been over the available monthly data, how large monthly price moves and spreads have been on average and at maximum, what portion of months exceeded the average move, and how long the historical data covers.

# Section 2 - Technical Analysis

The script is a Python program that uses a JackrabbitRelay object (from the JackrabbitRelay module) to load exchange/broker configuration, market definitions, and historical price data. Execution starts in main(), which constructs a JackrabbitRelay instance with a usage handler (Help). It queries that relay for the chosen exchange and account, then determines a price precision value based on the relay's framework string ("mimic" or "ccxt" use precision 8, "oanda" uses 5, otherwise the program exits).

The program retrieves the relay.Markets mapping and an optional search string from additional command-line arguments; if present it uppercases the search term and will later filter assets to only those whose name contains that term (unless the term is "ALL").

It prints a header line describing the columns, then iterates over each asset key in relay.Markets. For assets, if the relay framework is "ccxt" it skips assets whose name starts with a dot, contains ".d", or contains a space; it also skips assets explicitly marked with ['active'] == False in the market definition. Assets that do not match the optional search string are also skipped.

For each retained asset the program requests OHLCV (open-high-low-close-volume) data using relay.GetOHLCV with the highest timeframe available (relay.Timeframes[-1]) and a limit of 5000 candles. It initializes accumulators: mh for the highest observed price (set to 0), ml for the lowest observed price (set to a large number), wcp for a worst-case price high, mms for maximum monthly spread, maxMonth to store the candle with the largest spread, and lists spList and avgList for monthly spreads and individual price points.

It then loops over each candle in the returned OHLCV list. For each candle it inspects the three price fields at indices 1..3 (these correspond to open, high, low, or high/low depending on how OHLCV is ordered by the relay implementation). Within that inner loop it updates wcp, mh, ml with the maximum/minimum of those values, and appends each of those three values to avgList. After that inner loop it computes the monthly spread as slice[2] - slice[3], appends that to spList, and if this spread is larger than mms it updates mms and records the entire candle in maxMonth.

After processing all candles it computes sp as the market spread (mh - ml) rounded to the chosen precision. It sets htf to the highest timeframe string. It calculates the start and end timestamps using the first and last candle timestamps (ohlcv[0][0] and ohlcv[-1][0]), converting milliseconds-since-epoch to datetime strings, then to datetime objects; it computes the difference between end and start using dateutil.relativedelta and builds a short duration string containing years, months, and days present in that delta.

It computes market statistics: market median mmed as the midpoint of mh and ml rounded to precision; market average mavg as the mean of all values in avgList rounded to precision. It obtains the maximum monthly movement mmm from maxMonth as maxMonth[2] - maxMonth[3] rounded to precision, and the average monthly movement amm as the mean of spList rounded to precision. It computes percent values pmmm and pamm by dividing the maximum and average monthly movements by mh and converting to percentage (rounded to two decimals).

To count months with spread above average, it iterates spList and increments maa for each spread greater than amm. It sets lsp to the total number of monthly samples (len(spList)) and tfaa to the percentage of months above average (maa / lsp * 100, rounded to two decimals).

Finally it prints a formatted line for the asset containing: asset name, highest timeframe, maximum high (mh), maximum low (ml), market spread (sp), market median (mmed), market average (mavg), maximum monthly movement (mmm) with its percent pmmm, average monthly movement (amm) with its percent pamm, total number of monthly samples lsp, percentage of months above average tfaa, and the computed duration string dstr. The program wraps main() in a try/except to print "Terminated" on KeyboardInterrupt.

In summary, the program iterates assets, fetches up to 5000 highest-timeframe candles per asset, computes high/low/average/median/spread and monthly-movement statistics from those candles, and prints a one-line summary per asset including the analyzed time span.
