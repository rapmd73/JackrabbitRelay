# Section 1 - Non-Technical Description

This program reads a transaction history file for a named account, groups the transactions by asset type, calculates total fees per asset, and then prints a per-asset summary showing the total fees paid and a line-by-line sequence of computed balances and values for each transaction of that asset.

# Section 2 - Technical Analysis

The program expects to be run with at least one command-line argument: the account name. It constructs a path to a history file by appending the account name and ".history" to a fixed directory path stored in the MimicData variable. If the account argument is missing or the constructed history file path does not exist, the program prints an error message and exits.

It loads the entire contents of the history file using a ReadFile function from an imported JRRsupport module, strips trailing whitespace, and splits the result into lines. It initializes two dictionaries: fees to accumulate fee totals per asset, and Wallet to collect the raw lines (transaction records) for each asset.

The program iterates over each non-empty line from the file. For each line it attempts to parse the line as JSON. If parsing fails for any line, the program prints "Line damaged:" followed by the offending line and exits. For successfully parsed records it extracts the 'Asset' string and the 'Fee' numeric value (converted to float). It ensures there is a list in Wallet keyed by the asset and a numeric entry in fees keyed by the asset, then adds the fee to fees[asset] and appends the original line (the JSON string) to Wallet[asset].

After grouping and accumulating fees, the program iterates through the sorted list of asset keys from Wallet. If a second command-line argument was provided, the program will only process the asset that exactly matches that second argument; other assets are skipped. For each processed asset the program prints a one-line header that shows the asset name and the total fees paid for that asset formatted to eight decimal places.

For each asset, it initializes two numeric variables: balance (set to 0) and tfee (set to 0). It then scans each stored transaction line for that asset in the order they were appended. For each line it again parses the JSON (exiting on parse error), then extracts values used in the printed output and the balance computation:

- asset is read from data['Asset'].
- base and quote are derived by splitting asset on '/', with additional parsing: if a ':' appears in the asset string the quote portion is replaced by the substring after the colon; if that quote substring contains a '-', the quote is truncated at the '-' character.
- dt is taken from data['DateTime'].
- act is the uppercase first character of data['Action'].
- bw is the float value of data[base] (interpreted as the base wallet numeric field).
- qw is the float value of data[quote] (interpreted as the quote wallet numeric field).
- a is float(data['Amount']).
- p is float(data['Price']).
- f is float(data['Fee']).

For each transaction the program increments tfee by the transaction fee f, then sets balance to the expression: qw + (abs(bw) * p) - tfee. It formats a line containing the transaction datetime, the single-letter action, the base wallet value (bw) and quote wallet value (qw) each with 14 characters and 8 decimals, the amount a with 14 characters and 8 decimals, the price p with 8 decimals, the fee f with 8 decimals, and the computed balance with 8 decimals. This formatted line is printed for each transaction in the asset group.

After printing all transactions for an asset the program prints a blank line and proceeds to the next asset (subject to the optional asset filter). The output therefore contains, for each processed asset, a header line with total fees and then a chronological list of formatted transaction lines showing the derived per-transaction values and the running balance as computed by the program.
