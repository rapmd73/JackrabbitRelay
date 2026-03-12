# Section 1 - Non-Technical Description

This program reads a file of historical price and volume data for the ADA/USD market, processes each row in order, calculates a moving average and two band values for each row, and prints a display line for each processed row to show the results.

# Section 2 - Technical Analysis

The script is a Python 3 program that sets up a runtime environment, imports modules, constructs a technical-analysis object, reads OHLCV data from a text file, and iterates through that data to compute indicators and display results.

- At the top it adjusts sys.path to include '/home/GitHub/JackrabbitRelay/Base/Library' and then imports standard modules (os, math, json, datetime, time) as well as two project-specific modules: JackrabbitRelay (aliased JRR) and JRRtechnical (aliased jrTA).

- The main() function constructs an instance of jrTA.TechnicalAnalysis with the arguments 'kraken', 'MAIN', 'ADA/USD', '1m', and 197. That instance is assigned to the variable ta. Immediately after, it calls ta.ReadOHLCV('ADAUSD.txt') and assigns the returned value to the variable ohlcv. This implies the program expects a file named ADAUSD.txt and that ReadOHLCV returns an iterable collection of rows (slices) representing OHLCV data.

- Several numeric constants are set up: SlowLength is set to 197; Opening is 1; HighIDX is 2; LowIDX is 3; Closing is 4; Volume is 5. These constants are used as index identifiers when passing column positions to the analysis methods.

- The program iterates over each element in ohlcv with "for slice in ohlcv:". For each slice (a single row of OHLCV data), it calls ta.Rolling(slice). That method receives the current row and presumably updates internal state in the ta object to include the new row in its rolling window or buffer.

- After rolling in the current row, the program sets emaIDX=6, then calls ta.EMA(Closing, SlowLength). This invokes the object's EMA method, passing the index number for the closing price (4) and the length 197, which instructs the object to compute an exponential moving average using the closing-price column and the 197-period length. The script intends that the resulting EMA value be stored in column index 6 of the internal row representation (emaIDX variable holds 6).

- Next it sets bbU=7 and bbL=8 and calls ta.BollingerBands(emaIDX, 20, 7). This calls the object's BollingerBands method with three arguments: the index where the EMA was stored (6), a period of 20, and a final argument of 7. From the call signature in the code, the method is invoked so that it computes upper and lower band values based on the EMA at index 6, with a 20-period lookback and the provided third parameter 7. The code's comments indicate the intent that the upper band will be stored in column 7 and the lower band in column 8, corresponding to bbU and bbL.

- After computing the EMA and Bollinger Bands for the current row, the program calls ta.Display(-1). This calls the TechnicalAnalysis object's Display method with -1 as the argument; based on usage this likely instructs the object to display or print the most recent row's data and computed indicators. The call occurs once per input row, so the program will output one display line per slice processed.

- The script's entry point checks if __name__ == '__main__' and calls main() when run as a script. There is no additional logging, error handling, or return value. The sequence of operations for each input row is: update internal rolling window with the row (Rolling), compute a 197-period EMA from the closing price and store it at index 6 (EMA), compute Bollinger Bands derived from that EMA using a 20-period lookback and parameter 7 storing results in indexes 7 and 8 (BollingerBands), and then output the current row and indicators via Display(-1). The constants at the top define the column indices that are passed to those methods.
