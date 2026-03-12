Section 1 - Non-Technical Description

This program reads command-like inputs to identify a market, account and asset, then looks up the current market price and uses the provided numeric values to calculate and display a proposed trade's size and price targets, including the per-pip cost, take-profit and stop-loss price levels, and a position size based on a fixed budget percentage.

Section 2 - Technical Analysis

The script begins by modifying Python's import path and importing several modules (os, json, time, random) plus two local modules: JRRsupport and JackrabbitRelay (aliased as JRR). It then constructs an instance of JRR.JackrabbitRelay and queries that object for argument-related values. Specifically, it calls relay.GetArgsLen() and, if that length is greater than 3, retrieves exchangeName via relay.GetExchange(), account via relay.GetAccount(), asset via relay.GetAsset(), and three argument values via relay.GetArgs(4), relay.GetArgs(5), and relay.GetArgs(6). The three GetArgs results are converted to floats and assigned to amount, tp, and sl. If GetArgsLen() is not greater than 3, the program prints an error message and exits with status 1.

After validating and extracting inputs, the program calls relay.GetMarkets() and relay.GetTicker(symbol=asset). It reads the ticker dictionary returned from GetTicker and computes price as the midpoint between ticker['Bid'] and ticker['Ask'] ((Bid + Ask)/2).

The script sets several constants and derived variables: pip_value is fixed at 0.0001, budget is fixed at 1000, and position_size is computed as 1% of the budget (budget * 0.01). take_profit_pips and stop_loss_pips are computed by multiplying the provided tp and sl floats by pip_value. Two intermediate values cost_per_pip_take_profit and cost_per_pip_stop_loss are computed by dividing the take_profit_pips and stop_loss_pips by the mid price and rounding the results to five decimal places.

The take-profit and stop-loss price levels (tp_price and sl_price) are computed by adding or subtracting the raw take_profit_pips or stop_loss_pips from the midpoint price and rounding to five decimal places.

pip_size is computed as (pip_value / amount) * price. The program then prints five lines of output: the computed "Cost of 1 pip" formatted to five decimal places, "Take Profit" computed as pip_size multiplied by take_profit_pips formatted to five decimals, "Stop Loss" as cost_per_pip_stop_loss formatted to five decimals, "Position Size:" followed by the numeric position_size value, and the string "Place Take Profit at:" followed by tp_price, and "Place Stop Loss at:" followed by sl_price.

In summary, the program obtains input parameters and a current market midpoint price from the JackrabbitRelay object, converts user-supplied values to pip-scaled quantities, computes per-pip cost and absolute price targets for take-profit and stop-loss, determines a fixed-percent position size from a hard-coded budget, and prints these computed values.
