# Section 1 - Non-Technical Description

This program reads recent foreign-exchange price data for a currency pair, processes that data in a rolling fashion to compute a sequence of moving-average based indicators, and prints a summary display for each new data point as it is processed.

# Section 2 - Technical Analysis

The script is a Python program that imports several standard modules (sys, os, math, json, datetime, time) and Plotly plotting libraries, then imports two local modules: `JackrabbitRelay` as `JRR` and `JRRtechnical` as `jrTA`. It appends a specific directory to `sys.path` so the local modules can be found, then defines a `main()` function that drives the processing.

Inside `main()`, the code constructs a `TechnicalAnalysis` object by calling `jrTA.TechnicalAnalysis` with the arguments ('oanda','CherryBlossom','EUR/USD','M1',5000). It then calls `GetOHLCV()` on that object and assigns the returned data to `ohlcv`. (Two commented lines show an alternate construction and a file-read call that are not executed.)

The code establishes numeric constants for column indices into OHLCV records: `Opening=1`, `HighIDX=2`, `LowIDX=3`, `Closing=4`, and `Volume=5`. It then iterates over every element in `ohlcv` using `for slice in ohlcv:`. For each element (named `slice`), the program calls `ta.Rolling(slice)`. This indicates that the `TechnicalAnalysis` instance maintains an internal rolling window or history and `Rolling` updates that state with the current record.

Next the script sets up parameters and index constants used for indicator calculations: `SlowLength=50` and `period=21`. It defines indexes for intermediate computed series: `emaIDX=6`, `ema2IDX=7`, `synIDX=8`, `sqpIDX=9`, and `hmaIDX=10`. These numeric labels are passed into subsequent API calls and represent positions or identifiers within the `TechnicalAnalysis` object's internal data structures.

The program then computes a short sequence of exponential moving average (EMA) based operations in four method calls on `ta`:

- `ta.EMA(Closing,period)`: computes an EMA of the closing price with the window `period` (21) and stores it at index `emaIDX` (the code supplies only two arguments; how they map internally depends on the `EMA` implementation).
- `ta.EMA(Closing,int(period/2))`: computes an EMA of the closing price with window `period/2` (10) and stores it at index `ema2IDX`.
- `ta.HMA(emaIDX,ema2IDX,period)`: calls a method named `HMA` with the two EMA indexes and `period`. This call triggers the HMA-related math using the previously computed EMA series; the method likely computes an intermediate value and stores results in internal series (the code provides three arguments).
- `ta.EMA(synIDX,sqpIDX)`: calls `EMA` again with two index-like arguments `synIDX` and `sqpIDX`. In this script the comment says this call produces the "Actual HMA based on EMA"; as written it invokes the `EMA` method using the index values produced earlier. The effect is to compute a final EMA over the intermediate "synthetic" series stored at `synIDX`, with a smoothing length indicated by `sqpIDX`.

After performing these indicator computations for the current record, the program calls `ta.Display(-1)`. That display call passes -1, which commonly indicates "latest" or "most recent" in such APIs; the `Display` method prints or outputs diagnostic or summary information for the last entry in the rolling window.

The `main()` function processes every record in `ohlcv` this way: updating the rolling state, computing two EMAs, combining them via an HMA step, smoothing via another EMA call, and then outputting a display for the most recent data point. When the script is executed as a program (`if __name__ == '__main__'`), it runs `main()` and thus performs this sequential processing over the retrieved OHLCV data. The script does not produce plots or write files within the shown code; its observable actions are the sequence of method calls on `ta` and whatever output `ta.Display(-1)` produces.
