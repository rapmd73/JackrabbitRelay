# Section 1 - Non-Technical Description

This program repeatedly checks the current orders available for a specified financial asset on a chosen trading service and prints a concise summary whenever certain summarized order quantities or prices change; specifically, it finds the largest grouping of buy-side and sell-side interest near the current market prices within a given depth and logs those values with a timestamp.

# Section 2 - Technical Analysis

The script begins by importing modules and adding a specific directory to the import path, then imports two project-specific modules: JackrabbitRelay (as JRR) and JRRsupport. Two functions are defined to process order book data depending on which exchange framework is used: ccxtProcessOrderBook for the "ccxt" framework and oandaProcessOrderBook for the "oanda" framework.

ccxtProcessOrderBook(relay, asset, depth)
- Calls relay.GetTicker(symbol=asset) to obtain a ticker and reads Ask into BuyPrice and Bid into SellPrice, converting them to floats and rounding to 8 decimals.
- Calls relay.GetOrderBook(symbol=asset) to obtain an order book with 'asks' and 'bids' lists.
- Initializes counters and index markers (lp, sp, buyIDX, sellIDX) and sets l to the minimum of the lengths of asks and bids. If the requested depth is larger than l, depth is reduced to l.
- Iterates through the first l levels of the order book. For each level:
  - Reads bid price and quantity from orderbook['bids'][ob] and ask price and quantity from orderbook['asks'][ob].
  - Rounds prices to 8 decimals.
  - Tracks the index positions buyIDX and sellIDX by comparing current and previous prices against BuyPrice and SellPrice.
  - Accumulates total buy and sell quantities (lp and sp).
  - Appends per-level buy and sell entries to separate lists oblB and oblS.
  - Updates previous price trackers (ppB, ppS) and an index counter.
- After scanning levels, it scans depth levels starting from the identified buyIDX and sellIDX positions (adding increasing offsets) to find:
  - maxBorders: the maximum buy quantity among those depth-adjacent buy levels and the corresponding maxBprice.
  - maxSorders: the maximum sell quantity among those depth-adjacent sell levels and the corresponding maxSprice.
- Returns a tuple (maxBorders, maxBprice, maxSprice, maxSorders).

oandaProcessOrderBook(relay, asset, depth)
- Calls relay.GetTicker(symbol=asset) and assigns BuyPrice to ticker['Ask'] and SellPrice to ticker['Bid'] (no rounding here).
- Calls relay.GetOrderBook(symbol=asset) expecting a list of order book entries for Oanda.
- Initializes counters, buyIDX and sellIDX, an empty list obl, and index tracking.
- Iterates through the orderbook list. For each entry:
  - Reads buy as longCountPercent, price rounded to 4 decimals, and sell as shortCountPercent from the entry fields.
  - Uses price progression relative to BuyPrice and SellPrice to set buyIDX and sellIDX (with slightly different index adjustments than ccxt version).
  - Accumulates long and short totals (lp and sp).
  - Appends [buy, price, sell] to obl.
- After collecting levels, it iterates depth levels around buyIDX and sellIDX (subtracting for buy side, adding for sell side) and computes:
  - maxBorders and associated maxBprice from buy-side entries inspected.
  - maxSorders and associated maxSprice from sell-side entries inspected.
- Returns (maxBorders, maxBprice, maxSprice, maxSorders).

Main loop and orchestration
- Creates a JackrabbitRelay instance: relay = JRR.JackrabbitRelay().
- Reads command-line/relay-supplied arguments via relay methods. If fewer than five arguments (GetArgsLen() <= 4) it prints an error message and exits. Otherwise it extracts exchangeName, account, asset, and a depth parameter (converted to int) from relay methods.
- Calls relay.GetMarkets() and stores it in markets (not used further in the code).
- Initializes OLDmaxBorders, OLDmaxBprice, OLDmaxSprice, OLDmaxSorders to zero.
- Enters an infinite loop:
  - Captures current time as a formatted timestamp string with microsecond precision.
  - Checks relay.GetFramework() to determine which processing function to call:
    - If framework is 'ccxt', it calls ccxtProcessOrderBook(relay, asset, depth).
    - If framework is 'oanda', it calls oandaProcessOrderBook(relay, asset, depth).
  - Each processing call returns four values: maxBorders, maxBprice, maxSprice, maxSorders.
  - The loop compares each returned value against the corresponding OLD... variable. If any of the four returned values differ from their OLD values, it updates the OLD variables with the new values, computes spread as maxSprice - maxBprice, and prints a formatted line including the timestamp and numeric values. The printed order and formatting differ slightly between ccxt and oanda branches.
  - After the conditional printing, the loop calls JRRsupport.ElasticSleep(1), which delays before the next iteration.

Output behavior
- Whenever one of the computed summary values changes, the program prints a single line containing the timestamp and numeric summaries: maximum buy-side aggregated quantity found near the buy price, the associated buy price, the associated sell price, the maximum sell-side aggregated quantity (order dependent on framework branch), and the computed spread between the reported sell and buy prices. The exact order of printed numeric columns varies between the ccxt and oanda branches.
- The program runs continuously, periodically sleeping between iterations via JRRsupport.ElasticSleep(1).
