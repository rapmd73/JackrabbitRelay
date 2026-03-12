Section 1 - Non-Technical Description

This program connects to a trading relay, checks that an exchange, account, and asset were provided as inputs, retrieves the set of currently open trades for the specified asset, and then prints a line for each open trade showing when it opened, the trade identifier, whether it is long or short, the number of units, the entry price, the unrealized profit or loss, and the financing amount. After listing all open trades it prints the summed unrealized profit/loss plus financing and the count of open trades.

Section 2 - Technical Analysis

The script begins by importing standard modules (sys, os, json, datetime) and then imports a module named JackrabbitRelay under the alias JRR. It appends a specific path ('/home/GitHub/JackrabbitRelay/Base/Library') to sys.path before the import, so the JackrabbitRelay module is loaded from that search path. An instance of JRR.JackrabbitRelay is created and assigned to the variable relay.

The program checks the number of command-line arguments available to the relay instance by calling relay.GetArgsLen(). If GetArgsLen() returns a value greater than 3, it calls relay.GetExchange(), relay.GetAccount(), and relay.GetAsset() and stores their return values in exchangeName, account, and asset respectively. If GetArgsLen() is not greater than 3, the program prints an error message ("An exchange, (sub)account, and an asset must be provided.") and exits with status code 1.

After that, the variable markets is assigned the value relay.Markets (the code does not use markets further). The program calls relay.GetOpenTrades(symbol=asset) and assigns the returned list to oo. It initializes an accumulator tpnl to 0; this accumulator will hold the running total of unrealized profit/loss plus financing for all open trades.

The code then iterates over each element o in oo. For each trade object o, it accesses o['openTime'] and splits the string on the '.' character into parts. It constructs a new timestamp string dsS by combining the first segment parts[0], a dot, the first six characters of parts[1], and a trailing 'Z' (f'{parts[0]}.{parts[1][:6]}Z'). It parses dsS using datetime.datetime.strptime with the format '%Y-%m-%dT%H:%M:%S.%fZ' to produce a datetime object dt, then calls dt.timestamp() and stores that epoch value in epoch. (The computed epoch value is not used elsewhere in the script.)

The script extracts numeric values from the trade object: it converts o['currentUnits'] to an integer iu, converts o['price'] to a float price, converts o['unrealizedPL'] to a float upl, and converts o['financing'] to a float fin. It adds upl + fin to the tpnl accumulator.

It determines a side indicator: if iu is greater than or equal to zero it sets side to 'L' (long), otherwise to 'S' (short). It then prints a formatted line for the trade containing the original openTime string, the trade id o['id'] right-aligned in a field of width 7, the side letter, the absolute value of iu in a 4-character wide integer field with no decimals, the price in a 10-character field with 5 decimal places, upl in a 9-character field with 5 decimal places, and fin in a 9-character field with 5 decimal places. The print uses an f-string that embeds these values directly.

After the loop completes, the program prints a newline followed by the rounded tpnl value to 5 decimal places and the number of open trades len(oo). Overall, the program lists open trades for a given asset, computes a total of unrealized P/L plus financing, and displays that total and the count of open trades.
