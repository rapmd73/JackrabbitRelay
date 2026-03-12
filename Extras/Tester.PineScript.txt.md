# Section 1 - Non-Technical Description

This program watches price data from a chart and marks when the current opening price is higher than the current closing price as a "buy" condition, and when the current closing price is higher than the current opening price as a "sell" condition. It counts how many buy and sell events occur, computes elapsed time shown in days, and displays those counts and the elapsed time on the chart. It also raises alert conditions and draws small markers on the chart when buy or sell conditions happen.

# Section 2 - Technical Analysis

The script is a TradingView Pine Script v5 indicator named "Tester" that runs on chart price data. It declares a persistent label variable lblStats to hold on-chart statistics text and defines a helper function fprint that creates or updates a label at a given timestamp and price coordinate on the last realtime bar. The fprint function computes an x time coordinate using the current bar time and an offset multiplier, and either creates a new label or updates the existing label's position, text, color, and alignment.

User inputs control DCA testing (testDCA, a string "Yes" or "No"), a TakeProfit percentage (TakeProfit, entered as percent then divided by 100), and a color for stats text (colStats).

The script copies the chart's open and close series into local variables so and sc. It declares persistent (var) counters and accumulators: sum (float) and count (int) for averaging price during DCA accumulation, lp (last purchase price, float), tb (total buys, int) and tc (total cycles or total sells, int).

BuySignal is computed as so > sc (open greater than close). SellSignal is computed as sc > so (close greater than open). These booleans are used to increment counters and manage DCA state.

When a BuySignal is true:
- tb is incremented unconditionally.
- If testDCA is "Yes", the code enters a DCA accumulation routine:
  - If count is 0 (no prior accumulated buys in the current cycle), it sets lp to the current close, adds the close to sum, increments count.
  - If count > 0, it compares sc to lp: if sc < lp, it updates lp to sc, adds sc to sum, and increments count; otherwise it cancels the buy by setting BuySignal to false.

The script computes an average price as sum / count and a take-profit level tp = average + (average * TakeProfit). Note: this average and tp are computed each bar using current sum and count variables.

When a SellSignal is true:
- If testDCA is "Yes" and count > 0, it checks if sc > tp. If sc > tp then it treats this as closing a DCA trade cycle: increments tc, and resets sum and count to zero. If sc is not above tp it cancels the sell by setting SellSignal to false.
- If testDCA is not "Yes" or count == 0, it increments tc and resets sum and count.

The script then computes elapsed time for display. It attempts to get the time of the first bar (using ta.valuewhen(bar_index == 1, time, 0)) as firstBarTime, uses timenow for lastBarTime, and computes elapsed days as (timeEnd - timeStart) / 86400000. It constructs a text string txt that includes the elapsed days formatted to two decimal places. Depending on testDCA, it appends either "Trade Cycles" and "Total Buys" or "Total Sells" and "Total Buys" to the txt string, using tc and tb values.

It calls fprint with lblStats, the constructed txt, the current close price sc as the y coordinate, the selected color, and zero offset; it assigns the returned label to ls and then updates lblStats to ls, so the same label persists and is updated on the last realtime bar.

Finally, the script registers two alertconditions named "BUY ASSET" (triggered when BuySignal is true) and "SELL ASSET" (triggered when SellSignal is true). It plots small shape markers on the chart: an upward triangle at the bottom for BuySignal and a downward triangle at the top for SellSignal, both with nearly black color and tiny size, titled "Buy" and "Sell" respectively.

Overall, the program continuously evaluates each bar for simple open-vs-close buy/sell conditions, optionally accumulates multiple buys into an average for a DCA cycle, detects sells when the close exceeds a computed take-profit level, counts events, displays statistics, triggers alerts, and plots markers.
