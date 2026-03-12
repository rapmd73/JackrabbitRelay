# Section 1 - Non-Technical Description

This program retrieves a set of financial price records for a specific currency pair and timeframe, processes those records one at a time to maintain a moving window, computes two successive simple moving averages over a short period for the closing prices, and prints or displays the current processed record after each update.

# Section 2 - Technical Analysis

The script begins by adjusting the module search path and importing standard libraries (os, math, json, datetime, time) and Plotly plotting modules. It then imports two project-specific modules: JackrabbitRelay as JRR and JRRtechnical as jrTA. The main work happens inside the main() function.

Inside main(), an instance of jrTA.TechnicalAnalysis is created with five string/number arguments: the strings 'oanda', 'CherryBlossom', 'EUR/USD', 'M1', and the integer 5000. The code calls the GetOHLCV() method on that TechnicalAnalysis instance and stores its return value in the variable ohlcv. The script then defines integer constants that act as column or field indices: Opening=1, HighIDX=2, LowIDX=3, Closing=4, and Volume=5.

The code then iterates over each element in ohlcv using a for loop variable named slice. For each slice, it calls the instance method Rolling(slice) on the TechnicalAnalysis object, which updates the internal rolling window or state with the current slice. After updating the rolling state, the code sets a variable period to 5 and defines sma1IDX=6 and sma2IDX=7 to label positions used for moving-average values.

Next, the code calls the instance method SMA(Closing, period). This computes a simple moving average based on the data located at the index indicated by Closing (which is 4) over the window length specified by period (5) and stores the result internally at a position corresponding to sma1IDX. Immediately after, the code calls SMA(sma1IDX, period) a second time, which computes a simple moving average of the previously computed SMA values over the same period and stores that second SMA at a different internal position (sma2IDX). The comments describe this sequence as computing a triangular moving average (TMA) by applying a double simple moving average: first the SMA of closing prices, then the SMA of that SMA.

Finally, for each processed slice the code calls ta.Display(-1). This invokes the TechnicalAnalysis object's Display method with -1 as an argument; based on the naming and usage this produces output for the most recent entry of the rolling window (for example printing, logging, or plotting the most recent state), so each iteration results in a displayed representation of the current processed record including the newly computed moving averages.

The script uses the standard Python module guard if __name__ == '__main__' to call main() when executed as a program. The overall behavior is a single-pass processing loop over returned OHLCV records that updates a rolling state, computes a 5-period simple moving average of closing prices, computes a 5-period SMA of that SMA (double SMA / TMA), and displays the latest state after each update.
