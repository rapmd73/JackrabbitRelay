# Section 1 - Non-Technical Description

This program looks through a stored list of open trade orders, picks out those that belong to a specific trading exchange, account, and asset provided when the program runs, and then reports which matching order has the highest price and which has the lowest price, along with how long the program took to perform the read and the comparison operations.

# Section 2 - Technical Analysis

The script starts by importing modules and appending a custom library path. It defines file-system paths: DataDirectory, chartDir, and Storehouse, and creates a locker object OliverTwistLock via JRRsupport.Locker('OliverTwist') (the locker object is created but its lock/unlock calls are commented out where reading occurs).

A function ReadStorehouse(exchange, account, asset) reads and filters entries from the Storehouse file. Inside ReadStorehouse:
- It initializes an empty list OrphanList and sets WorkingStorehouse to the global Storehouse path.
- If the file at WorkingStorehouse exists, it reads the file contents via JRRsupport.ReadFile(WorkingStorehouse), strips whitespace, and if the resulting buffer is non-empty it splits the buffer on newline to get individual entries.
- For each non-empty entry string:
  - It assigns Entry to Orphan and attempts to repeatedly json.loads() the Orphan while its type is str. This unwraps nested JSON-encoded strings into a Python object.
  - If json decoding fails, it attempts to log the broken entry via JRLog.Write and continues to the next entry.
  - If the decoded Orphan contains an 'Order' field that is a string, it json.loads() that string into order, removes an 'Identity' key from the order if present, and replaces Orphan['Order'] with the decoded order dict.
  - Similarly, if Orphan contains a 'Detail' field that is a string, it json.loads() it into a detail dict, removes 'Identity' if present, and stores it back into Orphan['Detail'].
  - It then checks whether Orphan['Order']['Exchange'], Orphan['Order']['Account'], and Orphan['Order']['Asset'] exactly match the exchange, account, and asset arguments passed to ReadStorehouse.
  - If they match and Orphan does not already have a 'Price' key, the code attempts to obtain order details via relay.GetOrderDetails(OrderID=Orphan['ID'])[-1] and takes the 'price' field from that result to set Orphan['Price']; if that attempt raises an exception it prints od and exits the process.
  - Matching Orphan objects are appended to OrphanList.
- The function returns OrphanList.

In the main driver:
- An instance relay = JRR.JackrabbitRelay() is created.
- The script requires three command-line style inputs (checked via relay.GetArgsLen() > 3). If present, it obtains exchange, account, and asset via relay.GetExchange(), relay.GetAccount(), and relay.GetAsset(); otherwise it prints a message and exits.
- The script times and calls ReadStorehouse(exchange, account, asset) and prints the elapsed time for that read phase.
- It initializes hPrice to negative infinity and lPrice to positive infinity, and hTrade and lTrade to None.
- It iterates over the list oo returned by ReadStorehouse:
  - For each entry o it converts o['Price'] to a float.
  - If price is less than lPrice, it sets lTrade to the current entry and updates lPrice.
  - If price is greater than hPrice, it sets hTrade to the current entry and updates hPrice.
- After iteration it prints the ID and Price of the highest-price order and the ID and Price of the lowest-price order, and prints the elapsed time taken for the comparison phase.
- Finally the script exits with status 0.

Observed behaviors and data interactions:
- The program relies on a plaintext Storehouse file where each line is a JSON-encoded record; some fields inside each record (Order, Detail) may themselves be JSON-encoded strings and are decoded.
- It filters records by exact match on Exchange, Account, and Asset fields inside each record's Order object.
- If a matching record lacks a Price, the program queries relay.GetOrderDetails using the record's ID and uses the price from the returned details.
- It reports the ID and numeric price of the highest- and lowest-priced matching records and measures and prints elapsed times for reading and for scanning/comparison.
