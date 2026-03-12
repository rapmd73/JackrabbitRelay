# Section 1 - Non-Technical Description

This program connects to a specified trading account on a chosen exchange, gathers recent price history for the exchange's listed markets (optionally filtered by a search string), computes how closely each market's recent percent price movements match every other market, and produces a visual chart (either an image or an HTML file) showing those pairwise correlation values as a colored heatmap.

# Section 2 - Technical Analysis

The script starts by importing modules, appending a specific library directory to Python's path, and importing two local modules: JRRsupport and JackrabbitRelay (aliased as JRR). It defines a helper function CalculateCorrelation(list1, list2) that computes the Pearson correlation coefficient for two equally sized numeric lists and returns the value rounded to four decimal places; if the lists differ in length or the denominator would be zero, it returns 0.

The program expects command-line arguments. It requires at least three arguments: an output type flag (first argument) indicating Image or Html, an exchange name (second argument), and an account identifier (third argument). If provided, a fourth argument is treated as an optional asset search string used to filter which markets are processed. The script then removes the processed command-line arguments from sys.argv (by repeatedly removing sys.argv[1] until only the program name remains).

A JackrabbitRelay object is instantiated with the provided exchange name and account. The code sets a data and chart directory paths: DataDirectory is fixed to /home/JackrabbitRelay2/Data and chartDir becomes DataDirectory/Charts/.

It retrieves a list of markets from relay.GetMarkets(). Based on relay.Framework it selects a candle timeframe: if the framework string is 'ccxt' it sets TimeFrame to '1d', if 'ccapi' it sets '1m', and if 'oanda' it sets 'D'; otherwise it prints an unsupported-framework message and exits. (This selection is determined by conditional checks in the code.)

An ohlcv dictionary is initialized with an empty list for each market returned by GetMarkets(); if an asset search string was provided, only markets whose identifiers contain that search string are included. The program prints "Processing markets" and then iterates over the markets (again skipping those that don't match the search if one was supplied).

For every selected market, the code requests OHLCV data via relay.GetOHLCV(symbol=asset, timeframe=TimeFrame, limit=count) with count set to 5000, then takes all but the last returned candle (slicing to [:count-1]) to avoid the incomplete current candle. From those candles it extracts the close price of the first candle as a reference cZ, then for each candle computes:
- timestamp: converting the candle's first element (assumed to be a millisecond epoch) to a datetime and formatting it as YYYY-MM-DD,
- roc: the percent rate-of-change of that candle's close relative to cZ, computed as ((c - cZ) / cZ) * 100 and rounded to five decimal places.

For each market the script stores two lists in ohlcv[asset]: the list of date strings and the list of rate-of-change values in the same order.

After collecting data for all selected markets, it sorts the market keys alphabetically into a list al. It ensures the chart directory exists by calling JRRsupport.mkdir(chartDir). It then prepares to build the heatmap: for each market assetV in al it creates a row cpData, and for each market assetH in al it computes the correlation between the rate-of-change lists previously stored (ohlcv[assetV][1] and ohlcv[assetH][1]) by calling CalculateCorrelation; the returned correlation values fill cpData, and the list of rows is assembled into hmData. Thus hmData is a square matrix of correlation values, ordered by the sorted market list al.

The script builds a Plotly figure: it constructs a subplot figure, adds a semi-transparent background image (the URL https://rapmd.net/RAPMDlogo.png) centered in the figure with low opacity, and adds a Heatmap trace with x and y axes labeled by the market list al and z values from hmData. The heatmap uses a manually specified colorscale mapping 0 to red (#ff0000), 0.5 to yellow (#ffff00), and 1 to green (#00ff00). The figure layout receives a centered title "Heatmap of (Inverse) Correlated Pairs" and the 'plotly_white' template.

Finally, the program determines an output filename: it composes chartDir + exchangeName + '.' + account + '.Heatmap.html' if the first argument indicated HTML output, otherwise it uses '.Heatmap.png'. It writes the figure to that filename using fig1.write_html(fn) for HTML output or fig1.write_image(fn, width=1920, height=1024) for image output. The observable result is a heatmap file saved to the chart directory illustrating pairwise correlations of recent percent price movements across the selected markets.
