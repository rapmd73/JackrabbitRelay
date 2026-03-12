# Section 1 - Non-Technical Description

This program loads historical currency price data, processes it step by step through a set of technical-analysis routines, and prints or otherwise displays analysis results for each new data point as it iterates through the dataset.

# Section 2 - Technical Analysis

The script is a Python program that imports several standard libraries and Plotly modules, then imports two local modules: `JackrabbitRelay` (as JRR) and `JRRtechnical` (as jrTA). It appends a specific directory to `sys.path` so that those local modules can be imported. The program defines a single `main()` function and runs it when executed as a script.

Inside `main()`, the program constructs an instance of `jrTA.TechnicalAnalysis` with five string/number arguments: the strings 'oanda', 'CherryBlossom', 'EUR/USD', 'M1' and the integer 5000. It calls the instance method `GetOHLCV()` to obtain OHLCV data (open, high, low, close, volume) and stores that in the variable `ohlcv`.

The program then defines integer constants that map to positions in the OHLCV record: `Opening=1`, `HighIDX=2`, `LowIDX=3`, `Closing=4`, and `Volume=5`. These constants are not used elsewhere in the presented code beyond their assignment.

The main processing loop iterates over each element in `ohlcv` using `for slice in ohlcv:`. For each `slice` (each record or time step), it calls the `Rolling()` method of the `ta` object with the current `slice`. This suggests the `Rolling` method updates an internal rolling window or internal state with the new data point.

Within the loop the code sets local variables `period=14`, `viP=6`, and `viM=7`. These are used as parameters or index references for subsequent method calls. The program then calls `ta.Vortex()`; this call runs the Vortex indicator calculation (as implemented inside `jrTA.TechnicalAnalysis`). Immediately after, it calls `ta.Cross(viP,viM)`, which executes a cross-detection routine using the arguments 6 and 7 (likely indicating which internal indicator series or columns to compare). Finally, for each iteration it calls `ta.Display(-1)`, which displays or outputs the most recent result from the `ta` object's internal state (the `-1` argument indicates the last element).

When the script is run directly (not imported), `main()` is executed and this per-slice processing is carried out for every record returned by `GetOHLCV()`. The program relies on methods and data from the `jrTA.TechnicalAnalysis` class-specifically `GetOHLCV`, `Rolling`, `Vortex`, `Cross`, and `Display`-to manage data ingestion, run indicator calculations, detect crosses, and present the results. The flow is therefore: create analysis object → retrieve OHLCV series → for each record update rolling state → compute the Vortex indicator → check for crosses between two indicator series (indices 6 and 7) → display the latest analysis output. The script ends after iterating through all records.
