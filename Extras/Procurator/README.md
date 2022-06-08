# Procurator

**WORKING (hopefully) ALPHA**, *you are likely to LOOSE your money*.

The Procurator is a market making traditional grid bot.

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

## WARNING

Kucoin subaccounts do **NOT** seem to have a way to cancel limit orders
from either the web site or the app.

Plan your budget carefully. You should consider DOUBLE what you expect during testing.

If the program crashes, **ALL** limit orders remain **IN EFFECT** until
**YOU** cancel them.

## Installation

Installation is very simple. Just follow the below:

```bash
cd /home/GitHub/JackrabbitRelay/Extras/Procurator
./install
```

## Manual usage

Use a command such as the following command.

```bash
cd /home/Procurator
./Procurator USDT.cfg
```

## Additional programs

| Program | Description |
| --- | -------------------- |
| CancelAllOrders | Cancels all orders on the Exchange/account for a specific pair |
| ListOpenOrders | Displays all orders on the Exchange/account for a specific pair |

## Configuration files

JSON format:

```json
{
    "TakeProfit":"0.20",
    "ProfitBuy":"USDC/USD",
    "Exchange":"ftx",
    "Account":"MAIN",
    "Asset":"USDT/USD",
    "Steps":"25",
    "Top":"1.002",
    "Bottom":"0.997",
    "PositionSize":"1"
}
```

The items that can be used in this file,

| Argument | Example   | Description |
| --- | --------- | -------------------- |
| `Exchange` | `ftxus`   | Exchange             |
| `Account` | `MAIN`    | Account or subaccount (Case sensitive) |
| `Asset` | `trx/usd` | Asset |
| `Top` | `1.002` | the highest level of the grid |
| `Bottom` | `0.997` | The lowest level of the grid |
| `Steps` | `1`       | This is the number of grid levwls you want. |
| `Pips` | `0.001`       | This is the number of pips per levwl you want. Should be greater or equal to 1 pip (0.0001) |
| `PositionSize` | `2` | Amount according to **BASE** currency |
| `TakeProfit` | `0.20` | This is the minimum profit you want removed from your bot |
| `ProfitBuy` | `USDC/USDT` | This is the asset you want purchased for your profit store |
| `ProfitSell` | `USDT/USD` | This is for converting crypto to fiat. `USDT` is YOUR quote qurrency of the asset. `USD` is YOUR fiat |

## Donations

Information regarding donations and supporting Jackrabbit Relay can be
found [here](./Documentation/Donations.MD).

