# Section 1 - Non-Technical Description

This program reads a specific text log file and, for each trade-related line in that file, looks up details about the original order and prints human-readable summaries showing when the position was opened, when it was closed or reduced, the direction (long/short), the amounts, prices, profit/loss values, and account balances.

# Section 2 - Technical Analysis

- Startup and imports: The script runs as a Python 3 program, appends a hard-coded library path to sys.path, and imports standard modules (os, time, datetime, json) plus two project modules: JRRsupport and JackrabbitRelay (imported as JRR). It constructs a Log object via JRR.JackrabbitLog() and a SignalInterceptor via JRRsupport.SignalInterceptor(Log=Log).

- Command-line argument handling: The program requires at least one command-line argument. If none is provided it prints "An least OliverTwist log file is required." and exits with status 1. It takes the first argument (sys.argv[1]) as gblog, the path to an "OliverTwist" log file. After storing gblog it removes all additional command-line arguments from sys.argv in a loop (it repeatedly removes sys.argv[1] until only the program name remains).

- Log filename parsing: The script splits the gblog filename string on '.' into a list named data. It expects at least four dot-separated components and assigns:
  - exchange = data[1]
  - account = data[2]
  - asset = data[3]
  It then builds pair by inserting a slash after the third character of asset (pair = asset[:3] + '/' + asset[3:]).

- Relay initialization and file reading: It constructs a JRR.JackrabbitRelay object named relay with the keyword arguments framework='oanda', exchange=data[1], account=account, asset=pair. It reads the entire gblog file using JRRsupport.ReadFile(gblog), strips surrounding whitespace, and splits into lines on newline characters to produce a list named lines.

- Iterating over log lines and filtering: The script initializes several lists/dicts (entry, relay, lines, orderList as empty dicts initially, then oList, nList, nLines as empty lists). It iterates over each line in lines, lowercases the line, and skips lines that are empty or that do not contain any of the substrings 'prft', 'rduc', or 'loss'. Only lines containing one of those substrings are processed further.

- Tokenizing a line: For each selected line it splits the line on spaces, then removes any empty tokens resulting from consecutive spaces. From the resulting token list it extracts fields by position:
  - sdt = token[0] + ' ' + token[1]  (selling date/time string from the log)
  - pid = token[2]                    (a process or pair id)
  - id = token[3]                     (order id)
  - cid = token[5]                    (counterparty or client id)
  - act = token[6]                    (action string: expected 'prft', 'rduc', or 'loss')
  - dir = token[7] with commas removed (direction token, e.g., 'shrt')
  - amt = token[8] with colons removed (amount, possibly with punctuation)
  - bp = token[9]                     (buy price string)
  - sp,rpl = token[11].split('/')     (sell price and a profit/loss field parsed from a token containing a slash)
  - dur = ' '.join(token[12:])        (duration or trailing info joined back into a string)

- Retrieving order details: For each processed log line the script calls relay.GetOrderDetails(OrderID=id) and takes the last element of the returned value with [-1], assigning that to oDetail. It then reads the 'time' field from oDetail, replaces 'T' with a space and removes trailing 'Z', splits on '.' to isolate fractional seconds, and composes bdt as the time with six fractional-second digits (bdt = f'{parts[0]}.{parts[1][:6]}'). If act equals 'rduc', it replaces amt with oDetail['units']. It also reads bal = oDetail['accountBalance'].

- Direction normalization and NAV calculation: If dir equals the strings 'shrt' or 'short' it normalizes dir to 'Short'. It computes nav as float(bp) multiplied by the absolute value of float(amt).

- Printing output: Depending on the action (act), the script prints formatted lines to standard output:
  - For act equal to 'prft' or 'loss', two print statements are executed:
    1) A "buy" line in the format: "{bdt} {pid} OT   {dir} - {id} Buy @{bp} -> {amt}"
    2) A "sell" line in the format: "{sdt} {pid} OT   {id} {dir} - {cid} Sell {amt} @{sp} -> {rpl} {bal}/{nav:.5f} {dur}"
     These lines present the opening timestamp, pid, direction, order id, buy price, amount, and then the selling timestamp, pid, order id, direction and counterparty id, sell amount, sell price, profit/loss, account balance, NAV (formatted to 5 decimal places), and the duration string.
  - For act equal to 'rduc', one print statement is executed:
    "{sdt} {pid} OT   {id} {dir} - {cid} ReduceBy {1} @{sp} -> {rpl} {bal}/{nav:.5f}"
    This prints the selling timestamp, pid, order id, direction, counterparty id, the literal "ReduceBy 1", the sell price and profit/loss, account balance, and NAV to 5 decimal places.

- Summary of behavior: In effect, the script parses each qualifying line from a named log file, queries the relay for order details for the referenced order id, computes a notional NAV based on the buy price and amount, formats timestamps and other fields, and prints human-readable lines describing buy and sell (or reduce) events together with profit/loss and account balance information.
