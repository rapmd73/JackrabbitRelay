# Section 1 - Non-Technical Description

This program connects to a trading relay and repeatedly fetches market data for a specified asset, then presents a text-based, table-like view of the exchange's order book and best prices on the terminal. It updates the displayed order book continuously, highlighting the largest buy and sell interest levels and showing a small summary line with bid, ask and spread information.

# Section 2 - Technical Analysis

The program is a Python 3 script that uses a curses-based terminal UI to display order book information from a trading relay object. It imports a custom JackrabbitRelay module (JRR) and a support module (JRRsupport), constructs a relay instance, and expects command-line arguments specifying an exchange/subaccount, an asset, and a trade direction. If the required arguments are not provided the program prints an error message and exits.

curses.wrapper(main) runs the main(screen) function under curses. In main the script initializes several color pairs and clears the screen. It instantiates JRR.JackrabbitRelay() and checks the number of arguments via relay.GetArgsLen(). If there are sufficient arguments it reads exchange, account, asset and direction (direction is taken from sys.argv[4] and lowercased). It then enters an infinite loop that repeatedly:

- Requests a ticker and an order book from the relay for the selected asset via relay.GetTicker(symbol=asset) and relay.GetOrderBook(symbol=asset).
- If the returned orderbook is an empty list, writes a "Market closed, orderbook not available" message at a fixed location on the curses screen, refreshes the screen, sleeps briefly using JRRsupport.ElasticSleep(1), and continues the loop.
- Otherwise, it calls one of two display functions depending on the framework reported by relay.GetFramework(): ccxtOrderBook for the 'ccxt' framework, or oandaOrderBook for the 'oanda' framework. After calling the appropriate function it refreshes the screen and sleeps for one second.

ccxtOrderBook(screen, curses, orderbook, ticker, direction):
- Accepts an orderbook and a ticker dictionary.
- Reads the best buy and sell prices from the ticker with BuyPrice = round(float(ticker['Ask']),8) and SellPrice = round(float(ticker['Bid']),8). (Note: BuyPrice uses the ticker 'Ask' and SellPrice uses ticker 'Bid' as the code shows.)
- Iterates through the shorter of the orderbook's asks and bids, collecting totals and building two lists oblB (bid volume and price) and oblS (ask volume and price). While iterating it computes indices buyIDX and sellIDX by comparing the previous price and current price against BuyPrice and SellPrice.
- Prints table headers and a summary line including the BuyPrice, SellPrice, and their difference (spread) to standard output using formatted f-strings.
- Iterates for a range called depth (assumed to be defined elsewhere in the environment) starting at buyIDX and sellIDX to print rows with volume, bid price, ask price, and spread. It tracks the maximum buy volume and sell volume encountered and the corresponding prices.
- After printing rows it prints a MAX line showing the maximum observed buy volume, its price, the maximum sell price, its order volume, and the spread between the recorded max sell price and max buy price.

oandaOrderBook(screen, curses, relay, direction):
- Fetches an order book via relay.GetOrderBook(symbol=relay.GetAsset()) and ticker via relay.GetTicker(symbol=relay.GetAsset()).
- Extracts BuyPrice from ticker['Bid'] and SellPrice from ticker['Ask'].
- Determines terminal size maxY and maxX from the curses screen and sets a center y position.
- Iterates through the orderbook (which is expected to be a sequence of entries with keys 'longCountPercent', 'price', and 'shortCountPercent'). For each entry it converts these fields to numeric values and accumulates percent totals fb and fs. It rounds each price to four decimal places. It records the index positions buyIDX and sellIDX by comparing the previous price and current price against BuyPrice and SellPrice.
- Appends triples [buy_percent, price, sell_percent] into a list obl and accumulates totals and running sums of buy and sell volumes.
- Writes a header line and a summary line on the curses screen showing aggregated buy and sell percentages and the BuyPrice, SellPrice, and spread. Depending on the direction string ('long' or any other) it highlights either the buy side or sell side summary on that summary line using different color pairs.
- Determines a rendering depth (depth = maxY - 2) and scans the obl list around buyIDX and sellIDX to find the maximum buy percent and sell percent and the associated prices.
- Loops through depth rows and writes each row to the curses screen at successive y positions: the row index, buy percent, bid price, ask price, sell percent, and spread. When a row's bid price equals the recorded max buy price the code writes that row's buy and price again with a highlighted color pair; similarly if the ask price equals the recorded max sell price it highlights that ask price and sell percent.

Overall flow:
- The main loop continuously fetches live ticker and order book data from the relay and displays a formatted order book view on the terminal either to standard output (ccxt path uses print) or to the curses screen (oanda path uses screen.addstr). Between iterations the program sleeps for one second using JRRsupport.ElasticSleep(1). The program never exits the loop normally; after the loop there is a curses.endwin() call but it is unreachable in normal execution.
