# Section 1 - Non-Technical Description

This program reads a few pieces of information provided when it is run, looks up the current market price for a specified asset on a specified exchange, decides on a market price based on whether the user wants to buy or sell and whether the amount is positive or negative, sends an instruction to place a market order for that asset on the exchange, and then prints the result returned by the system that placed the order.

# Section 2 - Technical Analysis

The script begins by adding a fixed directory to the Python module search path and importing a module named JackrabbitRelay (aliased as JRR). It defines a Usage() function that prints required argument information and example command lines, then exits with status 1.

An instance of JRR.JackrabbitRelay is created and stored in the variable relay; the constructor is passed the Usage function (relay=JRR.JackrabbitRelay(Usage=Usage)). The script checks the number of command-line-like arguments available through relay.GetArgsLen(). If there are more than four arguments, it retrieves the exchange name with relay.GetExchange(), the account name with relay.GetAccount(), and an asset pair string with relay.GetAsset(). It also retrieves the action string from relay.GetArgs(4) and forces it to lowercase, and retrieves the amount from relay.GetArgs(5), converting that argument to a float. If insufficient arguments are present, the script calls Usage() and exits.

The script sets a boolean ro based on whether the last available argument (relay.GetArgs(-1)) lowercased equals the string "ro". It then obtains a market ticker by calling relay.GetTicker(symbol=asset). From the returned ticker object it reads two entries: 'Ask' into bPrice and 'Bid' into sPrice.

Next, the script computes a variable mPrice using a set of conditional branches based on the action string and the numeric sign of amount:
- If action is 'buy' and amount is greater than 0, mPrice is set to the maximum of bPrice and sPrice.
- If action is 'buy' and amount is less than 0, mPrice is set to the minimum of bPrice and sPrice.
- If action is 'sell' and amount is greater than 0, mPrice is set to the minimum of bPrice and sPrice.
- If action is 'sell' and amount is less than 0, mPrice is set to the maximum of bPrice and sPrice.

After determining mPrice, the script calls relay.PlaceOrder with these keyword arguments:
- pair set to asset
- orderType set to the literal string 'market'
- action set to the action string read earlier
- amount set to the floating-point amount
- price set to bPrice (the ticker 'Ask' value)
- ReduceOnly set to ro (the boolean indicating whether the last argument was 'RO')
- LedgerNote set to the fixed string 'CodeProofs/placeOrder'

The return value from relay.PlaceOrder is stored in result and then printed to standard output using print(result). The script therefore outputs whatever the PlaceOrder method returns after attempting to place the specified market order.
