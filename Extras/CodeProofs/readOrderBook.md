# Section 1 - Non-Technical Description

This program connects to a trading relay to read market information for a specified exchange account and asset, then prints a table showing price and volume information from the market's order book around the current bid and ask, including per-level buy/sell quantities, prices, and spreads, and highlights the largest buy and sell quantities found within the inspected depth.

# Section 2 - Technical Analysis

The script starts by importing system, OS, JSON modules and a local module named JackrabbitRelay (aliased as JRR). It creates an instance of JRR.JackrabbitRelay and expects command-line arguments: an exchange, a subaccount, an asset symbol, and a depth. If fewer than five arguments are present, it prints an error message and exits.

After validating arguments, it retrieves several pieces of data from the relay object:
- markets via relay.GetMarkets()
- a ticker for the requested asset via relay.GetTicker(symbol=asset)
- the order book for the requested asset via relay.GetOrderBook(symbol=asset)

It then checks the framework reported by relay.GetFramework() and takes different code paths for framework == 'mimic', 'ccxt', and 'oanda'. If the framework is 'mimic', it sets relay.Framework to relay.Broker.Framework before further processing (this assignment is done before the other framework-specific blocks).

For framework equal to 'ccxt':
- It extracts BuyPrice from ticker['Ask'] and SellPrice from ticker['Bid'], converting to float and rounding to 8 decimal places.
- It initializes accumulators lp, sp, and index variables buyIDX and sellIDX. It computes l as the smaller of the lengths of orderbook['asks'] and orderbook['bids'] minus 1.
- It iterates over order book levels up to l-1. For each level:
  - It reads the bid price and quantity from orderbook['bids'][ob][0] and [1], rounding the price to 8 decimals.
  - It reads the ask price and quantity from orderbook['asks'][ob][0] and [1], rounding the ask price to 8 decimals.
  - It checks whether the current bid/ask price crosses the BuyPrice and SellPrice thresholds and, if so, records current indices buyIDX and sellIDX.
  - It accumulates total buy and sell quantities into lp and sp.
  - It appends per-level [buy quantity, price] and [sell quantity, price] to oblB and oblS respectively.
- It prints a header with column labels and a summary line showing BuyPrice, SellPrice, and their difference.
- It then iterates depth times starting from the computed buyIDX and sellIDX, reading buy quantity and buy price from oblB[buyIDX+i], and sell price and sell quantity from oblS[sellIDX+i]. For each level it:
  - Computes the spread as sprice - bprice.
  - Updates maxBorders/maxBprice when a larger buy quantity is seen, and maxSorders/maxSprice when a larger sell quantity is seen.
  - Prints a formatted line containing the level number, buy volume, buy price, sell price, sell volume, and spread.
- After the loop it computes spread = maxSprice - maxBprice and prints a footer line and a MAX summary line showing the largest observed buy volume and price, the spread between the max sell and max buy prices, the largest sell price, and the largest sell quantity.

For framework equal to 'oanda':
- It extracts BuyPrice from ticker['Bid'] and SellPrice from ticker['Ask'] (note Buy/Sell naming is swapped relative to ccxt block).
- It initializes accumulators lp and sp, sets l to len(orderbook), and initializes indices.
- It iterates over each entry in the orderbook (which are expected to be dict-like entries). For each entry cur:
  - It computes buy as (float(cur['longCountPercent'])/100)*l and sell as (float(cur['shortCountPercent'])/100)*l.
  - It parses price as round(float(cur['price']),4).
  - It records buy, price, sell into an obl list.
  - It updates buyIDX and sellIDX based on whether the current price crosses BuyPrice or SellPrice thresholds (buyIDX is set to idx-1 when BuyPrice lies between pp and cp; sellIDX is set to idx when SellPrice lies between pp and cp).
  - It accumulates lp and sp.
- It prints a header similar to the ccxt block but with slightly different spacing, then a summary line showing BuyPrice, SellPrice, and their difference.
- It iterates depth times, and for each iteration uses indices buyIDX-i and sellIDX+i into the obl list to obtain buy volume, buy price, sell price and sell volume. For each level it:
  - Computes spread as sprice - bprice.
  - Updates maximum buy and sell trackers as in the ccxt block.
  - Prints a formatted line with level number, buy volume, buy price, sell price, sell volume, and spread.
- After the loop it computes spread = maxSprice - maxBprice and prints a footer line and a MAX summary line showing the maximum observed buy volume and price, maximum sell price and sell quantity, and the spread between the recorded extrema.

Across both framework paths, the program's observable behavior is: retrieve ticker and order book, determine indices around the current bid/ask, build per-price-level aggregates, print a formatted table of buy/sell volumes and prices for the requested depth centered on the bid/ask area, and print summary statistics showing the largest buy and sell quantities and associated prices within the inspected levels. The exact numeric formatting and which fields are read depend on the selected framework.
