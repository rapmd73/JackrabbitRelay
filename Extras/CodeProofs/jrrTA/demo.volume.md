Section 1 - Non-Technical Description

This program reads a sequence of market data records for the ADA/USD trading pair, performs a set of simple rolling calculations on each incoming record (including a 50-period average of volume, a one-period rate of change of volume, and a derived percentage comparing current volume to that average), and for each record it displays the latest computed row and a binary flag that marks records meeting a specific set of conditions (a rising price candle and both the volume-percent and volume-rate-of-change exceeding 30). The program processes all records in the provided data file and prints output for each processed record.

Section 2 - Technical Analysis

The script begins by importing modules and appending a specific path to sys.path so it can import two custom modules: JackrabbitRelay (aliased JRR) and JRRtechnical (aliased jrTA). The main function constructs an instance of jrTA.TechnicalAnalysis with parameters ('kraken','MAIN','ADA/USD','1m',197). It then reads OHLCV data from the file "ADAUSD.txt" via ta.ReadOHLCV(), storing the returned sequence in the variable ohlcv.

Several integer constants are defined that map to positions in the data rows: Opening=1, HighIDX=2, LowIDX=3, Closing=4, Volume=5. SlowLength is set to 50 and will be used as the length for a simple moving average.

The program iterates over each element named slice in the ohlcv sequence. For every slice it calls ta.Rolling(slice) - which, from the name and usage, updates the internal rolling window or state inside the TechnicalAnalysis object with the new record.

After rolling in the new record, the code requests the computation of a simple moving average of the Volume column by calling ta.SMA(Volume, SlowLength). That call is intended to append or update a moving-average column at index maIDX (maIDX is set to 6 just before the call, although the code does not use maIDX as an argument to SMA). Next it computes a rate-of-change of the Volume column for a 1-period difference by calling ta.RateOfChange(Volume,1); the code sets vrocIDX=7 before that call, suggesting the result will occupy column index 7 in the internal row representation.

The code sets vpctIDX=8 to indicate the intended index for a derived percentage column. It then retrieves the current latest row with row = ta.LastRow(). It checks whether the moving-average column at index maIDX is not None. If that moving-average value exists, it computes pct = ((row[Volume] - row[maIDX]) / (row[Volume] + row[maIDX])) * 100, and calls ta.AddColumn(pct) to append that percentage value to the current row. If the moving-average is None, it appends None instead by calling ta.AddColumn(None). After this step, the new percentage value will occupy the next column slot in the row (which the code expects to be vpctIDX).

The program then evaluates a condition to decide whether to mark the record as a candidate signal. It checks that the percentage column at vpctIDX is not None and that the rate-of-change column at vrocIDX is not None. It also checks that the current closing price is greater than the opening price (row[Closing] > row[Opening]), and that both row[vpctIDX] and row[vrocIDX] exceed 30. If all these conditions are true, it appends a 1 by calling ta.AddColumn(1); otherwise it appends a 0 by calling ta.AddColumn(0). This appended value becomes a final flag column for that row.

Finally, for each processed record the program calls ta.Display(-1), which prints or displays the most recent row (including the original OHLCV fields plus the added columns) to the program's output. The main function processes every record in the file in this way. When the script is run as the main program, main() is invoked and the whole sequence is executed from start to finish.
