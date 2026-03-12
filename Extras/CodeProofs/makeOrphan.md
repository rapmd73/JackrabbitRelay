# Section 1 - Non-Technical Description

This program retrieves a list of currently open trading orders from a specified trading account on a chosen exchange or platform, formats each open order into a standardized record that includes order details and the original response, and prints each formatted record as a JSON string.

# Section 2 - Technical Analysis

The script starts by extending Python's import path with a fixed directory and then imports a module named JackrabbitRelay as JRR. It creates an instance of JRR.JackrabbitRelay and uses that instance (referred to as relay) to obtain command-line-associated parameters. The script checks the number of arguments via relay.GetArgsLen(); if that value is greater than 3 it obtains three values from the relay instance: exchangeName (relay.GetExchange()), account (relay.GetAccount()), and asset (relay.GetAsset()). If the argument count check fails, the script prints an error message and exits with status 1.

Next, the script calls relay.GetOpenOrders(symbol=asset) and stores the returned list or iterable in the variable oo. It then determines which code path to follow by calling relay.GetFramework().

- If relay.GetFramework() returns the string 'ccxt':
  - The script iterates over each element o in oo.
  - For each o it builds a dictionary Order containing these keys and values:
    - 'Exchange': relay.Exchange
    - 'Account': relay.Account
    - 'Asset': relay.Asset
    - 'Market': the fixed string 'Spot'
    - 'OrderType': the fixed string 'Limit'
    - 'Action': o['side']
    - 'Base': o['amount']
    - 'Price': o['price']
    - 'Identity': relay.Active['Identity']
  - It then builds a dictionary Orphan with these keys and values:
    - 'Status': the fixed string 'Open'
    - 'Framework': relay.Framework
    - 'ID': o['id']
    - 'DateTime': o['datetime']
    - 'Order': the JSON string obtained by json.dumps(Order)
    - 'Response': the JSON string obtained by json.dumps(o)
  - The script prints Orphan as a JSON string using json.dumps(Orphan).

- If relay.GetFramework() returns the string 'oanda':
  - The script iterates over each element o in oo.
  - It sets a local variable side to the fixed string 'Buy'.
  - For each o it builds a dictionary Order containing:
    - 'Exchange': relay.Exchange
    - 'Account': relay.Account
    - 'Asset': relay.Asset
    - 'OrderType': the fixed string 'Limit'
    - 'Action': side (always 'Buy' as assigned)
    - 'Units': o['units']
    - 'Price': o['price']
    - 'Identity': relay.Active['Identity']
  - It then builds Orphan with:
    - 'Status': the fixed string 'Open'
    - 'Framework': relay.Framework
    - 'ID': o['id']
    - 'DateTime': o['createTime']
    - 'Order': json.dumps(Order)
    - 'Response': json.dumps(o)
  - The script prints Orphan as a JSON string via json.dumps(Orphan).

In both framework branches the program produces one JSON-encoded line per open order. Each printed JSON object (Orphan) contains metadata fields (Status, Framework, ID, DateTime), an 'Order' field containing a JSON string of a standardized order dictionary, and a 'Response' field containing a JSON string of the original order data returned by relay.GetOpenOrders. The program uses values exposed on the relay instance (attributes like Exchange, Account, Asset, Framework, and nested Active['Identity']) when populating the standardized Order and Orphan records. If the framework value is neither 'ccxt' nor 'oanda', the script does not print anything further.
