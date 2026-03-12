# Section 1 - Non-Technical Description

This program reads transaction history for a named account from a storage area, groups the transactions by each asset pair, and then walks through each group's transactions to compute and print summary numbers - how many buy and sell actions occurred, the net count (buys minus sells), the maximum simultaneous position reached, the total fees paid for that asset, and a running balance value; finally it prints totals across all asset pairs.

# Section 2 - Technical Analysis

The script expects at least one command-line argument: an account name. It constructs a file path by appending the account name with a ".history" extension to a fixed MimicData directory. If the file does not exist it prints an error and exits. It reads the file contents via JRRsupport.ReadFile, strips leading/trailing whitespace and splits into lines.

It initializes two dictionaries: fees and Wallet. It iterates over every non-empty line in the file, attempting to parse each line as JSON. For each successfully parsed JSON object it extracts the Asset field and the Fee field (converted to float). It ensures Wallet[Asset] is a list and fees[Asset] is a numeric accumulator. It adds the fee to fees[Asset] and appends the original line (the JSON string) to Wallet[Asset]. If any line fails JSON parsing the script prints the damaged line and exits.

After grouping lines by asset, the script prepares accumulators for global totals: maxbuys, maxsells, maxfees, maxbal, and maxpmax. It iterates over the asset keys in Wallet in sorted order. If a second command-line argument is provided, it will skip any asset whose name does not exactly match that second argument.

For each asset (referred to in code as pair), it initializes per-asset counters: balance=0, buys=0, sells=0, maxpos=0, curpos=0. Then it iterates through the stored JSON lines for that asset. For each line it reparses the JSON and extracts fields:

- asset = data['Asset']
- base, quote are derived from asset by splitting on '/'; if asset contains ':' it uses the part after ':' as quote, and if that quote contains '-' it truncates at the '-' character.
- dt = data['DateTime'] (stored but not otherwise used)
- act = first character of data['Action'] uppercased
- bw = float(data[base]) - value read from the JSON keyed by the base asset symbol
- qw = float(data[quote]) - value read from the JSON keyed by the quote asset symbol
- a = float(data['Amount'])
- p = float(data['Price'])
- f = float(data['Fee'])

The code then treats actions whose first letter is 'B' as buys; otherwise it treats them as sells. For a buy (act == 'B') it decreases the balance by (abs(a) * p) + f, increments buys, and increments curpos by 1. For a sell it increases the balance by (abs(a) * p) - f, increments sells, and decrements curpos by 1 but then clamps curpos to a minimum of 0 (if curpos becomes negative it is set to 0). After updating curpos, if curpos exceeds maxpos it updates maxpos to curpos.

After processing all lines for the current asset, the script updates the global totals: adds the per-asset balance to maxbal, buys to maxbuys, sells to maxsells, fees[pair] to maxfees, and maxpos to maxpmax. It then prints a formatted line for that asset showing: asset name (left-justified), buys, sells, buys-sells, maxpos, the total fees for that asset (fees[pair]) with 8 decimal places, and the per-asset balance with 8 decimal places.

After finishing all assets, the script prints a final summary line showing totals across all assets: a blank asset column, the total buys, total sells, net buys minus sells, total of max positions, total fees across all assets, and the sum of per-asset balances. If any JSON parsing fails during per-asset processing the script prints the damaged line and exits immediately.
