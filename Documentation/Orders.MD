# JackrabbitRelay Payloads

This document details the various types of order payloads.

## Disclaimer

Please note RAPMD Crypto, LLC ("the Company"), does not provide financial
advice. The Company, and any associated companies, owners, employees,
agents or volunteers, do not hold  themselves out as Commodity Trading
Advisors (“CTAs”) or Authorized Financial Advisors  (“AFAs”). The owners,
publishers, employees and agents are not licensed under securities laws 
to address particular investment situations. No information presented
constitutes a  recommendation to buy, sell or hold any security,
financial product or instrument discussed  therein or to engage in any
specific investment strategy.

All content is for informational purposes only. The content provided
herein is not intended to replace or serve as a substitute for any
legal, tax, investment or other professional advice,  consultation or
service. It is important to do your own analysis before making any
investment  based on your own financial circumstances, investment
objectives, risk tolerance and liquidity needs.

All investments are speculative in nature and involve substantial risk of
loss. The Company does not in any way warrant or guarantee the success of
any action you take in reliance on the  statements, recommendations or
materials. The Company, owners, publishers, employees and  agents are not
liable for any losses or damages, monetary or other that may result from
the  application of information contained within any statements,
recommendations or materials.  Individuals must use their own due
diligence in analyzing featured trading indicators, other trading  tools,
webinars and other educational materials to determine if they represent
suitable and  useable features and capabilities for the individual.

Use this Software at your own risk. It is provided AS IS. The Company
accepts no responsibility or liability for losses incurred through using
this software. While The Company has gone to great lengths to test the
software, if you do find any bugs, please report them to us in the
[Jackrabbit Support Server](https://discord.gg/g93TpbV) or on Github, and
we will sort them out. Remember that risk management is your
responsibility. If you lose your account, that's entirely on you.

Past performance is not indicative of future results. Investments involve
substantial risk. Any past  results provided are intended as examples
only and are in no way a reflection of what an individual  could have
made or lost in the same situation.

## Payload Synopsis

Description of the payload items

| Property Name | Description |
| :--- | :--- |
| `Exchange` | This is one of the supported exchanges |
| `Market` | This is the market you are trading. <table><tr><td>`Spot`<td><td>Working</td></tr><tr><td>`Future`<td><td>Working</td></tr><tr><td>`Margin`<td><td>In progress</td></tr></table> |
| `Account` | All main accounts must be called `MAIN`. Subaccounts can be used (if your exchange supports them) and must be exactly as listed on the exchange. |
| `OrderType` | This is one of the allowed [order types](#Order Types) |
| `Action` | This is one of the [supported actions](#Actions) |
| `Asset` | The asset you are trading.  Must be exactly as the exchange lists it. Hint: Use [ListMarkets](Extras/README.md#listmarkets) to confirm |
| `USD` / `Base` / `Quote` | Choose only one to set the amount to be purchased/sold:<br><li>`USD` will only work if the asset has a corresponding USD pair to do a proper base conversion on.</li> <li> `Base` is the asset itself value, ie BTC, ADA, AAVE, so one. A base of 1 for BTC is to purchase 1 BTC.</li> <li>`Quote` is the value of the asset in its quote currency. For example, if you want to purchase BCH/BTC using the price value of BTC, then you specify your amount in the quote currency.</li><br>The amount can be expressed in percentage form, which will reflct the percentage ofthe balance of the account.<br><br>Values expressed in percentage form can also denote base or quote currency volumes: <br><li>For base currency volume (`12%b`), the base value is kept consistent throught the trade cycle while the quote currwency volume depreciates.</li> <li>For quote currency volume (`12%q`), the quote currency value is kept consistent while the base currency value appreciates.</li> |
| `Close` | For limit orders. This value can be `bid`, `ask`, or a value. If this is not present, the current closing price is used. |
| `Leverage` | For binanceusdm and ftx, this sets the leverage amount |
| `Margin` | For binanceusdm, this sets the margin to `Crossed` or `Isolated`. |
| `SignalSource` | If this is `TVstrategy`, the buy/sell will be remapped to long/short. |
| `Spread` | This evaluate the difference between the bid and ask prices. Trades are only places if the spread is *under this value* |
| `OverridePCTtable` | Overrides thew PCT table and forces a balance percentage based upon the immediate current balance of the account |
| `RemapSymbol` | For use with the TradingView `{{ticker}}` macro. Only this order is remapped. |

### Order Types

| Type | Description |
| :--- | :--- |
| `Market` | Market Orders. You pay taker fees on both sides of the trade and this order completes immediately. This is the default if order type is not present and the exchange supports market orders. |
| `Limit` | Limit Orders. You will pay either a maker fee or a taker fee based upon how long this order sits on the books. This is the default for exchanges that do not support market orders. |
| `LimitMaker` | Limit Orders with a request to hold this order on the book for a maker fee. |
| `LimitTaker` | Limit Orders with a fill or kill request. You will pay a taker fee. This order type is a simulated effect of a market order for exchanges that onlt support limit orders. |

### Actions

| Action | Description |
| :--- | :--- |
| `Buy` | Purchase an asset. |
| `Sell` | Sell a portion of asset. If amount is more than balance, the full position will be closed. |
| `Close` | Sell all of the asset. |
| `Long` | (Perpetuals) Opens a long position, and can flip a short to long (if `ReduceOnly` is not included in configuration). |
| `Short` | (Perpetuals) Opens a short position, and can flip a long to short (if `ReduceOnly` is not included in configuration). |

## Examples

Here are examples of the payload:

This example of a gewneralized payload for TradingView that uses the `{{ticker}}` macro

```json
{ "Exchange":"binance","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"{{ticker}}","SymbolRemap":"Yes","USD":"30" }
```

This example purchased $30 of AAVE on the FTX US exchange.

```json
{ "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD","USD":"30" }
```

This example purchases the minimum amount of AAVE in USD. The minimum
amount is defined by the exchange.

```json
{ "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD" }
```

This example sells $7 of AAVE

```json
{ "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Sell","Asset":"AAVE/USD","USD":"7" }
```

This example sells th exchange minimum of AAVE

```json
{ "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Sell","Asset":"AAVE/USD" }
```

This example close out or sells all of AAVE

```json
{ "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Close","Asset":"AAVE/USD" }
```

This example purchases AAVE using its base value, in this case, 1 AAVE

```json
{ "Exchange":"kraken","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD","Base":"1" }
```

This example purchases BCH by the value of BTC

```json
{ "Exchange":"ftx","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"BCH/BTC","Quote":"1" }
```

This example purchases BCH by the value of BTC using a limit MAKER order

```json
{ "Exchange":"ftx","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"BCH/BTC","Quote":"1","OrderType":"LimitMaker","Close":"ASK" }
```

This example purchase of a perpetual contract of AAVE with a leverage of 5

```json
{ "Exchange":"ftx","Market":"Future","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD:USD","Base":"1","Leverage":"5" }
```

This example purchase of a perpetual contract of AAVE with a leverage of 20, using an isolated margin

```json
{ "Exchange":"ftx","Market":"Future","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD:USD","Base":"1","Leverage":"20","Margin":"Isolated" }
```

This example will purchasw 1% of the total value of the account using the
USD conversion amount. Market order is assumed.

```json
{ "Exchange":"kucoin","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"ADA/USDT","USD":"1%" }
```

This example closes the above. It is important to remember to maintain
the percentage reference in closing a position. Relay only checks its
internal tables as needed to retain maximum effecincy. That means you
must explicitly tell it what tables to check.

```json
{ "Exchange":"kucoin","Market":"Spot","Account":"MAIN","Action":"Close","Asset":"ADA/USDT","USD":"1%" }
```

## Donations

Information regarding donations and supporting Jackrabbit Relay can be
found [here](./Documentation/Donations.MD).

