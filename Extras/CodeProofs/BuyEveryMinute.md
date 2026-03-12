# Section 1 - Non-Technical Description

This program repeatedly sends a predefined buy order to an external relay service once every minute, then prints a short line summarizing the asset, the order identifier, the executed price, and the account balance for the asset. It continues doing this in an endless loop until the program is stopped.

# Section 2 - Technical Analysis

The script begins by importing standard libraries (sys, os, json, time) and then appends a specific directory to Python's module search path. It imports two project modules: JRRsupport and JackrabbitRelay (aliased as JRR). A dictionary named NewOrder is defined at module level containing fixed order parameters (for example, recipe, action "Buy", exchange "mimic", market "spot", account "Kraken04", asset "ARB/USD", USD amount "10", order type "Market", conditional flag "Yes", direction "Long", and take profit "2%").

A function PushOrder(NewOrder) is defined. Inside PushOrder:
- It constructs an instance of JRR.JackrabbitRelay with the JSON-serialized NewOrder passed as the payload and with keyword flags NoIdentityVerification=True and RaiseError=True.
- It copies an identity value from relay.Active['Identity'] into relay.Order['Identity'].
- It calls relay.SendWebhook(relay.Order) to send the order and stores the response in result.
- It calls relay.GetOrderID(result) to extract an order identifier (oid) from the send result.
- If an oid is returned (not None), it obtains the asset base symbol by splitting relay.Order['Asset'] on '/' and taking the first token, then calls relay.GetBalance(Base=...) to get the balance for that base asset.
- It calls relay.GetOrderDetails(id=oid, symbol=relay.Order['Asset']) to fetch order details, and then prints a single formatted line that includes: the asset string, the order id, the order price (rounded and formatted to eight decimal places), and the balance (rounded to eight decimal places). The print uses f-string formatting and accesses relay.Order, oid, detail['Price'], and bal.
- Any exception raised in this sequence is caught and printed.

The main() function contains an infinite loop that repeatedly calls PushOrder(NewOrder) and then calls JRRsupport.ElasticSleep(60). That ElasticSleep call is used to pause execution roughly 60 seconds between iterations (it is invoked with the integer 60 as its argument).

When the script is executed as the main program, it invokes main(), which starts the endless cycle of pushing the same NewOrder and sleeping. The program therefore continually builds a relay object, assigns identity into the order, sends the order via webhook, retrieves the order id and details when available, prints a one-line summary for successful orders, and waits approximately one minute before repeating. Any exceptions thrown during an order attempt are printed and the loop continues.
