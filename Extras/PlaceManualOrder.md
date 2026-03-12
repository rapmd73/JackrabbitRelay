# Section 1 - Non-Technical Description

This program takes user input about an exchange, account, asset, and an action, looks up the current market price for that asset, builds a market order with the specified size and options (such as a reduce-only flag or a market subtype), sends that order to a relay service, and then prints whether the order succeeded along with the order details or a failure reason.

# Section 2 - Technical Analysis

The script starts by importing modules, adding a specific path to sys.path, and importing a Jackrabbit Relay support module and the main Relay interface as JRR. It defines a Usage function that prints required command-line format examples and exits; Usage is passed into the relay constructor for use when argument validation fails.

In main(), Diagnostics is initialized to False. A JackrabbitRelay object is created using JRR.JackrabbitRelay(Usage=Usage). After construction, the program expects that the relay instance has parsed command-line arguments or consumed an order from standard input; it uses relay.GetArgsLen() to check the number of arguments. If there are more than four arguments, it retrieves exchange, account, asset, and action using relay.GetExchange(), relay.GetAccount(), relay.GetAsset(), and relay.GetArgs(4).lower(). If there are not enough arguments, it calls Usage and exits.

Diagnostics mode is activated if the string "diag" appears in the relay.args list. The code then checks whether the chosen asset exists in relay.Markets; if not present it prints a message and calls Usage.

For non-close actions, the program requires an amount. It inspects relay.GetArgsLen() > 5 and reads the amount from relay.GetArgs(5). If the specified exchange is 'oanda', it casts the amount to int; otherwise it casts to float. If no amount is provided where required, it prints a message and calls Usage.

The action string is validated: acceptable values are long, short, buy, sell, close, or flip. If action is "long" it is mapped to "buy"; if "short" it is mapped to "sell".

If the relay.Framework is 'ccxt' or 'mimic', the program determines a market type for the asset. It defaults marketType to 'spot' then checks entries in relay.Markets[asset] and relay.Markets[asset]['info'] to possibly override marketType from a 'type' field or from 'permissions'. It then scans the command-line arguments (relay.args) to find one of the tokens that match the marketType; if none is found it prints the expected market type and calls Usage. If a matching token is found it assigns it to mt and uses it later in the order payload.

The program determines whether the order should be reduce-only by checking whether the string "ReduceOnly" appears in relay.args (case-insensitive check via str(relay.args).lower()) and stores that boolean in ro.

It obtains a current ticker for the asset by calling relay.GetTicker(symbol=asset). From the ticker it extracts Ask as bPrice and Bid as sPrice. It picks a price mPrice based on action and the sign of amount: for buy with positive amount it uses the maximum of Ask and Bid; for buy with negative amount it uses the minimum; for sell with positive amount it uses the minimum; for sell with negative amount it uses the maximum. If the action is 'close' the program sets mPrice to the midpoint (average) of Ask and Bid.

Next it constructs a NewOrder dictionary with keys:
- 'Recipe' set to 'Manual Trade'
- 'Exchange' set to the selected exchange
- 'Account' set to the selected account
- 'Market' set to mt if mt was determined
- 'OrderType' set to 'Market'
- 'Asset' set to the asset string
- 'Action' set to the normalized action ('buy' or 'sell' or 'close' etc.)
- 'Price' set to the string representation of mPrice
For the amount it uses the key 'Base' with a string value of amount when the framework is 'ccxt' or 'mimic'; otherwise it uses the key 'Units' with the string value of amount. If ro is True, it sets 'ReduceOnly' to 'Yes'. It also sets 'Identity' to relay.Active['Identity'].

The program sends the order by calling relay.SendWebhook(NewOrder) and stores the returned result. If Diagnostics is True it prints the raw result. It then attempts to extract an order id using relay.GetOrderID(result). If the oid is not None it prints "Order successful: {oid}", then calls relay.GetOrderDetails with different parameter names depending on the framework (OrderID=oid for oanda, id=oid otherwise) and prints the returned detail. If oid is None, it obtains a failure reason by calling relay.GetFailedReason(result) and prints "Order failed: {failed}".

Finally, when run as a script (if __name__ == '__main__'), main() is invoked. The program thus orchestrates argument parsing (via the relay object), market-type checking, ticker retrieval, order price selection, order payload construction, submission to a relay, and printing of success or failure and order details.
