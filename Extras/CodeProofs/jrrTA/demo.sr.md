# Section 1 - Non-Technical Description

This program reads historical market price data for a currency pair from a technical analysis helper, processes each new data entry in sequence, computes short-term resistance and support values, computes a midline between those resistance and support values when both exist, and displays the results for each processed row.

# Section 2 - Technical Analysis

The script is a Python program that imports a custom technical analysis module (JRRtechnical) and uses it to obtain and process OHLCV (open, high, low, close, volume) data for a currency instrument. It sets up the Python path to include a specific library directory, imports standard libraries (os, math, json, datetime, time) as well as two project modules (JackrabbitRelay as JRR and JRRtechnical as jrTA), then defines and runs a main() function when executed as a script.

Inside main(), the program constructs a TechnicalAnalysis object from the jrTA module with parameters ('oanda','CherryBlossom','EUR/USD','M1',5000). It calls GetOHLCV() on that object to retrieve a sequence of OHLCV rows. The code defines numeric indices for row fields: Opening=1, HighIDX=2, LowIDX=3, Closing=4, Volume=5. For each row in the OHLCV sequence it does the following:

- Calls ta.Rolling(slice) to feed the current row into the technical analysis object's rolling update routine.
- Defines two additional indices rIDX=6 and sIDX=7, which the code expects to correspond to resistance and support values stored in the technical analysis object's last row representation.
- Calls ta.Resistance(HighIDX,50) to compute or update resistance values based on the value at index 2 (high) and a lookback or window size of 50.
- Calls ta.Support(LowIDX,50) to compute or update support values based on the value at index 3 (low) and a lookback or window size of 50.
- Calls ta.LastRow() to obtain the most recently processed row (a sequence or list-like object) from the technical analysis object, and extracts h = lr[rIDX] and l = lr[sIDX], which correspond to the resistance and support values produced by the previous calls.
- If both h and l are truthy (non-None, non-zero), the program computes their average (h + l) / 2 and calls ta.AddColumn((h+l)/2) to append that midline value to the current row in the technical analysis object. If either h or l is not present, it calls ta.AddColumn(None) to add a placeholder.
- Calls ta.Display(-1) to display or print the last row (the most recent row) after the new column has been appended.

After processing all rows from GetOHLCV(), the script ends. When run directly (if __name__ == '__main__'), the main() function is executed. The program therefore iterates through historical OHLCV data, updates resistance and support using 50-period calculations, derives a midpoint between resistance and support when both exist, adds that midpoint as an extra column to the data, and displays the updated row for each step.
