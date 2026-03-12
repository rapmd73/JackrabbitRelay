# Section 1 - Non-Technical Description

This program connects to a trading relay system, examines the currently open trades for a given asset on a specified exchange account, and determines the next available trade size to use so that it does not duplicate any lot sizes already in use; it then prints the list of used sizes and the chosen next size.

# Section 2 - Technical Analysis

The script starts by importing modules and appending a specific directory to Python's module search path, then imports a module named JackrabbitRelay as JRR. It defines a single function, LowestLotSize(relay, asset, units, step), and then creates an instance of JRR.JackrabbitRelay and uses that instance to read command-line or runtime arguments to determine exchangeName, account, asset, and units. If fewer than four arguments are provided, the program prints an error message and exits.

LowestLotSize performs these steps:
- It initializes lowestSize to the absolute value of the provided units argument and lotSize to the absolute value of the provided step argument.
- It calls relay.GetOpenTrades(symbol=asset) to obtain a list of open trades for the specified asset. The function assumes each trade in this list is a mapping (e.g., a dict) containing at least 'currentUnits' and 'initialUnits' fields.
- It builds a list usedSize of unique absolute integer values derived from each trade's 'currentUnits' and 'initialUnits'. For each trade, it converts the two fields to int, takes their absolute values, and appends them to usedSize only if they are not already present.
- It sorts usedSize in ascending order and prints that list.
- It sets nextSize initially to lowestSize, then increments nextSize by lotSize repeatedly while nextSize already appears in usedSize. In other words, it finds the smallest value >= lowestSize that is not present in usedSize, stepping by lotSize each iteration.
- It determines sign by checking the original units argument: if units is negative it sets sign to -1, otherwise sign is 1. It multiplies nextSize by sign to preserve trade direction.
- It prints a message indicating the computed next unit size and returns nextSize multiplied by sign.

Back in the main flow, after reading arguments and creating the relay object, the script calls LowestLotSize with step fixed at 1, captures the returned signed size in ls, and prints ls. Overall, the program identifies existing absolute lot sizes in current open trades for a given asset and selects the next available absolute lot size (starting from the absolute requested units and incrementing by one) that is not already used, then outputs that signed size.
