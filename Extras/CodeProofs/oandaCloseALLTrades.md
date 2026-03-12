# Section 1 - Non-Technical Description

This program connects to a trading relay, finds all markets known to that relay, checks for any currently open trades in each market, and for every open trade it submits a market sell order to close that trade and prints the trade identifier along with the market symbol.

# Section 2 - Technical Analysis

The script begins by setting up the Python environment and importing required modules: sys, os, json, and a module named JackrabbitRelay (aliased as JRR). It appends a specific filesystem path (/home/GitHub/JackrabbitRelay/Base/Library) to sys.path so that the JackrabbitRelay module from that location can be imported.

A helper function Help(args, argslen) is defined which, when called, prints a usage message ("An exchange, and (sub)account must be provided.") and exits the program with status 1.

An instance of JRR.JackrabbitRelay is created and assigned to the variable relay; the constructor is called with a named parameter Usage=Help, which registers the Help function with the relay object (the code passes the function reference; the constructor's behavior is not modified here, only invoked).

The script obtains an exchange name and an account from the relay instance by calling relay.GetExchange() and relay.GetAccount(), storing their return values in exchangeName and account respectively. These values are retrieved but not used elsewhere in the script.

The script inspects relay.Markets, which it expects to be a mapping (dictionary-like) of market symbols to market details. It creates a list of the dictionary keys via list(relay.Markets.keys()) and sorts that list in-place with markets.sort(), resulting in an ordered list of market symbols stored in markets.

Next, the script iterates over each market symbol in the sorted markets list. For each symbol (referred to as asset), it calls relay.GetOpenTrades(symbol=asset) to retrieve open trades for that market. The returned value is assigned to orders and is iterated over; each element in orders is assumed to be a mapping (dictionary-like) describing a single open trade.

For every trade dictionary (single), the script reads the trade identifier from single['id'] and the number of current units from single['currentUnits']. It converts currentUnits to an integer by calling int(single['currentUnits']) and stores that in iu.

The script branches on the sign of iu: if iu is less than zero, it sets amt to the string '-ALL'; otherwise, it sets amt to the string 'ALL'. No other values for amt are used.

The script then calls relay.PlaceOrder with positional keyword arguments: pair=asset, action='Sell', amount=amt, ticket=id, orderType='Market', Quiet=True. The return value of PlaceOrder is stored in result but is not otherwise inspected or used.

After placing the order, the script prints a formatted line containing the trade id and the market symbol. The print uses an f-string that formats id to a width of 7 characters and asset to a width of 7 characters: print(f'{id:7} {asset:7}').

In summary, the runtime behavior is:
- Initialize a JackrabbitRelay instance with a Help callback.
- Retrieve exchange and account identifiers.
- Build and sort the list of known market symbols from relay.Markets.
- For each market symbol:
  - Retrieve open trades with relay.GetOpenTrades(symbol=...).
  - For each open trade:
    - Extract the trade id and currentUnits.
    - Choose an amount string of '-ALL' if currentUnits < 0, otherwise 'ALL'.
    - Place a market sell order via relay.PlaceOrder with the determined amount, supplying the original trade id as the ticket value and requesting quiet mode.
    - Print the trade id and the market symbol to standard output.

The script performs these actions for every market and every open trade returned by the relay instance.
