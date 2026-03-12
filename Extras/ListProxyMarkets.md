# Section 1 - Non-Technical Description

This program lists trading markets for a specified exchange and account, filters them based on optional command-line criteria, and prints a formatted line for each market showing its name, identifier (if present), market type, margin ratio (if present), and current bid, spread, and ask prices; if interrupted by the user, it prints a termination message.

# Section 2 - Technical Analysis

The script is a Python 3 program that imports a pair of modules named JackrabbitRelay and JackrabbitProxy from a custom path added to sys.path. It defines a small helper GetRatio(decimal) that computes the reciprocal of a numeric input and returns it formatted as an integer ratio string like "  4:1". The Help function prints a short usage message and exits; it is passed to the proxy object as the Usage callback.

In main(), the program constructs a JackrabbitProxy instance with Usage set to the Help function. It then retrieves the exchange name and account via proxy.GetExchange() and proxy.GetAccount(), although those retrieved values are not used later in the script other than the initial calls. The program calls proxy.GetMarkets() which presumably causes the proxy to load market metadata into proxy.Markets; it then processes additional optional command-line arguments from the proxy: a search string (default 'ALL') is read from argument index 3 if present; optional numeric lower and upper thresholds (sLT and sGT) are read from argument indices 4 and 5 and stored along with boolean flags srchLT and srchGT indicating their presence.

The main processing loop iterates over all market symbols in proxy.Markets (for pair in proxy.Markets). For each market symbol it applies several filters:
- If proxy.Framework equals 'mimic' or 'ccxt', it skips symbols that start with a dot, contain ".d", or contain a space. Also under those frameworks, if the market entry has an 'active' field and it is False, the market is skipped.
- If a search string other than 'ALL' was provided, the code skips any symbol whose name does not contain that search substring (case-insensitive by earlier uppercasing of srch).
After passing filters, the code obtains live market data by calling proxy.GetTicker(symbol=pair), which returns a ticker dictionary expected to contain fields like 'Bid', 'Ask', and 'Spread'.

If both ticker['Bid'] and ticker['Ask'] are zero, the script skips printing that market. Otherwise it builds a formatted string dstr that begins with the market symbol left-padded to 30 characters. If the market entry in proxy.Markets contains an 'id' field, that id is appended (also padded to 30 characters). If the market entry contains a 'type' field, that type is appended (padded to 8 characters); additionally, if the market entry has a 'margin' field set to True and the type is 'spot', the code substitutes 'margin' for the market type before appending. If the market entry has a 'marginRate' field, the script converts that value to a float, calls GetRatio on it to get a reciprocal ratio string, and appends that string. Finally the code appends numeric values from the ticker: the Bid, Spread, and Ask formatted as floating-point numbers with 18 total width and 8 digits after the decimal point. The completed dstr is printed to standard output.

The script is guarded by the usual if __name__ == '__main__' block. When run directly it calls main() inside a try/except that catches KeyboardInterrupt; on such an interrupt it prints "Terminated".
