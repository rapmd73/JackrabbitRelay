# Equilibrium

The byproduct of the Jackrabbit Savings Account and a grid bot...

That is the simple explanation. The proper one is far more complicated.

Equilibrium is a "grid tracking" algorithm that works very similar to the
Jackrabbit Savings Account module, with one very distinct difference.

Equilibrium does not channel lock. Its algorithms allow it to buy and
sell in ranged markets. The more prolonged the ranged market is, the more
profitable Equilibrium is.

**Equilibrium is very different from every other Jackrabbit paradigm**.
Please be sure to read this entire file first and paper trade before
risking real money.

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

## Videos

[Introducing Equilibruim: Abstract Theory](https://youtu.be/kGpoD-dJ1k4)

[Equilibrium: trial by fire](https://youtu.be/RU8zgGDfbao)

[Equilibrium unleashed (installing it)](https://youtu.be/Nwr2fH8LQw8)

## Installation

Installation is very simple. Just follow the below:

    cd /home/GitHub/JackrabbitRelay/Extras/Equilibrium
    ./install

## Reboot startup

For Equilibrium to auto start after a reboot, the following line
needs to be added to your crontab. 

    @reboot ( /home/Equilibrium/Launcher ftxus MAIN trx/usd 2 1 PAPER & ) > /dev/null 2>&1

Please be aware that the exchange, coin, and other parameters **MUST**
match the below usage. The cronjob will only work properly when it is
aligned with a tested working coin.

You should extensively test your coin first with a virtual console
**before** setting up a cronjob.

## Configuration

Equilibrium uses the same configuration as Jackrabbit Relay, *with one
very import addition*. Your configuration must have a webhook item on
each API/Secret combination the Equilibrium uses.

This example is for KuCoin, but applies to *all* exchanges where
Equilibrium will be used. The Webhook **MUST** be present and point to
your IP address/port entry for Jackrabbit Relay. 

**The port used below, 7732, is EXAMPLE ONLY. It MUST be changed to YOUR
installation.**

    # Spot Market - JackrabbitRelay
    { "Account":"MAIN","API":"API1","SECRET":"SECRET1","Passphrase":"pw1","RateLimit":"1000","Retry":"3","Webhook":"http://127.0.0.1:7732" }

    # Spot Market - JackrabbitRelay1
    { "Account":"MAIN","API":"API2","SECRET":"SECRET2","Passphrase":"pw2","RateLimit":"1000","Retry":"3","Webhook":"http://127.0.0.1:7732" }

    # Spot Market - JackrabbitRelay2
    { "Account":"MAIN","API":"API3","SECRET":"SECRET3","Passphrase":"pw3","RateLimit":"1000","Retry":"3","Webhook":"http://127.0.0.1:7732" }

Equilibrium rotates your API/Secret on **EVERY** call to your exchange.
You should have *at least* **THREE (3)** API/Secret listings in your
exchange configuration that Equilibrium will use.

Equilibrium does not have to be on the same machine as Relay, but latency
and slippage will be a consideration otherwise, not to mention security.

## Usage

    cd /home/Equilibrium
    ./Launcher       ftxus MAIN trx/usd  2   Bal AUTO PAPER

Or

    cd /home/Equilibrium
    ./Launcher       ftxus MAIN trx/usd  2   1   1.1  PAPER

Or

    cd /home/Equilibrium
    ./Launcher       ftxus MAIN trx/usd  2   1.1 1    PAPER

Or

    cd /home/Equilibrium
    ./Launcher       ftxus MAIN trx/usd  2   1   1    PAPER

Or, for futures trading

    cd /home/Equilibrium
    ./LauncherFuture ftx   MAIN TRX-PERP 0.5 Bal AUTO Short

This launches Equilibrium. The arguments are as follows:

| Argument | Example   | Argument description |
| --- | --------- | -------------------- |
| 1 | `ftxus`   | Exchange             |
| 2 | `MAIN`    | Account (Case sensitive) |
| 3 | `trx/usd` | Asset                |
| 4 | `2`       | Deviation/Take Profit/Boundary in percent form. (`2` maps to 2%) |
| 5 | `1` or `Bal` | **Number of lots to buy** <br><br> A lot is the minimum position size. If you wanted a $10 position of an asset that has a minimum position size of $2.50, you would want `4` lots. <br><br> `Bal`: This tells Equilibrium to calculate the number of lots based on the balance of the (sub)account and the boundary. **NOTE**: This also tells Equilibrium to replace the value for the 6th argument. |
| 6 | `1.1` or `AUTO` | **Number of lots to sell** <br><br> This is the number of lots to sell. It works exactly like the buy lots with one very distinct difference: If you put **`AUTO`** (or if you set `Bal` for the 5th argument), the selling lot size will be 10% more then the buying lot size. <br><br> If your selling lot size is equal to your buying lot size, reverse trading will **NOT** take place. <br><br> If your selling lots size is less then your buying size, you will ACCUMULATE the diffence in your account. For example, if your buying lot size is 2 and your selling lot size is 1.9, you will ACCUMULATE 0.1 of the asset with each SELL. |
| 7 | `Long` or `Short` | **Trade direction, used with futures ONLY.** Not used for SPOT. *(Simply leave this out for spot)* <br><br> Long or Short direction for trading. You can NOT use both in the same (sub)account, doing so WILL cause losses. |
| 8 | `PAPER` | This activates the paper trading mode. Equilibrium will do everything except actually place orders to the exchange. <br><br> **Even in PAPER mode, you API/Secret and Webhook must be correct as Equilibrium WILL login into your account using your exchange's private API/rate limit values to get the prices.** <br><br> After testing in paper trading mode, you can remove this to enable live trading. |

## Donations

If you would like to help support this project financially, please use
any of the below addresses. Anything donated goes to the costs of
sustaining Jackrabbit Relay. Thank you.

You can subscribe to the Jackrabbit Relay tier for recurring monthly
support:

    https://www.patreon.com/RD3277

If you perfer crypto or just a one time donation, please use any of the
below:

    BCH     bitcoincash:qzw5h5ccfz6v7zzh0vf5pl0eqp3zjmp5us07l72nvv
    BTC     3JUbL3Vsj61VBAmyHtQhyiFJcizEfxAvzV
    ETH     0x3c6C06150B2f24b3179a50b618aD3c0f58CF74FD
    LINK    0xd8Fd4fA3b489861ad6Eb95a0617B4DA7c78123F8
    LTC     MHj8nQcRdJWVVNeHUemSQgzBw3cPrZEtRU
    USDT    0xd8Fd4fA3b489861ad6Eb95a0617B4DA7c78123F8
