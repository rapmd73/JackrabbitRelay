# Section 1 - Non-Technical Description

This program loads a set of recent currency market data for the EUR/USD pair and then steps through each time record, updating a technical analysis engine and computing a specific trend indicator called the parabolic SAR for each new record, printing a display line for each step so you can see how the analysis evolves over time.

# Section 2 - Technical Analysis

The script begins by extending Python's import path to include a specific directory and then imports several standard libraries (os, math, json, datetime, time) and two custom modules: JackrabbitRelay (as JRR) and JRRtechnical (as jrTA). The main() function constructs an instance of jrTA.TechnicalAnalysis using five constructor arguments: the strings 'oanda' and 'CherryBlossom', the instrument 'EUR/USD', the timeframe 'M1', and the integer 5000. Immediately after construction it calls GetOHLCV() on that object to retrieve a sequence of OHLCV (open, high, low, close, volume) data slices.

Index name variables for fields are defined: Opening = 1, HighIDX = 2, LowIDX = 3, Closing = 4, Volume = 5. These are set but not otherwise manipulated in the provided code; they suggest the expected positions of values within each OHLCV slice.

The program then iterates over each slice in ohlcv. For each slice it performs three calls on the TechnicalAnalysis instance:

- ta.Rolling(slice): This call passes the current OHLCV slice into the analysis object's rolling-window update routine. It updates internal state to incorporate the new record into the rolling analysis window.

- ta.PSAR(startAF=0.01, stepAF=0.01, maxAF=0.2): After updating the window, the code invokes the PSAR calculation method with explicit parameters startAF = 0.01, stepAF = 0.01, and maxAF = 0.2. This computes or updates the parabolic SAR indicator values based on the current rolling data and the supplied acceleration factor parameters.

- ta.Display(-1): Finally, the Display method is called with argument -1. This prints or otherwise outputs a representation of the current analysis state for the most recent record (the -1 index indicates the last element). The example header and rows in the file show the format that Display produces: a timestamp followed by numeric columns for Open, High, Low, Close, Volume, and then additional computed indicator columns such as +DI, -DI, ADX, Crossing distance, and Crossing direction. When earlier rows lack computed indicators, Display shows placeholder dashes for those columns.

The script runs main() when executed as a program. There is no file I/O, network logic, or other visible side effects in this file beyond constructing the TechnicalAnalysis object, iterating through the OHLCV data returned by GetOHLCV, computing PSAR for each slice, and outputting a display line per slice. The included commented example shows how the printed output lines align with column descriptions and example numerical values for successive timestamps.
