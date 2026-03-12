# Section 1 - Non-Technical Description

This program reads historical price and volume data for a specific asset, processes each row in sequence using a technical analysis component, computes a short-term rate of change, and displays the analysis results as it progresses through the dataset.

# Section 2 - Technical Analysis

The script is a Python program that begins by extending the module search path to include a specific local library directory, then imports several standard libraries (os, math, json, datetime, time) and two custom modules: JackrabbitRelay (aliased JRR) and JRRtechnical (aliased jrTA).

The main routine constructs an instance of a TechnicalAnalysis class from the jrTA module by calling jrTA.TechnicalAnalysis with five string and numeric arguments: the strings 'kraken' and 'MAIN', the trading pair 'ADA/USD', the timeframe '1m', and the integer 197. This object is assigned to the variable ta.

Next, the program calls ta.ReadOHLCV with the filename 'ADAUSD.txt'. The return value of that call is stored in the variable ohlcv; based on naming conventions in the code, ohlcv is expected to be an iterable collection (such as a list) of rows, where each row represents an open-high-low-close-volume (OHLCV) data slice.

The code defines several integer variables that appear to be index constants for fields within each OHLCV row:
- Opening = 1
- HighIDX = 2
- LowIDX = 3
- Closing = 4
- Volume = 5

These are used to indicate which position in a row corresponds to each data field.

The program then iterates over each element in ohlcv using a for loop with the loop variable named slice. For each slice (each OHLCV row), three methods on the TechnicalAnalysis object ta are called in sequence:
1. ta.Rolling(slice) - the current row is passed to a method named Rolling, which presumably updates the internal rolling data structures or state with the new slice.
2. ta.RateOfChange(Closing,10) - the program requests a rate-of-change computation; it passes the Closing index constant (value 4) as the field to operate on and the integer 10 as the period over which to compute the rate of change.
3. ta.Display(-1) - the program calls Display with -1 as the argument, which causes the TechnicalAnalysis object to output or render its current analysis state for the latest data point.

Finally, the standard Python conditional if __name__ == '__main__': triggers the execution of main() when the script is run as a program.

In summary, the program initializes a technical analysis object for ADA/USD on a 1-minute timeframe, reads OHLCV data from 'ADAUSD.txt', iterates through each data row, updates internal rolling data, computes a 10-period rate-of-change on the closing price field for each new row, and displays the analysis result after processing each row. The code relies entirely on the behavior implemented in the imported jrTA.TechnicalAnalysis class for data handling, calculation, and display.
