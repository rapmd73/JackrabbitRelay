# Section 1 - Non-Technical Description

This program connects to a trading relay, looks up the currently open trades for a given asset on a specified exchange and account, picks the single trade that has been open the longest, and prints a one-line summary of that trade including when it opened, its identifier, whether it is a long or short position, the number of units, the price, unrealized profit/loss, and financing amount.

# Section 2 - Technical Analysis

The script starts by setting up its import paths and importing standard Python modules (sys, os, json, datetime, time) plus two project-specific modules: JRRsupport and JackrabbitRelay (aliased JRR). It defines a helper function GetOldestTrade(relay, pair) that uses the relay object to fetch open trades for the given symbol (pair) and returns the trade dictionary whose recorded open time is the earliest.

Inside GetOldestTrade:
- It calls relay.GetOpenTrades(symbol=pair) to obtain a list of open trade dictionaries.
- If the returned list is empty, the function returns None.
- If there are open trades, it initializes oldestTrade to None and oldestTime to the current epoch time (time.time()).
- It then iterates over each trade in openTrades. For each trade it:
  - Reads the trade['openTime'] string and splits it at the period ('.') into parts.
  - Reconstructs a timestamp string dsS by taking parts[0], a period, the first six characters of parts[1], then appending a 'Z'. This produces a string in the form YYYY-MM-DDTHH:MM:SS.ffffffZ (UTC with microseconds).
  - Parses dsS into a datetime object using datetime.datetime.strptime with format '%Y-%m-%dT%H:%M:%S.%fZ'.
  - Converts that datetime to a POSIX timestamp (seconds since epoch) via ds.timestamp().
  - Compares this timestamp ts to oldestTime; if ts is smaller (earlier), it updates oldestTime and sets oldestTrade to the current trade dictionary.
- After checking all trades, it returns the oldestTrade dictionary (or None if none were provided).

In the main driver code:
- It creates an instance of JRR.JackrabbitRelay and assigns it to relay.
- It checks relay.GetArgsLen() to see how many arguments were provided; if the returned value is greater than 3, it retrieves exchangeName, account, and asset by calling relay.GetExchange(), relay.GetAccount(), and relay.GetAsset() respectively. If GetArgsLen() is not greater than 3, it prints an error message "An exchange, (sub)account, and an asset must be provided." and exits with status 1.
- It calls GetOldestTrade(relay, asset) and stores the result in variable o.
- It then extracts and converts several fields from the trade dictionary o:
  - iu = int(o['currentUnits']) - currentUnits converted to an integer.
  - price = float(o['price']) - price converted to a float.
  - upl = float(o['unrealizedPL']) - unrealized profit/loss converted to a float.
  - fin = float(o['financing']) - financing converted to a float.
- It determines the side: if iu >= 0 it sets side to 'L' (representing long), otherwise 'S' (representing short).
- Finally, it prints a single formatted line summarizing the trade. The printed fields are:
  - o['openTime'] - the original open time string from the trade dictionary.
  - o['id'] - formatted to occupy at least 7 characters right-aligned.
  - side - the single-character position side ('L' or 'S').
  - abs(iu) - the absolute value of the integer units, formatted with no decimal places and a width of 4 characters.
  - price - shown with 10 characters width and 5 decimal places.
  - upl - shown with 9 characters width and 5 decimal places.
  - fin - shown with 9 characters width and 5 decimal places.

The program thus produces exactly one line of output describing the oldest open trade for the chosen asset on the specified exchange/account, unless there were insufficient command arguments (in which case it prints the error message and exits) or there were no open trades (in which case GetOldestTrade would return None and subsequent field accesses would attempt to read from None, as the code proceeds to extract fields from o).
