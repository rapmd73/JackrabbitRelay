# Section 1 - Non-Technical Description

This program repeatedly watches one or more currency pairs and automatically places, replaces, and closes market trades using an OANDA trading relay according to configuration rules; it keeps a history of recent price ticks, computes simple statistics (like average price, spread, and volatility), decides whether to open new buy or sell positions or close existing ones based on those metrics and configured thresholds, logs actions, and enforces margin limits while running in an endless loop.

# Section 2 - Technical Analysis

Overall structure
- The program is a Python script that reads a JSON-based configuration file (path supplied as the first command-line argument), then enters an infinite loop where it processes each configured currency pair in turn. For each pair it creates a JackrabbitRelay object configured for OANDA, gathers market data and account/trade state, updates stored ticker history, computes derived metrics, then manages long or short positions by sending market orders via the relay. It logs order activity and periodically persists ticker data to disk.

Configuration reading
- ReadConfig(fname) reads the configuration file line-by-line, parsing each non-empty, non-comment line as JSON. Each parsed JSON object must contain required keys (Account, Asset, PipProfit, MarginPips, UnitPips, UnitStart, UnitStep, MarginLimit, Direction, Clustering, ClusterStyle, Confidence, Confirmation, Volatility). Missing optional keys receive defaults (MarginPips, UnitPips, Clustering, ClusterStyle, Confidence, Confirmation, Volatility). Each configuration entry is stored in a dictionary keyed by "Asset.Account". ReadConfig also converts Confidence to float if needed and initializes per-pair flags First and BuyPips.

Ticker data storage and update
- Ticker data are kept on disk in files under oandaBotTickerData. The file name used is "{Account}.{Asset-without-slash}.ticker". LoadTickerData(Config, ticker) reads that file into a list of JSON-decoded tick dictionaries, keeps only the most recent 86,400 entries, and appends the incoming tick if it differs from the last saved tick by both Bid and Ask. When appending a new tick, it computes and stores summary fields on that tick: LenBA (length of loaded historical list), SumBA (sum of Bid or Ask values depending on configured Direction), MaxBA and MinBA (max/min Bid or Ask). After updating the in-memory representation it calls SaveTickerData to overwrite the ticker file with the stored list. SaveTickerData toggles a SignalInterceptor into a critical state while writing and calls SafeExit at the end.

Order sending and identification
- SendOrder(relay, **kwargs) builds a market order dictionary with Identity, Exchange, Account, Asset and action details (Action, Units, optional Ticket) and invokes relay.SendWebhook(Order). It returns whatever result string the relay returns. GetOrderID(res) attempts to find the substring "Order Confirmation ID" in the returned string and, if found, extracts a following "ID:" value by scanning until a newline character; if not found it returns None.

Utility math functions
- isPrime(n) and ClosestPrime(n) provide primality testing and a nearest lower prime selection: ClosestPrime returns 2 for n <= 2, otherwise it returns a prime less than or equal to n with special behavior (if n itself is prime and greater than 2 it decrements to the next lower prime). This is used to select starting lot sizes or steps when UnitStart or UnitStep are configured as "prime".

Order book and price prediction helpers
- GetOrderBookDirection(relay, Config) requests an order book for the asset from the relay, inspects the middle half of the orderbook price levels (center ±25% of length), sums longCountPercent and shortCountPercent over that slice, normalizes to percentages, stores obDirection in Config as either 'long' or 'short' depending on which side is dominant, and returns the updated Config. If the order book is empty it returns 'closed'.
- PredictConsolidatedPrice(relay, Config) computes a simple mean and standard deviation of recent prices from Config['TickerData'] (summing Bids for a long-direction config or Asks for short). It computes a predicted_price (mean) and a confidence percentage based on 1 - (std_dev / mean), scaled down if the number of ticks n is less than 14,400. It returns (predicted_price, confidence).
- CalculatePipProfits(relay, Config) averages the stored tick Spread values across recent TickerData and returns the mean spread (rounded).
- CalculateVolatilityPips(relay, Config) computes the standard deviation of Bid or Ask values (depending on Direction), converts that to a relative percentage (std_dev / mean * 100) and scales it down by 0.001; the function returns this rounded volatility value.

Position and clustering logic helpers
- AlreadyBought(relay, asset, price, pipDistance) checks open trades for a given asset and returns True if any existing trade's price is within ±pipDistance of the provided price (after rounding). This function prevents placing overlapping orders unless clustering allows it.
- AllowClustering(relay, Config) returns True only when Config['Clustering'] is 'yes', marginLimit is above 30, marginUsed is below 73% of marginLimit, confidence from PredictConsolidatedPrice meets or exceeds Config['Confidence'], and (if Confirmation is 'Yes') the order book direction matches the configured Direction; otherwise it returns False.
- ClusterStyle(openTrades, relay, pair, Config) returns a lot size chosen by either HighestLotSize or LowestLotSize depending on ClusterStyle and whether marginUsed is below 73% of marginLimit.
- LowestLotSize and HighestLotSize iterate through existing open trades' currentUnits to find the smallest or largest next available lot size step. They interpret UnitStart and UnitStep values; if UnitStart or UnitStep is 'prime' they call ClosestPrime on a value derived from marginLimit. LowestLotSize increments the candidate until it finds a size not present among open trades. HighestLotSize inspects current units and returns the next higher size.

Margin and position lookup
- GetMarginUsed(relay, asset) inspects relay.GetPositions() and returns marginUsed for the matching instrument (instrument name in positions uses underscores replaced with slashes). If not found it returns 0.

Long and short management routines
- ManageLongs(relay, pair, Config, ticker)
  - Updates marginUsed and openTrades.
  - Obtains order book direction via GetOrderBookDirection.
  - Determines whether clustering is allowed via AllowClustering and sets a clusterStr to annotate logs.
  - Scans all openTrades to find the lowest entry price and, for each positive (long) open trade, computes a sellPrice at price + pipStep + BuyPips + ticker.Spread. If the current Bid >= sellPrice, it sends a Close action for that trade and, if the close is confirmed, logs the event and refreshes open trades.
  - After closing a profitable long trade it may place a replacement buy order at the trade's fill price if another nearby order does not already exist (via AlreadyBought) or if clustering is allowed, subject to marginLimit checks. Replacement order units are chosen by ClusterStyle; new positions increase marginUsed by relay.Markets[pair]['marginRate'] multiplied by lot size, and placement only occurs if marginLimit is unlimited (negative) or newPos is less than marginLimit. On success it logs the replacement and records BuyPips from the current ticker Spread.
  - If no open trades and Config['First'] is True and margin is permitted, it issues an initial buy order using LowestLotSize and sets First to False and BuyPips to ticker.Spread on success.
  - Finally, it computes the next buy threshold as (lowestPrice - pipStep - BuyPips - marginPips - unitPips - VolatilityPips - ticker.Spread). If the current ticker Bid is below this threshold and no overlapping trade exists (or clustering is allowed), it chooses a lot size via ClusterStyle and places a new buy order (subject to margin checks). On success it logs and updates BuyPips.
  - The function returns the updated Config.

- ManageShorts(relay, pair, Config, ticker)
  - Mirrors ManageLongs but inverted: it tracks highestPrice among open trades, closes negative-unit (short) trades when ticker Ask is at or below a computed sellPrice (price - pipStep - BuyPips - Spread), and places replacement short orders (negative Units) where appropriate. It places an initial short if Config['First'] is True by sending a buy with negative units. It computes a trigger for adding an additional short as highestPrice + pipStep + BuyPips + marginPips + unitPips + VolatilityPips + ticker.Spread and opens a short if ticker Ask exceeds that trigger, subject to AlreadyBought, clustering, and margin checks. It returns the updated Config.

Main loop behavior
- After reading the configuration, the script removes the configuration argument from sys.argv (so it does not interfere with the relay framework) and enters while True:
  - For each configured pairAccount key in Config:
    - Records start time and creates a relay object JRR.JackrabbitRelay for the pair and account.
    - Reads account balance via relay.GetBalance and stores it in Config[pairAccount]['balance'].
    - Retrieves open trades via relay.GetOpenTrades and the current ticker via relay.GetTicker.
    - Calls LoadTickerData to load and update ticker history for the pair (this may rewrite the per-pair ticker file).
    - Sets Config[pairAccount]['Price'] to ticker Bid or Ask according to Direction.
    - Updates marginUsed and computes marginLimit either from a percentage of balance (if MarginLimit string contains '%') or as an absolute float; ensures marginLimit does not exceed balance.
    - If marginLimit > 0, it subtracts the absolute value of unrealizedPL across open trades plus marginUsed from marginLimit, ensuring marginLimit remains non-negative. This effectively reduces usable margin allowance by current unrealized losses and currently used margin.
    - Sets marginPips = marginUsed * 0.0001 and unitPips based on HighestLotSize * 0.0001.
    - Computes pipStep using CalculatePipProfits (average spread) and, if MaxBA and MinBA are present on the latest ticker data item, increases pipStep by (MaxBA - MinBA) / 100.
    - Computes VolatilityPips via CalculateVolatilityPips.
    - Ensures BuyPips is initialized from ticker.Spread if not set.
    - Routes to ManageLongs or ManageShorts depending on Direction.
    - After trading logic, it sets Config[pairAccount]['TickerData'] to None and invokes gc.collect() to free memory.
    - Computes loop elapsed time and prints a formatted status line including elapsed time, direction initial (L or S), forex session string from GetForexSession(), account name, asset pair, number of open trades, BuyPips, pipStep, marginPips, unitPips, VolatilityPips, ticker Spread, balance, marginUsed and marginLimit.
    - Calls interceptor.SafeExit() and sleeps using JRRsupport.ElasticSleep(1) before continuing.
  - After processing all pairs, it prints a blank line and continues the outer infinite loop.

Signal handling and file safety
- At startup an interceptor object of type JRRsupport.SignalInterceptor is created. SaveTickerData sets the interceptor into a critical state while the ticker file is being overwritten, then clears it and calls interceptor.SafeExit(). After each iteration of the main loop interceptor.SafeExit() is called again. These calls provide coordinated behavior around exits and file writes.

Logging and relay interactions
- Orders and trade replacements are executed by building order dictionaries and invoking relay.SendWebhook(Order) or relay.GetOrderDetails(OrderID). The script writes log messages via relay.JRLog.Write with formatted messages that include session, order id, action and sizes. The program relies on relay methods for market data (GetTicker, GetOrderBook), account and trade state (GetBalance, GetOpenTrades, GetPositions), market definitions (relay.Markets), and order execution/confirmation strings.

End result
- The program runs continuously, maintaining a persistent per-pair local ticker history, periodically computing simple statistical signals and constraints (pipStep, volatility, clustering allowance) and creating, closing, and replacing market trades for configured currency pairs while respecting computed margin budgets and avoiding placing orders too close to existing ones unless clustering rules permit it. It logs events and prints per-iteration status lines to standard output.
