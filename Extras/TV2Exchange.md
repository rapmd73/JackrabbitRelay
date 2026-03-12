Section 1 - Non-Technical Description

This program reads information about available trading markets for a specified exchange and account, converts those market names into a different naming style used by another service, and writes a mapping of the converted names to the original market names into a file. After saving the file it prints a short confirmation message naming the exchange and account.

Section 2 - Technical Analysis

- Startup and setup: The script runs under Python 3, modifies the module search path to include '/home/JackrabbitRelay2/Base/Library', imports json, and imports a module named JackrabbitRelay as JRR. It defines a Help function that prints a usage message and exits with status 1. It then constructs an instance of JRR.JackrabbitRelay, passing the Help function via the Usage parameter.

- Retrieving context: From the relay instance the script obtains the exchange name via relay.GetExchange(), the account via relay.GetAccount(), and the markets dictionary via relay.Markets. It relies on the relay instance having already loaded any required login or initialization state.

- Building the TradingView mapping: The script creates an empty dictionary named TradingView. It queries relay.GetFramework() to decide how to construct keys:
  - If the framework string equals 'oanda', it iterates over each key in markets, treating markets[cur] as a market description p. For each p it takes p['displayName'], removes any '/' and '_' characters to form the TradingView key tv, and uses the original p['displayName'] as the mapped value ns. It assigns TradingView[tv] = ns.
  - If the framework string equals 'ccxt' or 'mimic', it iterates over markets similarly. For each market p it checks if p contains a 'type' field and whether p['type'].lower() != 'spot'. If that condition is true, it creates tv by taking p['id'] and removing '/', '-', and ':' characters, then appending ':' plus the lowercased p['type']. If the market has no 'type' or the type is 'spot', tv is created by removing '/', '-', and ':' from p['id'] only. In both cases the mapped value ns is set to p['symbol'], and TradingView[tv] = ns.

- Writing the file: The script computes a filename fn by joining relay.Directories['Data'] with a filename composed of exchangeName, a dot, account, and the extension '.symbolmap'. It opens that file for writing, writes a JSON-encoded representation of the TradingView dictionary followed by a newline, and closes the file.

- Final output: After writing the file the script prints a single line to standard output in the form "{exchangeName}/{account} symbol map file written", where exchangeName and account are the values obtained from the relay instance.
