# Section 1 - Non-Technical Description

This program reads a saved list of cryptocurrency price data for the ADA/USD pair, processes each row one at a time through a technical analysis component, computes a momentum indicator for each row, and displays the most recent analysis output repeatedly until all data rows have been handled.

# Section 2 - Technical Analysis

The script is a Python 3 program that imports modules from the file system and two project-specific modules named JackrabbitRelay (aliased JRR) and JRRtechnical (aliased jrTA). In its main function it constructs an instance of the TechnicalAnalysis class from jrTA by calling jrTA.TechnicalAnalysis('kraken','MAIN','ADA/USD','1m',197). The constructor receives five arguments: the exchange identifier 'kraken', a label 'MAIN', the trading pair 'ADA/USD', the timeframe '1m', and the numeric value 197. The created object is assigned to the variable ta.

Next, the program calls ta.ReadOHLCV('ADAUSD.txt'), passing the filename 'ADAUSD.txt'. The return value from ReadOHLCV is stored in the variable ohlcv; this is expected to be an iterable collection of rows (slices) representing OHLCV data read from that file.

Five integer variables are then defined: Opening is set to 1, HighIDX to 2, LowIDX to 3, Closing to 4, and Volume to 5. These variables serve as indices or labels for the positions of open, high, low, close, and volume within each OHLCV slice; they are used later when calling technical analysis methods.

The program enters a loop that iterates over each element in ohlcv. For each slice (each row of OHLCV data) the following steps occur in order:
- ta.Rolling(slice) is invoked with the current slice as its argument. This call hands the current row to the technical analysis object; the method is expected to update internal rolling or windowed state inside ta with the new data.
- ta.Momentum(Closing) is called with the Closing variable (value 4). This instructs the technical analysis object to compute a momentum-related calculation using the index 4 (close price) from the most recent data in its internal state.
- ta.Display(-1) is called with -1 as the argument. This requests the technical analysis object to produce output for display; the -1 argument indicates that the most recent or last computed result should be displayed.

After processing all slices in ohlcv, the main function ends. The script's usual Python entry-point check if __name__ == '__main__' calls main(), causing this behavior to execute when the file is run as a script.

Outside of main, at the top of the file, the script appends the path '/home/GitHub/JackrabbitRelay/Base/Library' to sys.path before importing project modules, ensuring those local modules can be found. The script also imports standard libraries os, math, json, datetime, and time, though none of those are directly used within the visible code. The displayed program does not write files or accept user input; all observable I/O is performed by the ReadOHLCV method reading 'ADAUSD.txt' and by the Display method producing visible output via the technical analysis object.
