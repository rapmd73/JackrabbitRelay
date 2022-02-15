# JackrabbitRelay

Jackrabbit Relay is an API endpoint for stock, forex and cryptocurrency
exchanges that accept REST webhooks.

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

**Special Thanks** to the following people for providing me with testing
accounts.

    1. Me4tGrind3r | Jonas
    2. MisterCrease
    3. Riodda
    4. Cozzy
    5. bobo2314

Having the test accounts really help in tracking issues and solving
problems. If you would like to donate a test account, please DM me of Discord.

## Video

Yes, there's videos. Please watch them, then come back here and read
everything. Rinse and repeat as many times as needed :)

[Installing Jackrabbit Relay](https://youtu.be/cvtSHj1ubJs)

[Updating Jackrabbit Relay](https://youtu.be/Yb05lp9BPL4)

[Big update to Jackrabbit Relay](https://youtu.be/27XXZTIWSrw)

[Testing the Jackrabbit Relay Server](https://youtu.be/4l3yMbMc6Wc)

[Relay Extras](https://youtu.be/qXykEckzEgs)

## Exchanges
### Confirmed working exchanges

    ftx                 ftxus           kraken          kucoin

### Problematic exchanges

    binance

### Theoretically supported

This is a theoretical list. The exchange name listed below is what MUST be
used in your alert message to interact with a given exchange. Some
exchange may NOT work, but I have no way of testing them.

These exchanges accept market and limit orders,

    aax                  ascendex             bequant              bibox                bigone               
    binance              binancecoinm         binanceus            binanceusdm          bit2c                
    bitbank              bitbay               bitbns               bitcoincom           bitfinex             
    bitfinex2            bitflyer             bitforex             bithumb              bitmex               
    bitpanda             bitrue               bitso                bitstamp             bitstamp1            
    bittrex              bitvavo              bl3p                 blockchaincom        btcalpha             
    btcbox               btcmarkets           btctradeua           btcturk              buda                 
    bw                   bybit                bytetrade            coinbase             coinbaseprime        
    coinbasepro          coincheck            coinfalcon           coinmate             coinone              
    coinspot             crex24               cryptocom            currencycom          delta                
    deribit              digifinex            eqonex               equos                exmo                 
    flowbtc              fmfwio               ftx                  ftxus                gateio               
    gemini               hitbtc               hitbtc3              hollaex              idex                 
    independentreserve   indodax              itbit                kraken               kucoin               
    kucoinfutures        kuna                 latoken              latoken1             lbank                
    liquid               luno                 lykke                mercado              mexc                 
    ndax                 novadax              oceanex              paymium              phemex               
    poloniex             qtrade               ripio                stex                 therock              
    tidebit              tidex                timex                vcc                  wazirx               
    xena                 yobit                zaif                 zb                   zipmex               
    zonda                

These exchanges accept only LIMIT orders,

    bitget               bitmart              cdax                 cex                  coinex               
    huobi                huobijp              huobipro             okcoin               okex                 
    okex5                okx                  probit               upbit                wavesexchange        
    whitebit             woo                  

## Requirements

This software requires a VPS with one core, one gig of RAM, 2 gigs of
swap, 40 gigs of SSD storage. This software was developed for the
intention of using a VPS to its fullest extent. If you wish to use a
virtual environment, please consult your VPS documentation.

Jackrabbit Relay requires Python 3 and pip3. If you do not have pip3, the
below link will show you how to install it.

    https://www.linuxscrew.com/install-pip

The command for installation really is very simple and here is the short
version. please be sure you are in route or in your virtual environment
appropriate to the documentation of your VPS. the below command is for
Ubuntu.you will need to use the package manager appropriate to your VPS.

    apt install python3-pip

## Security and firewall

Whitelisting IP addresses and setting up restrictions is solely to the
the responsibility of your native firewall. There is absolutely no way I
can provide any level of security that is even remotely comparable to the
firewall your VPS already comes with. Suggesting such is a severe
misnomer to you and the security of your VPS. Please consult the
documentation of your VPS for establishing your firewall rules.

## Installation

Please be aware that you may need to switch to your root account. Please
follow the necessary instructions provided by your VPS provider. This
document assumes you are already at root level or have your virtual
environment established, both are beyond the scope of this
documentation.

Start with these shell commands

```bash
mkdir -p /home/GitHub
cd /home/GitHub
git clone https://github.com/rapmd73/JackrabbitRelay
```

You now have a copy of the Jackrabbit Relay repository. Now its time to install
everything.

```bash
cd /home/GitHub/JackrabbitRelay
./install
```

At this point the files are installed, but more setup is required before
Relay is ready to run. Configuring the exchanges and crontab need to be
completed next.

## Updating

Please be sure to update Jackrabbit Relay frequently. The following commands can be used to pull the latest code from GitHub:

```bash
cd /home/GitHub/JackrabbitRelay
git pull https://github.com/rapmd73/JackrabbitRelay
```

**IMPORTANT** This only updates the files in the GitHub directory. **IT
DOES NOT OVERWRITE ANY FILES IN THE WORKING DIRECTORIES**

To update code that was installed via the `./install` script, there is also an update script that will do this for you. It also updates the Extras and Equilibrium directories as applicable:

```bash
cd /home/GitHub/JackrabbitRelay
./update
```

## Structure

The Jackrabbit Relay file structure and folder layout is as follows:

| Folder | Description |
| :--- | :--- |
| `/home/JackrabbitRelay/` | This is the main folder |
| `/home/JackrabbitRelay/Config/` | This is where all configuration files are stored |
| `/home/JackrabbitRelay/Base/` | All program files go here |
| `/home/JackrabbitRelay/Logs/` | All log files go here |

In the base directory (`/home/JackrabbitRelay/Base/`), there are several
files:
| File | Description |
| :--- | :--- |
| `CCXT-PlaceOrder.spot` and `CCXT-PlaceOrder.future` | These are the Order Processors. You actually wont use these files directly, but rather copy them to the actual exchange designated order transactor, for example `PlaceOrder.ftxus.spot` |
| `PlaceOrder.tester.spot` | This is just a dummy test module that you can use to test the connection with TradingView. |
| `JackrabbitRelay` | This is the actual server program that waits for a connection. It should NOT be ran directly, but rather through the RelayLauncher shell script. |
| `RelayLauncher` | This shell script sets the port and launches the server. It is the harness that keeps everything running and is what you place in your CronTab. |

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

Order types (for `OrderType`/`OrderTypeOverride`):

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

## Reboot startup

For Jackrabbit Relay to auto start after a reboot, the following line
needs to be added to your crontab. BE SURE TO CHANGE THE 12345 TO THE
PORT YOU WANT.

```crontab
@reboot ( /home/JackrabbitRelay/Base/RelayLauncher 12345 & ) > /dev/null 2>&1
```

## Manual startup

Use the following command. Be sure to replace the 12345 with the proper port.

```bash
( /home/JackrabbitRelay/Base/RelayLauncher 12345 & ) > /dev/null 2>&1
```

## Incoming Messages
sent from TradingView or similar webhook based application. Any tool that can make HTTP requests, such as Postman or curl, can be used as well. These can be POST requests with the payload as the body. 

HTTP request messages should be sent to the address can by the hostname (IP address) of your server, and the port specified above (under #reboot-startup and #manual-startup). For example:

```
POST http://YOUR.VPS.IP.ADDRESS:12345 [with payload as described below]
```


### The Payload

Here are examples of the payload:

This example purchased $30 of AAVE on the FTX US exchange.

```json
{ "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD","USD":"30" }
```

This example purchases the minimum amount of AAVE in USD

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

Description of the payload

| Property Name | Description |
| :--- | :--- |
| `Exchange` | This is one of the [supported exchanges](#exchanges) |
| `Market` | This is the market you are trading. <table><tr><td>`Spot`<td><td>Working</td></tr><tr><td>`Future`<td><td>Working</td></tr><tr><td>`Margin`<td><td>In progress</td></tr></table> |
| `Account` | All main accounts must be called `MAIN`. Subaccounts can be used (if your exchange supports them) and must be exactly as listed on the exchange. |
| `Action` | This is one of the [supported actions](#actions) |
| `Asset` | The asset you are trading.  Must be exactly as the exchange lists it. Hint: Use [ListMarkets](Extras/README.md#listmarkets) to confirm |
| `USD` / `Base` / `Quote` | Choose only one to set the amount to be purchased/sold: <li>`USD` will only work if the asset has a corresponding USD pair to do a proper base conversion on.</li> <li> `Base` is the asset itself value, ie BTC, ADA, AAVE, so one. A base of 1 for BTC is to purchase 1 BTC.</li> <li>`Quote` is the value of the asset in its quote currency. For example, if you want to purchase BCH/BTC using the price value of BTC, then you specify your amount in the quote currency.</li> |
| `Leverage` | For binanceusdm and ftx, this sets the leverage amount |
| `Margin` | For binanceusdm, this sets the margin to `Crossed` or `Isolated`. |

### Actions
| Action | Description |
| :--- | :--- |
| `Buy` | Purchase an asset. |
| `Sell` | Sell a portion of asset. If amount is more than balance, the full position will be plosed. |
| `Close` | Sell all of the asset. |
| `Long` | (Perpetuals) Opens a long position, and can flip a short to long (if `ReduceOnly` is not included in configuration). |
| `Short` | (Perpetuals) Opens a short position, and can flip a long to short (if `ReduceOnly` is not included in configuration). |

## Logging

Below are examples of the log files.

This is the Jackrabbit Relay server log file:

```log
2021-09-22 22:34:53.059783 62.151.179.169   ('POST / HTTP/1.1', '200', '-')
```

Here is an example of the Place Order log for the FTX US exchange:

```log
2021-09-22 22:34:53.277575 1009381 Processing order
2021-09-22 22:34:53.277851 1009381 Order Parsed
2021-09-22 22:34:53.277908 1009381 |- Exchange: ftxus
2021-09-22 22:34:53.277943 1009381 |- Target Market: Spot
2021-09-22 22:34:53.277974 1009381 |- Account reference: MAIN
2021-09-22 22:34:53.278003 1009381 |- Trade Action: close
2021-09-22 22:34:53.278032 1009381 |- Asset: SUSHI/USD
2021-09-22 22:34:53.278060 1009381 |- Using minimum position size
2021-09-22 22:34:53.278166 1009381 API/Secret loaded for ftxus, (sub)account: MAIN
2021-09-22 22:34:53.282798 1009381 |- Rate limit set to 200 ms
2021-09-22 22:34:53.519999 1009381 Markets loaded
2021-09-22 22:34:53.520204 1009381 Base currency:  SUSHI
2021-09-22 22:34:53.520250 1009381 Quote currency: USD
2021-09-22 22:34:53.773082 1009381 Getting market: SUSHI/USD
2021-09-22 22:34:53.773290 1009381 |- Minimum: 0.5
2021-09-22 22:34:53.773339 1009381 |- Amount: 0.5
2021-09-22 22:34:54.000871 1009381 Previous Balance: 3.500000 SUSHI
2021-09-22 22:34:54.001063 1009381 |- Forcing balance
2021-09-22 22:34:54.001123 1009381 Placing Order
2021-09-22 22:34:54.001157 1009381 |- Pair: SUSHI/USD
2021-09-22 22:34:54.001187 1009381 |- Action: close
2021-09-22 22:34:54.001219 1009381 |- Amount: 3.5
2021-09-22 22:34:54.001250 1009381 |- Close: 10.4774
2021-09-22 22:34:54.001291 1009381 |- Price: 36.6709
2021-09-22 22:34:54.280677 1009381 |- ID: 1547473833
2021-09-22 22:34:54.398102 1009381 New Balance: 0.000000 SUSHI
2021-09-22 22:34:54.398277 1009381 Processing Completed: 01.120702 seconds
```

## Extras

The Extras folder has many interesting scripts/programs and its own [README](./Extras/README.md).

## Donations

If you would like to help support this project financially, please use
any of the below addresses. Anything donated goes to the costs of
sustaining Jackrabbit Relay. Thank you.

You can subscribe to the Jackrabbit Relay tier for recurring monthly
support:

    https://www.patreon.com/RD3277

If you perfer crypto or just a one time donation, please use any of the
below:
| | |
| :--- | :--- |
| BCH | bitcoincash:qzw5h5ccfz6v7zzh0vf5pl0eqp3zjmp5us07l72nvv|
| BTC | 3JUbL3Vsj61VBAmyHtQhyiFJcizEfxAvzV |
| ETH | 0x3c6C06150B2f24b3179a50b618aD3c0f58CF74FD |
| LINK | 0xd8Fd4fA3b489861ad6Eb95a0617B4DA7c78123F8 |
| LTC | MHj8nQcRdJWVVNeHUemSQgzBw3cPrZEtRU |
| USDT | 0xd8Fd4fA3b489861ad6Eb95a0617B4DA7c78123F8 |