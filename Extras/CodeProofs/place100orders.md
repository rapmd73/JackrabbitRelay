# Section 1 - Non-Technical Description

This program repeatedly places up to one hundred market orders for a specified asset on a chosen exchange account, starting with a provided amount and increasing that amount by one unit after each order; it fetches current quote prices before each order and prints the exchange's response for every order it attempts.

# Section 2 - Technical Analysis

The script begins by importing system, path, operating system, and JSON modules, then appends a specific library directory to the Python module search path and imports a module named JackrabbitRelay as JRR. It creates an instance of JRR.JackrabbitRelay and then checks the number of command-line arguments available via relay.GetArgsLen().

If there are more than four arguments, it reads four pieces of information from the relay object: the exchange name via relay.GetExchange(), the account via relay.GetAccount(), the asset identifier via relay.GetAsset(), then it obtains the trading side (buy or sell) from relay.GetArgs(4) and the initial amount from relay.GetArgs(5). If there are not more than four arguments, it prints an error message stating that exchange, (sub)account, asset, side, and amount must be provided, and then exits with status code 1.

The script converts the amount string into a floating-point number and stores it in variable u. It then enters a for loop that iterates exactly 100 times (i ranges from 0 to 99). For each iteration the code does the following:

- Calls relay.GetTicker(symbol=asset) to retrieve current market quote information for the specified asset, storing the returned structure in ticker.
- Reads ticker['Ask'] into bPrice and ticker['Bid'] into sPrice.
- Computes mPrice as the smaller of bPrice and sPrice, but does not use mPrice afterward.
- Calls relay.PlaceOrder with keyword arguments pair=asset, orderType='market', action=side, amount=u, and price=bPrice. It stores the return value of PlaceOrder in result.
- Prints the result value to standard output.
- Increments u by 1.0 so the next iteration uses a larger amount.

Thus, for up to 100 iterations the script fetches the asset's current bid and ask, places a market order with the current amount (starting from the provided amount and increasing by one each time) using the ask price as the price argument, prints the order result, and then increases the amount before the next order. The loop runs regardless of order outcomes; there is no conditional break or error handling within the loop.
