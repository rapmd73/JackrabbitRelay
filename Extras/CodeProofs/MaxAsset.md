Section 1 - Non-Technical Description

This program reads stored asset records for a specified trading exchange and account, calculates how many days remain until each asset record expires, and prints each asset name alongside the remaining time in days for those assets that have not yet expired.

Section 2 - Technical Analysis

The script begins by adding a specific directory to Python's module search path and importing required modules: os, time, json, plus two project-specific modules JRRsupport and JackrabbitRelay. It creates an instance of JackrabbitRelay from the JackrabbitRelay module and checks the argument count via relay.GetArgsLen(). If fewer than three arguments are present, it prints an error message and exits with status 1.

Next, it builds a filename string fn by combining the relay instance's Directories['Data'] path with the relay instance's Exchange and Account attributes, joined by periods and suffixed with ".MaxAssets". It then constructs a TimedList object from JRRsupport by calling JRRsupport.TimedList('MaxAssets', fn, Timeout=300). It reads the contents of that timed list into dataDB by calling tList.read().

The code then iterates over each key in dataDB (each key represents an asset). For each asset key it takes the corresponding value dataDB[asset], parses that value as JSON into a Python dictionary item via json.loads(...). It computes e as (item['Expire'] - time.time()) / 86400, i.e., the difference between the stored Expire timestamp and the current time converted from seconds into days. If e is greater than zero (meaning the expire time is in the future), it prints a formatted line with the asset name left-aligned in a 20-character field and the computed e displayed as a floating-point number with eight digits after the decimal point.

In summary: the program requires command-line context provided through the relay object, reads a timed list file named from the relay's data directory and exchange/account identifiers, parses JSON entries per asset, computes remaining days until expiration using the Expire field, and prints each non-expired asset with its remaining days.
