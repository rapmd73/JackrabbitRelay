# Section 1 - Non-Technical Description

This program analyzes historical price data for a chosen market instrument and reports summary information about how that market has moved over time. It determines the highest and lowest observed prices, how frequently price candles fall above or below central measures, the largest and average monthly movements, the time span covered by the data, and an overall average spread across several timeframes, then prints those results.

# Section 2 - Technical Analysis

The program begins by importing modules and a custom JackrabbitRelay library, then constructs a JackrabbitRelay object named relay. It requires at least three command-line arguments (exchange, account, asset); if they are present it retrieves those values from the relay object, otherwise it prints an error and exits.

Next it determines numeric precision based on the framework returned by relay.GetFramework(). If the framework is 'mimic' or 'ccxt' it sets precision to 8. If the framework is 'oanda' it reads a pipLocation value for the selected asset from relay.Markets and sets precision to the absolute integer of that value. If the framework is unrecognized the program prints an error and exits.

The program then attempts to obtain OHLCV (Open, High, Low, Close, Volume-style) historical candle data for the asset. It sets tf to -1 and repeatedly calls relay.GetOHLCV with the timeframe relay.Timeframes[tf] and limit 5000 until a non-empty list is returned; effectively it tries the highest available timeframe (the last element of relay.Timeframes) and steps down if needed. Once it has ohlcv data, it iterates over each candle (named slice in the code). For each candle it examines indices 1..4 (these represent price-related fields in the candle structure as used here) and:

- Updates wcp to the maximum value seen across those fields (wcp starts at 0).
- Updates mh (market high) to the maximum observed value.
- Updates ml (market low) to the minimum observed value.
- Appends each examined field to avgList for later average calculation.

For each candle it computes a monthly spread ms as slice[2] - slice[3] and appends ms to spList. If this ms is larger than the current maximum monthly spread mms, it updates mms and records that entire candle as maxMonth.

After processing all candles the program computes sp as mh - ml and prints the selected timeframe string for the asset.

It then computes the time span covered by the ohlcv data: it converts the timestamp of the first candle (ohlcv[0][0]) and the timestamp at index tf (ohlcv[tf][0]) into datetime strings, parses them, creates a relativedelta between them, and prints the resulting years, months, and days as the timeframe duration.

The program prints the maximum market high, minimum market low, and highest market spread, formatting numbers to the previously determined precision.

If the relay.Framework attribute equals 'mimic' or 'ccxt' the program calls relay.GetMinimum(symbol=asset), receives minimum and mincost, and prints the minimum amount/units and minimum cost, again formatted to the set precision.

It computes a market median mmed as (mh + ml) / 2 and a market average mavg as the average of all values stored in avgList. It then counts candles that lie entirely above or entirely below the median: for each candle it checks the same indices 1..4, counts how many of those four fields are above the median and how many are below; if all four are above it increments ca, if all four are below it increments cb. It computes spl as the remainder of candles that are neither fully above nor fully below. It prints the market median and the counts and percentages of candles above, below, and split relative to the number of candles.

The program repeats the same above/below/split counting procedure using the market average mavg instead of the median, and prints the market average and percentages.

It computes the maximum monthly movement mmm from maxMonth as the difference between indices 2 and 3 of that stored maxMonth candle, and the average monthly movement amm as the mean of spList. It prints both the maximum and average movement for the chosen timeframe, including each movement as an absolute number formatted to precision and as a percent of mh.

Next it counts how many monthly spreads in spList exceed the average monthly movement amm (stored in maa), computes the total number of months lsp as len(spList), and prints total months analyzed and the count and percentage of months above average.

Finally, the program computes average spreads across all defined timeframes in relay.Timeframes. For each timeframe it fetches up to 5000 OHLCV candles, then for each candle iterates indices 1..4 updating per-timeframe mh and ml and appending mh - ml to a local spList for that timeframe. It computes an average spread for each timeframe and collects those averages in a list avg. After processing all timeframes it computes avgsp as the mean of the timeframe averages and prints "Average pip spread/all TF" followed by that number formatted with four decimal places.
