# Section 1 - Non-Technical Description

This program connects to a trading service and prints out the current account information, including which trading framework and exchange are being used, followed by a listing of available funds and any open trading positions in a human-readable table format; the exact balance and position output depends on which backend framework the program detects.

---

# Section 2 - Technical Analysis

The script begins by importing a custom module named JackrabbitRelay and creating an instance of JackrabbitRelay called relay. It then checks the number of command-line arguments (via relay.GetArgsLen()). If there are more than two arguments, it retrieves the exchange name and account by calling relay.GetExchange() and relay.GetAccount(); if not, it prints an error message and exits with status 1.

It reads relay.Markets into a local variable markets and obtains the active trading framework string via relay.GetFramework(), converting it to lowercase and storing it in framework. The program prints the framework name, exchange name, and account, then prints a separator line.

The remainder of the program branches based on the value of framework. For each supported framework it calls relay.GetBalance() and sometimes relay.GetPositions(), then formats and prints the returned data. The supported framework branches are 'ccapi', 'ccxt', 'oanda', and 'mimic'. If framework does not match any of these, the program prints an "Unknown framework" message listing supported frameworks and exits with status 1.

- Framework: 'ccapi'
  - Prints a header indicating balances via CCAPI.
  - Calls relay.GetBalance() and expects a dictionary. If the dictionary contains a 'free' key, it iterates over coin identifiers in balances['free']. For each coin it retrieves numeric values from balances['free'] and balances['total'], converts them to floats, and prints only coins where either free or total is greater than zero. The output uses fixed-width columns labeled "Asset", "Free", and "Total".
  - If relay.Active contains a 'Market' key and its value (lowercased) is not 'spot', the script prints a positions header and calls relay.GetPositions(), expecting a list. If the list has entries it prints a table header and iterates positions. For each position dictionary it converts the 'contracts' field to float; if that value is nonzero and the position has a 'symbol' key, it retrieves side, entryPrice, and unrealizedPnl (converting numerics to floats) and prints symbol, absolute contract count, side, entry price, and unrealized PnL with fixed-width numeric formatting.

- Framework: 'ccxt'
  - Prints a header indicating balances via CCXT.
  - Calls relay.GetBalance() and expects a structure with a 'free' mapping. It prints a table header and iterates the keys in balances['free'], converting balances['free'][coin] and balances['total'][coin] to floats and printing only those coins where both free and total are greater than zero. Columns printed are "Asset", "Free", and "Total".
  - If relay.Active contains a 'Market' key and it is not 'spot' (case-insensitive), it prints a positions header and calls relay.GetPositions(), expecting a list. It prints a table header and iterates positions. For each position it converts pos['contracts'] to float (and treats None by setting bal to 0.0 afterward). If bal is nonzero and the position has a 'symbol', it converts pos['contractSize'] to float, gets side (falls back to 'unkn' if side is None), and prints symbol, absolute contract count, side, and contract size.

- Framework: 'oanda'
  - Prints a header indicating a single balance value via Oanda.
  - Calls relay.GetBalance() and, if not None, prints a single "Balance" value formatted with five decimal places.
  - Prints a positions header and calls relay.GetPositions(), expecting a list. If positions are present it prints a table header and iterates each position dictionary. For each position it:
    - Converts the instrument field by replacing underscores with slashes.
    - Calls relay.GetPositions(symbol=asset) to obtain a numeric position balance for that instrument.
    - Converts pos['marginUsed'] to a float and rounds it to two decimal places.
    - Determines side as 'long' if the returned balance is >= 0, otherwise 'short'.
    - Prints instrument, absolute balance (formatted), side, and margin.

- Framework: 'mimic'
  - Prints a header indicating balances via Mimic.
  - Calls relay.GetBalance() and, if not None, prints a table header "Asset", "Balance", "Side" and iterates over items in the returned balance mapping. For each coin it converts the mapped value to float; if negative it sets side to 'short', otherwise 'long'; it then prints the asset name, the absolute balance, and the side.

After handling the chosen framework branch, the script prints a final separator of equals signs and the word "Done". Throughout, the program expects specific structures (dictionaries, lists, numeric string values) from relay.GetBalance(), relay.GetPositions(), and related relay attributes, and it formats and prints the results in aligned columns depending on the branch taken.
