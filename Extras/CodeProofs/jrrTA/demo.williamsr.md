# Section 1 - Non-Technical Description

This program reads historical trading data for a cryptocurrency pair and processes each record sequentially to compute and show a specific technical indicator, updating its internal state as it goes and printing the latest results after each record.

# Section 2 - Technical Analysis

The script is a Python program that imports modules and a local technical analysis library (JackrabbitRelay and JRRtechnical). In the main() function it constructs an instance of a TechnicalAnalysis object from the jrTA module with the arguments: exchange string 'kraken', a name 'MAIN', the trading pair 'ADA/USD', a timeframe '1m', and a window size 197. It then calls the ReadOHLCV method on that object to load OHLCV data from the file named 'ADAUSD.txt' into a variable named ohlcv.

The code defines integer constants for column indices used by the OHLCV data: Opening = 1, HighIDX = 2, LowIDX = 3, Closing = 4, and Volume = 5. It then iterates over each element in the ohlcv sequence with "for slice in ohlcv:".

For every slice (each record) in the ohlcv list, the script performs three operations on the TechnicalAnalysis instance in order:
1. Calls ta.Rolling(slice) - this updates the internal rolling/windowed data structures of the TechnicalAnalysis object with the current slice.
2. Calls ta.WilliamsR(HighIDX,LowIDX,Closing,14) - this asks the TechnicalAnalysis object to compute the Williams %R indicator using the provided column indices for high, low, and close and a period length of 14. The method is invoked on every slice as it is processed.
3. Calls ta.Display(-1) - this requests the TechnicalAnalysis object to display or print output related to its current state; passing -1 likely selects the most recent element or a particular display mode, as used by the object.

The module-level guard if __name__ == '__main__': ensures main() is executed only when the script is run directly. The script does not handle command-line arguments, exceptions, or alternative data sources; it uses a hardcoded file path and module import path modifications at the top (sys.path.append) before importing the JackrabbitRelay and JRRtechnical modules. The program thus sequentially reads records from the specified file, updates its internal rolling window with each record, computes Williams %R with a 14-period setting for each new record, and prints or displays the current analysis output after each record.
