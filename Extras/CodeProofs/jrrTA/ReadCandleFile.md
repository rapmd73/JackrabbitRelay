Section 1 - Non-Technical Description

This program loads a set of historical market price entries for the ADA/USD trading pair, feeds them into a technical analysis component to build an internal window of recent candles, and then prints how many candles were read followed by a printed representation of the last ten items in that internal window.

Section 2 - Technical Analysis

The script is a Python3 executable that modifies the module search path to include /home/GitHub/JackrabbitRelay/Base/Library, then imports several standard libraries (os, math, json, datetime, time) and two project-specific modules: JackrabbitRelay (as JRR) and JRRtechnical (as jrTA). It defines a main() function and calls it when run as a script.

Inside main(), it initializes an empty list named ohlcv. It creates an instance named ta of jrTA.TechnicalAnalysis with the arguments 'kraken', 'MAIN', 'ADA/USD', '1m', and 197. It then calls ta.ReadOHLCV('ADAUSD.txt') and assigns the returned value to ohlcv. Immediately after reading, it prints a line "Candles read: N" where N is the length of the ohlcv list as determined by len(ohlcv).

Next, it iterates over each element s in the ohlcv list and calls ta.Rolling(s) for each element in sequence. This loop feeds every candle/record from the ohlcv list into the ta.Rolling method, building whatever internal state or window the TechnicalAnalysis object maintains.

After populating the rolling window, the code computes a start index as len(ta.window) - 10 and iterates from that start index up to len(ta.window) - 1 inclusive. For each index s in that range it calls ta.Display(s). In other words, it invokes the Display method of ta for the last ten entries of ta.window (or fewer if ta.window has fewer than ten entries, subject to how the language handles negative start indices in range). The program produces console output: first the "Candles read: ..." line and then whatever textual output ta.Display writes for each of those last ten window entries.

The script ends after main() returns. All file reading, window-building, and display behavior are performed by the TechnicalAnalysis object's ReadOHLCV, Rolling, and Display methods; this script acts as a driver to read the ADAUSD.txt data file, feed it into the technical analysis object, and show the final ten window items.
