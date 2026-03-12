# Section 1 - Non-Technical Description

This program repeatedly builds and updates a short series of recent price data for a particular market pair, computes technical values on that data, and prints the latest result ten times in a row, using a configured analysis setup for a specific exchange and trading pair.

# Section 2 - Technical Analysis

The script is a Python 3 program that imports modules and appends a specific local directory to the module search path before importing two project-specific modules: `JackrabbitRelay` (as JRR) and `JRRtechnical` (as jrTA). The script defines a `main()` function and runs it when executed as the main program.

Inside `main()`, it initializes an empty list named `ohlcv`. It then constructs an instance of `jrTA.TechnicalAnalysis` with the arguments `'kraken'`, `'MAIN'`, `'ADA/USD'`, `'1m'`, and `197`. This object is bound to the name `ta`. (There is an alternate constructor call commented out that would create a different `TechnicalAnalysis` object for OANDA and EUR/USD, but it is not used.)

The program enters a loop controlled by a counter `c` initialized to 0. The loop condition is `c < 10`, so the loop executes exactly ten times. On each iteration the following sequence occurs:

- It calls `ta.MakeOHLCV(seconds=60, synthetic=True)` and assigns the return value to the `ohlcv` variable. This call requests OHLCV (open-high-low-close-volume) candle data from the `ta` object, specifying a 60-second candle interval and indicating `synthetic=True`. The returned `ohlcv` replaces the previous contents of the `ohlcv` variable.
- It calls `ta.Rolling(ohlcv)`. This passes the newly obtained `ohlcv` data into the `ta` object's `Rolling` method. The code does not capture a return value from `Rolling`; the method is invoked for its side effects on the `ta` object's internal state.
- It calls `ta.Display(-1)`. This invokes the `Display` method of `ta` with an argument of `-1`. The code does not use a return value; `Display` is invoked for its side effect, which is expected to print or otherwise present information about the current state or most recent data point (index `-1` typically means the most recent element).
- It increments the counter `c` by 1 and repeats until the loop has executed ten times.

When the script is run directly (not imported), it executes `main()` and thus performs the ten iterations described above, each time obtaining fresh OHLCV data via `MakeOHLCV`, updating internal rolling calculations via `Rolling`, and producing output via `Display`. Outside of those calls, the script does not perform file I/O, network I/O, or other observable actions in the shown code; all substantive behaviors depend on the implementations of the `jrTA.TechnicalAnalysis` object and its `MakeOHLCV`, `Rolling`, and `Display` methods.
