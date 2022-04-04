# Configuration Files

This file details the configuration files for each exchange.

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

## Configuration files

### Location and file names
This would be placed in a folder called `/home/JackrabbitRelay/Config/` and
named something like `ftxus.cfg`. This file would be the configuration for the FTX.US exchange.

In general, the name of each file is `[exchangename].cfg` where `[exchangename]` is the ccxt lowercase representation of your exchange. See the [Exchanges](#exchanges) section above.

### File contents

The Jackrabbit Relay configuration files contain JSON-based text. Here is an example:

```json
{ "Account":"MAIN","API":"YourAPI","SECRET":"YourSecret","RateLimit":"200","MaxAssets":"7","Reduction":"0.00001","ReduceOnly":"Yes" }
```

Note: KuCoin *requires* a passphrase as well. It is case sensitive and must be
*EXACTLY* as you gave it to KuCoin. Here is an example:

```json
# ./JackrabbitRelay/Config/kucoin.cfg
{ "Account":"MAIN","API":"YourAPI","SECRET":"YourSecret","Passphrase":"YourPassphrase","RateLimit":"1000","MaxAssets":"7","Reduction":"0.00001","ReduceOnly":"Yes" }
```

Now for the details:

| Property Name | Description |
| :--- | :--- |
| `Account` | This MUST be `MAIN`, case sensitive, for the main account of every exchange. |
| `API` | Your API key exactly as your exchange gives it to you. |
| `SECRET` | Your SECRET key exactly as your exchange gives it to you. |
| `Passphrase` | This is only required for exchanges that use passphrases, such as KuCoin. |
| `RateLimit` | This is the amount Relay waits between each exchange API call. <br> ALL EXCHANGES HAVE RATE LIMIT REQUIREMENTS. <br> This value represent milliseconds. 1000 is one second. If you leave this out, chances are you will be banned from your exchange, most likely temporarily. You will have to tweak this number based upon your exchange. |
| `MaxAssets` | This is the maximum number of assets that can be traded simultaneously. |
| `ReduceOnly` | This tells the exchange NOT to flip a position from long to short or vice-versa. <br> It can have any value as its presence is only required. |
| `OrderTypeOverride` | This overrides the specified order type. |
| `Reduction` | The amount to reduce your position to all your exchange to close it. Deprecated... <br> This is a percentage. Do NOT put a percent (%) sign. Use this ONLY if you receive errors closing a position. Finding the amount of the reduction is strictly trial and error. |
| `Sandbox` | Any value accepted as its presence activates an exchange's testnet or sandbox mode |
| `OverridePCTtable` | Overrides thew PCT table and forces a balance percentage based upon the immediate current balance of the account for all orders on this exchange. |
| `RemapSymbol` | For use with the TradingView `{{ticker}}` macro. All orders for this account are remapped. |

Order types `OrderTypeOverride`:

| Property Name | Description |
| :--- | :--- |
| `Market` | Market order. You will pay taker fees |
| `Limit` | Limit order. Exchange decides what you pay (maker/taker). Unlike market orders, limit order have a high rate of failure. |
| `LimitTaker` | Limit order. You pay taker fee, This is a fill or kill order |
| `LimitMaker` | Limit order. You pay maker fee. |

Jackrabbit Relay supports multiple API keys per exchange (sub)account. This is
accomplished by this format:

```json
{ "Account":"MAIN","API 1":"YourAPI","SECRET 1":"YourSecret","RateLimit":"200" }
{ "Account":"MAIN","API 2":"YourAPI","SECRET 2":"YourSecret","RateLimit":"200" }
```

The above means the your MAIN account has two API/SECRET combinations that
Relay will rotate between. Each (sub)account can have as many as your
exchange will allow.

## Donations

Information regarding donations and supporting Jackrabbit Relay can be
found [here](./Documentation/Donations.MD).

