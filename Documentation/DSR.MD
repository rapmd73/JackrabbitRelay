# DSR
## Duplicate Signal Remover

If you've spent any amount of time using TradingView on lower timeframes,
you have become painfully aware of the propensity of duplicated or cached
(common called misfired) signals. This is a serious issue that can and
has cost many people significant money.

The DSR works to help solve that issue. While no system is 100% full
proof, the DSR has had a year of testing and operational fortitude to
prove it goes a long way of protect your investments from misfires.

The DSR was specifically built for Jackrabbit TV DCA and analyzier
modules.

Below is an example of the TradingView alert message.

```json
{
  "Time":"{{time}}",
  "Recipe":"#ATR #RSI #DCA",
  "Action":"Buy",
  "Exchange":"DSR",
  "Sub-Exchange":"kucoin",
  "Account":"MAIN",
  "Market":"Spot",
  "Asset":"{{ticker}}",
  "Price":"{{close}}",
  "AvgProfit":"{{plot_0}}",
  "LProfit":"{{plot_1}}",
  "TCycles":"{{plot_2}}",
  "CBuys":"{{plot_3}}",
  "MBCycle":"{{plot_4}}",
  "TBuys":"{{plot_5}}",
  "PSize":"1%",
  "Link":"https://www.tradingview.com/chart/lMQAJ6YU",
  "Identity":"YourIdentity"
}
```

Here is a breakdown of the above payload. All elements are required.

| Property Name | Description |
| :--- | :--- |
| `Time` | The date/time of this trade. Should be `{{time}}` |
| `Recipe` | This can be anything, buy should accurately represent the recipe you are using. It will be a key reference point for watching for duplicates |
| `Action` | Should be `buy`, `sell`, `close`, or `{{strategy.order.acrion}}` |
| `Exchange` | Must be `DSR` to use the DSR framework |
| `Sub-Exchange` | This is the actual exchange this order will be placed on |
| `Account` | The account to use from the exchange configuration file |
| `Market` | `Spot` or `Future` |
| `Asset` | `{{ticker}}` as TradingView will fill it in |
| `Price` | `{{close}}`, the current closing price at the time of the alert |
| `AvgProfit`| `{{plot_0}}`, These **MUST** be the exact TV macro used here. They will be filled in at the time of the alert |
| `LProfit` | `{{plot_1}}` |
| `TCycles` | `{{plot_2}}` |
| `CBuys` | `{{plot_3}}` |
| `MBCycle` | `{{plot_4}}` |
| `TBuys` | `{{plot_5}}` |
| `PSize` | The position size. Can be a number or perecentage |
| `Link` | The TradingView link to the chart |
| `Identity` | You identity for Relay, if you set one up |

## Donations

Information regarding donations and supporting Jackrabbit Relay can be
found [here](./Documentation/Donations.MD).

