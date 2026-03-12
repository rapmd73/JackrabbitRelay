# Section 1 - Non-Technical Description

This program connects to a trading relay, checks that an exchange, a sub-account, and an asset were provided when it was run, retrieves the list of open orders for that asset from the relay, and then prints each open order in a human-readable table-like format; the exact fields printed depend on which trading framework the relay is using.

# Section 2 - Technical Analysis

The script begins by importing standard modules (sys, os, json) and then appends a specific directory (/home/GitHub/JackrabbitRelay/Base/Library) to Python's module search path. It imports a module named JackrabbitRelay (aliased as JRR), constructs an instance of JRR.JackrabbitRelay, and uses methods of that instance to inspect command-line arguments and configuration.

Immediately after creating the relay object, the code checks the number of command-line style arguments via relay.GetArgsLen(). If that reported length is greater than 3, the script retrieves three pieces of context from the relay: the exchange name via relay.GetExchange(), the account via relay.GetAccount(), and the asset via relay.GetAsset(). If GetArgsLen() is not greater than 3, the script prints an error message saying "An exchange, (sub)account, and an asset must be provided." and exits with status code 1.

The script then reads two properties from the relay object: relay.Markets (assigned to the local variable markets, though that variable is not used later) and the list of open orders for the chosen asset via relay.GetOpenOrders(symbol=asset), assigned to the local variable oo.

Next the script branches based on the framework reported by relay.GetFramework(). If GetFramework() returns the string 'ccxt', it iterates over each order object in oo. For every order o it prints one line per order using formatted output that includes these fields from the order object: o['symbol'], o['id'], o['side'], o['status'], o['amount'], and o['price']. The amount and price fields are formatted as floating-point numbers with 8 digits after the decimal.

If GetFramework() returns the string 'oanda', it iterates over each order object in oo and for each order converts o['units'] to an integer (stored in iu) and converts o['price'] to a float (stored in price). It determines a textual side label: if price is greater than or equal to zero it sets side to 'Long', otherwise to 'Shrt'. It then prints one line per order using formatted output that includes these fields from the order object: o['instrument'], o['id'], the computed side label, o['state'], the units (iu) formatted with 8 decimal places, and the price formatted with 8 decimal places.

In summary, the program validates arguments via the relay, fetches open orders for a specified asset, and prints those orders in a framework-dependent format: one layout when the relay framework is 'ccxt' and a different layout when it is 'oanda'.
