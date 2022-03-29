# Black Crow Hunter

***HAVE YOUR BANKRUPTCY PAPERS READY***

In trading, a black crow is 3 consecutive downwards candles.
BlackCrowHunter takes this concept and extends it to allow the ability to
search for any number of downward candles.

Simply put, the more consecutive candles in a row, the less purchases
made and the more likely the market will rebound. Fewer candles are more
aggressive and more accumulation.

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

## Notes

All programs now use a config file in JSON format. Commandline arguments 
are **NO LONGER USED.**

## Installation

Installation is very simple. Just follow the below:

```bash
cd /home/GitHub/JackrabbitRelay/Extras/BlackCrowHunter
./install
```

## Configuration file

The following describes the new configuration layout. This is the **NEW
STANDARD** moving forward as it is extendable and more robust then the
commandline. *This MUST be in proper JSON format*.

Data and time must be in the exact format as shown. If your exchange
returns no data, your date/time selection is out of range. Pick a more
recent date/timwe combination.

```json
{
    "DateTime":"2019-07-04 00:00:00",
    "Timeframe":"1m",
    "Exchange":"kucoin",
    "Account":"MAIN",
    "Asset":"ADA/USDT",
    "StartCandles":"3",
    "TakeProfit":"1",
    "BuyLots":"1"
}
```

| Item             | Value        | Description |
| ----             | -----        | -------------------- |
| `"DateTime"`     | `"2019-07-04 00:00:00"` | Date and time to start collecting historic data |
| `"Timeframe"`    | `"1m"`       | Used in collection, backtesting. Timeframe. Most exchanges support `1m`, `5m`, `15m`, `1h`, `4h`, `1d` for timeframes |
| `"Exchange"`     | `"kucoin"`   | Your exchange |
| `"Account"`      | `"MAIN"`     | Your (sub)account |
| `"Asset"`        | `"ADA/USDT"` | The asset (pair) you want to trade |
| `"StartCandles"` | `"3"`        | The starting number of candles to match for the Black Crow pattern |
| `"TakeProfit"`   | `"1"`        | Take profit in percentage |
| `"BuyLots"`      | `"1"`        | The number of lots to begin the first purchased |

## Reboot startup

For BlackCrowHunter to auto start after a reboot, the following line
needs to be added to your crontab. 

```crontab
@reboot ( /home/BlackCrowHunter/Launcher /home/BlackCrowHunter/TRX.cfg & ) > /dev/null 2>&1
```

Please be aware that the exchange, coin, and other parameters **MUST**
match the below usage. The cronjob will only work properly when it is
aligned with a tested working coin.

You should extensively test your coin first with a virtual console
**before** setting up a cronjob.

## Configuration

BlackCrowHunter uses the same configuration as Jackrabbit Relay, *with one
very import addition*. Your configuration must have a webhook item on
each API/Secret combination the BlackCrowHunter uses.

This example is for KuCoin, but applies to *all* exchanges where
BlackCrowHunter will be used. The Webhook **MUST** be present and point to
your IP address/port entry for Jackrabbit Relay. 

**The port used below, 7732, is EXAMPLE ONLY. It MUST be changed to YOUR
installation.**

```json
# Spot Market - JackrabbitRelay
{ "Account":"MAIN","API":"API1","SECRET":"SECRET1","Passphrase":"pw1","RateLimit":"1000","Retry":"3","Webhook":"http://127.0.0.1:7732" }

# Spot Market - JackrabbitRelay1
{ "Account":"MAIN","API":"API2","SECRET":"SECRET2","Passphrase":"pw2","RateLimit":"1000","Retry":"3","Webhook":"http://127.0.0.1:7732" }

# Spot Market - JackrabbitRelay2
{ "Account":"MAIN","API":"API3","SECRET":"SECRET3","Passphrase":"pw3","RateLimit":"1000","Retry":"3","Webhook":"http://127.0.0.1:7732" }
```

BlackCrowHunter rotates your API/Secret on **EVERY** call to your exchange.
You should have *at least* **THREE (3)** API/Secret listings in your
exchange configuration that BlackCrowHunter will use.

BlackCrowHunter does not have to be on the same machine as Relay, but latency
and slippage will be a consideration otherwise, not to mention security.

## Backtesting

**ALWAYS** backtest first.

```bash
cd /home/BlackCrowHunter
./CandleCollector /home/BlackCrowHunter/BNB.cfg
./Backtest.historic /home/BlackCrowHunter/BNB.cfg
```

Runs a backtest with results. You must have collected the historic data
with the above process. You can run multiple tests with different candle
counts without having to redownload (recollect) the data. The more data
you collect, the more memory intensive the process will be.

## Usage

```bash
cd /home/BlackCrowHunter
./Launcher /home/BlackCrowHunter/ADA.cfg
```

## Results

Results breakdown for buys,

| Column | Example   | Description |
| --- | --------- | -------------------- |
| 1 | `2021-12-19 19:24` | Date/Time |
| 2 | `Buy`              | Direction |
| 3 | `46699.70000000`   | Closing (Buy) price |
| 4 | `46690.45000000`   | Running Average is more then 1 purchase has occurred |
| 5 | `47166.69700000`   | Take profit price. Recalculated every purchase |
| 6 | `5`                | The Number of red candles that *this* purchase matched. This will increase as purchases increase. This is a deliberate limiter to slow accumulation extensively. |

Results breakdown for sells,

| Column | Example   | Description |
| --- | --------- | -------------------- |
| 1 | `2021-12-19 19:24` | Date/Time |
| 2 | `Sell`             | Direction |
| 3 | `47179.80000000`   | Closing (Sell) price |
| 4 | `46690.45000000`   | Result of closing price less average. This is literal in context of owing actual amount, ie, 1 BTC |
| 5 | `93380.90000000`   | Statistical, total accumulation |

```log
Reading historic data...
2021-12-19 19:24 Buy    46699.70000000                    47166.69700000
2021-12-19 21:57 Buy    46681.20000000   46690.45000000   47157.35450000  5
2021-12-19 22:46 Sell   47179.80000000     489.35000000   93380.90000000
2021-12-19 23:13 Buy    47143.30000000                    47614.73300000
2021-12-19 23:58 Buy    46686.80000000   46915.05000000   47384.20050000  5
2021-12-20 03:19 Buy    46560.20000000   46796.76666667   47264.73433333  6
2021-12-20 06:33 Buy    46428.30000000   46704.65000000   47171.69650000  8
2021-12-20 21:07 Sell   47192.80000000     488.15000000  186818.60000000
2021-12-20 23:54 Buy    46894.40000000                    47363.34400000
2021-12-21 00:36 Buy    46883.90000000   46889.15000000   47358.04150000  5
2021-12-21 00:37 Buy    46886.50000000   46888.26666667   47357.14933333  6
2021-12-21 03:34 Sell   47525.50000000     637.23333333  140664.80000000
2021-12-21 04:41 Buy    48605.60000000                    49091.65600000
2021-12-21 05:26 Buy    48580.00000000   48592.80000000   49078.72800000  5
2021-12-21 05:27 Buy    48580.20000000   48588.60000000   49074.48600000  6
2021-12-21 05:40 Buy    48422.50000000   48547.07500000   49032.54575000  8
2021-12-21 12:21 Sell   49096.60000000     549.52500000  194188.30000000
2021-12-21 13:14 Buy    48649.90000000                    49136.39900000
2021-12-21 15:31 Buy    48473.70000000   48561.80000000   49047.41800000  5
2021-12-21 15:32 Buy    48515.20000000   48546.26666667   49031.72933333  6
2021-12-21 18:56 Buy    48448.50000000   48521.82500000   49007.04325000  8
2021-12-21 21:43 Sell   49072.10000000     550.27500000  194087.30000000
2021-12-21 23:41 Buy    49114.40000000                    49605.54400000
2021-12-22 00:46 Buy    48868.60000000   48991.50000000   49481.41500000  5
2021-12-22 02:31 Sell   49510.00000000     518.50000000   97983.00000000
2021-12-22 03:01 Buy    49371.20000000                    49864.91200000
2021-12-22 03:15 Buy    49284.80000000   49328.00000000   49821.28000000  5
2021-12-22 04:23 Buy    49281.90000000   49312.63333333   49805.75966667  6
2021-12-22 15:30 Buy    48698.90000000   49159.20000000   49650.79200000  8
2021-12-23 17:42 Sell   49690.00000000     530.80000000  196636.80000000
2021-12-23 23:00 Buy    50814.10000000                    51322.24100000
2021-12-23 23:18 Buy    50711.70000000   50762.90000000   51270.52900000  5
2021-12-24 00:14 Buy    50699.00000000   50741.60000000   51249.01600000  6
2021-12-24 01:35 Sell   51300.00000000     558.40000000  152224.80000000
2021-12-24 03:54 Buy    50983.50000000                    51493.33500000
2021-12-24 06:59 Buy    50882.00000000   50932.75000000   51442.07750000  5
2021-12-24 11:24 Sell   51453.00000000     520.25000000  101865.50000000
2021-12-24 11:33 Buy    51166.70000000                    51678.36700000
2021-12-24 14:59 Buy    50777.70000000   50972.20000000   51481.92200000  5
2021-12-24 18:50 Sell   51600.00000000     627.80000000  101944.40000000
2021-12-24 19:39 Buy    51442.40000000                    51956.82400000
2021-12-24 21:39 Buy    50900.00000000   51171.20000000   51682.91200000  5
2021-12-24 22:48 Buy    50622.20000000   50988.20000000   51498.08200000  6
2021-12-24 22:49 Buy    50657.40000000   50905.50000000   51414.55500000  8
2021-12-25 16:21 Buy    50569.40000000   50838.28000000   51346.66280000 10
2021-12-25 16:22 Buy    50671.20000000   50810.43333333   51318.53766667 13
2021-12-27 13:28 Sell   51320.20000000     509.76666667  304862.60000000
2021-12-30 02:08 Buy    46389.20000000                    46853.09200000
2021-12-30 04:15 Sell   46868.10000000     478.90000000   46389.20000000
2021-12-30 08:19 Buy    46978.60000000                    47448.38600000
2021-12-30 11:13 Buy    46921.70000000   46950.15000000   47419.65150000  5
2021-12-30 11:14 Buy    46933.30000000   46944.53333333   47413.97866667  6
2021-12-30 11:44 Sell   47423.90000000     479.36666667  140833.60000000
2021-12-30 15:27 Buy    47392.10000000                    47866.02100000
2021-12-30 15:58 Buy    47204.10000000   47298.10000000   47771.08100000  5
2021-12-30 18:53 Sell   47808.30000000     510.20000000   94596.20000000
2021-12-30 19:47 Buy    47816.80000000                    48294.96800000
2021-12-30 19:58 Buy    47556.90000000   47686.85000000   48163.71850000  5
2021-12-30 19:59 Buy    47559.70000000   47644.46666667   48120.91133333  6
2021-12-30 20:44 Buy    47417.20000000   47587.65000000   48063.52650000  8
2021-12-31 04:36 Buy    47337.20000000   47537.56000000   48012.93560000 10
2021-12-31 08:32 Sell   48040.00000000     502.44000000  237687.80000000
2022-01-01 14:36 Buy    46923.40000000                    47392.63400000
2022-01-01 15:38 Sell   47462.00000000     538.60000000   46923.40000000
2022-01-01 15:52 Buy    47229.10000000                    47701.39100000
2022-01-01 17:39 Sell   47756.10000000     527.00000000   47229.10000000
2022-01-01 18:37 Buy    47498.50000000                    47973.48500000
2022-01-01 20:43 Buy    47408.70000000   47453.60000000   47928.13600000  5
2022-01-02 03:44 Buy    47401.80000000   47436.33333333   47910.69666667  6
2022-01-02 04:19 Buy    47298.40000000   47401.85000000   47875.86850000  8
2022-01-02 17:00 Sell   47938.60000000     536.75000000  189607.40000000
2022-01-02 18:29 Buy    46935.60000000                    47404.95600000
2022-01-02 19:28 Buy    46932.40000000   46934.00000000   47403.34000000  5
2022-01-02 23:30 Sell   47447.80000000     513.80000000   93868.00000000
2022-01-02 23:39 Buy    47327.90000000                    47801.17900000
2022-01-03 03:12 Buy    46986.60000000   47157.25000000   47628.82250000  5
2022-01-03 03:13 Buy    46994.30000000   47102.93333333   47573.96266667  6
2022-01-03 09:18 Buy    46865.80000000   47043.65000000   47514.08650000  8
2022-01-03 12:13 Sell   47522.60000000     478.95000000  188174.60000000
2022-01-03 17:44 Buy    46586.20000000                    47052.06200000
2022-01-03 18:59 Buy    46473.50000000   46529.85000000   46995.14850000  5
2022-01-03 19:00 Buy    46473.80000000   46511.16666667   46976.27833333  6
2022-01-03 20:23 Buy    45949.50000000   46370.75000000   46834.45750000  8
2022-01-04 13:29 Sell   46879.10000000     508.35000000  185483.00000000
2022-01-04 17:28 Buy    46827.10000000                    47295.37100000
2022-01-04 18:01 Buy    46545.70000000   46686.40000000   47153.26400000  5
2022-01-04 18:02 Buy    46624.90000000   46665.90000000   47132.55900000  6
2022-01-05 01:52 Buy    46188.80000000   46546.62500000   47012.09125000  8
2022-01-06 01:54 Buy    43415.00000000   45920.30000000   46379.50300000 10
2022-01-09 08:22 Buy    41702.70000000   45217.36666667   45669.54033333 13

```

## Donations

Information regarding donations and supporting Jackrabbit Relay can be found [here](./Documentation/Donations.MD).

