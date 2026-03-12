# Section 1 - Non-Technical Description

This program reads historical price data, computes several smoothed trend lines and a momentum line from that data, draws candlestick price charts together with those lines, and saves the resulting chart as an HTML file and a PNG image.

# Section 2 - Technical Analysis

The script imports a number of standard and third-party modules, then creates and runs a main() function when executed. In main(), it instantiates a TechnicalAnalysis object from the JRRtechnical module with parameters ('oanda','CherryBlossom','EUR/USD','1m',5000) and calls its ReadOHLCV method to load OHLCV data from the file "EURUSD.txt". The code defines integer labels for the OHLCV columns: Opening=1, HighIDX=2, LowIDX=3, Closing=4, Volume=5.

It constructs a Plotly subplot object with a single subplot (no secondary y-axis). It initializes empty lists to collect timestamps, open/high/low/close values and several indicator series (wma1, wma2, hma, zl, sw, mom).

The program iterates over each record ("slice") in the ohlcv dataset. For each record it tries to convert the first field to a Python datetime by treating the value as a millisecond timestamp; if that conversion fails it stores the raw first field. It appends the record's open, high, low, and close fields to the corresponding lists.

For each record the program calls ta.Rolling(slice) to feed the new row into the TechnicalAnalysis object's rolling-window storage. It sets several numeric configuration variables: SlowLength=50 and period=21, and defines a set of integer indices (wmaIDX..momIDX) that represent column positions inside the TechnicalAnalysis rolling window for intermediate and final indicator values.

The code then invokes a sequence of indicator calculations via methods on the TechnicalAnalysis instance:
- ta.WMA(Closing, period) and ta.WMA(Closing, int(period/2)) - compute weighted moving averages of the Close column for the full and half periods and store them into the rolling structure at the next available column positions.
- ta.HMA(wmaIDX, wma2IDX, period) - computes the intermediate combination "2 * WMA(p/2) - WMA(p)" using the previously stored WMA columns and stores that intermediate series.
- ta.WMA(synIDX, sqpIDX) - computes a WMA of the intermediate "raw hull" series using a sqrt(period) length to produce the final Hull Moving Average (HMA).
- ta.ZeroLag(hmaIDX, SlowLength) - computes a zero-lag transform of the HMA and stores it.
- ta.SineWeight(zlIDX, SlowLength) - computes a sine-weighted transform of the zero-lag HMA and stores it (producing the sine-weighted, zero-lag HMA).
- ta.SMA(Closing, 200) - computes a 200-period simple moving average of Close and stores it.
- ta.RateOfChange(momIDX) - computes a rate-of-change (momentum) series and stores it.

After these calls the code retrieves the most recent row of stored rolling values with ta.LastRow(). If that returned row is non-empty, it appends the values at the previously chosen column indices to the respective series lists: wma1, wma2, hma, zl, sw, and mom. It then calls ta.Display(-1) (presumably to show or log the most recent state).

After processing all rows, the program builds the chart: it adds a Plotly candlestick trace using the collected dt/open/high/low/close lists and then adds line traces for WMA(p), WMA(p/2), HMA, Zero Lag, Sine Weighted, and Momentum using the series collected during the loop. It sets the y-axis title to "Price", centers the chart title "Sine Weighted, Zero Lag, Hull Moving Average", applies the 'plotly_white' template, hides the x-axis range slider, and enables the legend.

Finally, the program writes the interactive chart to a file named "demo.sw-zl-hma.html" and exports a static PNG image "demo.sw-zl-hma.png" at 1920x1024 resolution. The script runs main() when executed as the main module.
