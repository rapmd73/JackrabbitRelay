# Section 1 - Non-Technical Description

This program looks up and lists tracked open orders for a specific trading exchange, sub-account, and asset, then fetches and prints detailed information about each matching order so a user can see what orders are currently being monitored for that trading combination.

# Section 2 - Technical Analysis

The script begins by preparing its runtime environment: it adds a specific library path to Python's search path, imports standard modules (os, json, datetime, sys) and two project modules: JRRsupport and JackrabbitRelay (aliased as JRR). It defines several filesystem paths used for data storage: a base DataDirectory, a chart directory, and a file path named OliverTwist.Storehouse.

A Locker object named OliverTwistLock is created by calling JRRsupport.Locker('OliverTwist'); this lock object is used to synchronize access to the storehouse file.

The function ReadStorehouse(exchange, account, asset) reads the storehouse file and returns a list of entries ("orphans") that match the provided exchange, account, and asset. The function behavior is:

- It declares a local OrphanList to accumulate matching entries and sets WorkingStorehouse to the Storehouse path defined globally.
- It acquires the lock by repeatedly calling OliverTwistLock.Lock() and sleeping (via JRRsupport.ElasticSleep(1)) until the Lock method returns the string 'locked'.
- If the storehouse file exists, it reads the file contents using JRRsupport.ReadFile(WorkingStorehouse), strips whitespace, and splits the contents by newline into individual entries.
- For each non-empty entry, it attempts to parse the entry as JSON repeatedly until the parsed object is not a string (i.e., handles nested JSON-encoded strings). If parsing fails, it writes a "Broken" message to JRLog and skips that entry.
- For parsed entries that contain an 'Order' field whose value is a string, it JSON-decodes that string into an object, removes any 'Identity' key from the decoded order object, and replaces the string with the decoded object. The same is done for a 'Detail' field if present and stored as a string.
- It then compares the decoded Orphan's Order object's 'Exchange', 'Account', and 'Asset' fields to the function arguments; if all three match, the Orphan object is appended to OrphanList.
- After processing, it calls OliverTwistLock.Unlock() and returns the OrphanList.

After the function definition, the script instantiates a JackrabbitRelay object (relay = JRR.JackrabbitRelay()). It checks the number of command-line arguments via relay.GetArgsLen(). If there are more than three arguments, it retrieves exchange, account, and asset values by calling relay.GetExchange(), relay.GetAccount(), and relay.GetAsset(); otherwise it prints an error message and exits with status 1.

A dictionary named CondOrder is constructed and populated with a set of keys and values representing a conditional order template (Recipe, Action, Exchange, Account, Asset, Units, ReduceBy, EnforceFIFO, Conditional, Direction, SellAction, TakeProfit, StopLoss). The populated CondOrder includes the exchange, account, and asset values obtained earlier, but this dictionary is not used later in the shown code.

The script calls ReadStorehouse(exchange, account, asset) to obtain OpenOrders matching the provided exchange/account/asset. For each matching stored order object o in OpenOrders, it calls relay.GetOrderDetails(OrderID=o['ID']) to retrieve detailed order information. It assigns that result to od, iterates over od, and prints each element i (followed by a blank line after each order). The printed output is whatever GetOrderDetails returns and its iterable contents.
