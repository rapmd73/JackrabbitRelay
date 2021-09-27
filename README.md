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

Currently, Jackrabbit Relay supports ONLY spot markets. Work is being done
to supprt futures and margins. Some exchanges may work already, but I
don't know which ones as many I can't test personally.

## Video

Yes, there's a video. Please watch it, then come back here and read
everything. Rinse and repeat as many times as needed :)

[Installing Jackrabbit Relay](https://youtu.be/cvtSHj1ubJs)

[Updaing Jackrabbit Relay](https://youtu.be/Yb05lp9BPL4)

## Confirmed working exchanges

    FTX
    FTX US
    Kraken

## Theorically supported

This is a theorical list. The exchange name listed below is what MUST be
used in your alwert message to interact with a given exchangge. Some
exchange may NOT work, but I have no way of testing them.

    aax            aofex          ascendex           bequant
    bibox          bigone         binance            binancecoinm 
    binanceus      binanceusdm    bit2c              bitbank
    bitbay         bitbns         bitcoincom         bitfinex
    bitfinex2      bitflyer       bitforex           bitget
    bithumb        bitmart        bitmex             bitpanda 
    bitso          bitstamp       bitstamp1          bittrex
    bitvavo        bitz           bl3p               braziliex 
    btcalpha       btcbox         btcmarkets         btctradeua 
    btcturk        buda           bw                 bybit 
    cdax           cex            coinbase           coinbaseprime 
    coinbasepro    coincheck      coinegg            coinex
    coinfalcon     coinfloor      coinmarketcap      coinmate 
    coinone        coinspot       crex24             currencycom 
    delta          deribit        digifinex          eqonex
    equos          exmo           exx                flowbtc 
    ftx            ftxus          gateio             gemini 
    hbtc           hitbtc         hollaex            huobi 
    huobijp        huobipro       idex               independentreserve 
    indodax        itbit          kraken             kucoin
    kuna           latoken        lbank              liquid 
    luno           lykke          mercado            mixcoins 
    ndax           novadax        oceanex            okcoin 
    okex           okex3          okex5              paymium 
    phemex         poloniex       probit             qtrade 
    ripio          stex           therock            tidebit 
    tidex          timex          upbit              vcc 
    wavesexchange  whitebit       xena               yobit 
    zaif           zb

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
follow the neccessary instructions provided by your VPS provider. This
document assumes you are already at root level or have your virtual
environment established, both are beyound the scope of this
documentatiom.

Start with these shell commands

    mkdir -p /home/GitHub
    cd /home/GitHub
    git clone https://github.com/rapmd73/JackrabbitRelay

You now have a copy of the Jackrabbit repository. Now its time to install
everything.

    cd /home/GitHub/JackrabbitRelay
    ./install

At this point the files are inatalled, but more setup is required before
Relay is ready to run. Configuring the exchanges and crontab need to be
completed next.

## Updating

Please be sure to update Jackrabbit Relay frequently. The following commands can be used:

    cd /home/GitHub/JackrabbitRelay
    git pull https://github.com/rapmd73/JackrabbitRelay

**IMPORTANT** This only updates the files in the GitHuib directory. **IT
DOES NOT OVERWWITE ANY FILES IN THE WORKING DIRECTORIES**

## Configuration

The Jackrabbit Relay file structure and folder layout is very simple:

    /home/JackrabbitRelay/

        This is the main folder

    /home/JackrabbitRelay/Config

        This is where all configuration files are stored

    /home/JackrabbitRelay/Base

        All program files go here

    /home/JackrabbitRelay/Logs

        All log files go here

In the base directory (/home/JackrabbitRelay/Base), there are several
files:

    CCXT-PlaceOrder

        This is the Order Processor. You actually wont use this file
        directly, but rather copy it to the actual exchange designated
        order transactor, for example PlaceOrder.ftxus

    PlaceOrder.tester

        This is just a dummy test module that you can use to test the
        connection with TradingView. It too, gets copied to the exchange
        designator, for example, PlaceOrder.kraken

    JackrabbitRelay

        This is the actual server program that waits for a connewction.
        It should NOT be ran directly, but rather through the
        RelayLauncher shell script.

    RelayLauncher

        This shell script sets the port and launches the server. It is
        the harness that keeps everything running and is what you place
        in your CronTab.

The Jackrabbit Relay files are ver sime JSON based text.  Here is an example:

    { "Account":"MAIN","API":"YourAPI","SECRET":"YourSecret","RateLimit":"200" }

This would be placed in a folder called /home/JackrabbitRelay/Config and
named something like ftxus.cfg

This file would be the configuration for the FTX.US exchange.

Now for the details:

    Account: this MUST be MAIN, case sensitive, for the main account of
    every exchange.

    API: your API key exactly as your exchange gives it to you.

    SECRET: your SECRET exactly as your exchange gives it to you.

    RateLimit: This is the amount Relay waits between each exchange API
    call.

        ALL EXCHANGES HAVE RATE LIMIT REQUIREMENTS.

        This value represent milliseconds. 1000 is one second. If you
        leave this out, chances are you will be banned from your
        exchange, most likely temporarily. You will have to tweak this
        number based upon your exchange.

Jackrabbit support multiple API per exchange (sub)account. This is
accomplished by this format:

    { "Account":"MAIN","API 1":"YourAPI","SECRET 1":"YourSecret","RateLimit":"200" }
    { "Account":"MAIN","API 2":"YourAPI","SECRET 2":"YourSecret","RateLimit":"200" }

The above means the your MAIN account has two API/SECRET combinations the
Relay will rotate between. Each (sub)account can hace as many as your
exchange will allow.

## Reboot startup

For Jackrabbit Relay to auto start after a reboot, the following line
neesa to be added to your crontab. BE SURE TO CHANGE THE 12345 TO THE
PORT YOU WANT.

    @reboot ( /home/JackrabbitRelay/Base/RelayLauncher 12345 & ) > /dev/null 2>&1

## Manual startup

Use the following command. Be sure to replace the 12345 with the proper port.

    ( /home/JackrabbitRelay/Base/RelayLauncher 12345 & ) > /dev/null 2>&1

## The Payload

Here are examples of the payload sent from TradingView of similar webhook
based application.

This example purchased $30 of AAVE on the FTX US exchange.

    { "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD","USD":"30" }

This example purchases the minimum amount of AAVE in USD

    { "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD" }

This example sells $7 of AAVE

    { "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Sell","Asset":"AAVE/USD","USD":"7" }

This example sells th exchange minimum of AAVE

    { "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Sell","Asset":"AAVE/USD" }

This example close out or sells all of AAVE

    { "Exchange":"ftxus","Market":"Spot","Account":"MAIN","Action":"Close","Asset":"AAVE/USD" }

This example purchases AAVE using its base value, in this case, 1 AAVE

    { "Exchange":"kraken","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD","Base":"1" }

This example purchases BCH by the value of BTC

    { "Exchange":"ftx","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"BCH/BTC","Quote":"1" }

Discriptionn of the payload

    Exchange

        This is one of the supported exchanges.

    Market

        This is the market you are trading. 

        Spot            Working 
        Prepetuals      Maybe working FTX ONLY
        Margin          In progress
        Future          In progress

    Account

        All main accounts must be called MAIN. Subaccounts can be used
        and must be exactly as listed on the exchange.

    Action

        Buy             Make a purchase
        Sell            Sell a portion. If amount is more then balance, position will be closed
        Close           Sell all of the asset

    Asset

        The asset you are trading. Must be exactly as the exchange lists it

    USD/Base/Quote

        Choose only one to set the amount to be purchased/sold

        USD will only work if the asset has a coresponsing USD pair to do
        a proper base conversion on.

        Base is the asset itself value, ie BTC, ADA, AAVE, so one.
            A base of 1 for BTC is to purchase 1 BTC.

        Quote is the value of the asset in its quote currency. For
        example, if you want to purchase BCH/BTC using the price value of
        BTC, then you specify your amout in the quote currency.

## Logging

Below are examples of the log files.

This is the Jackrabbit Relay server log file:

    2021-09-22 22:34:53.059783 62.151.179.169   ('POST / HTTP/1.1', '200', '-')

Here is an example of the Place Order log for the FTX US exchange:

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

## Donations

If you would like to help support this project financially, please use
any of the below addresses. Anything donated goes to the costs of
sustaining Jackrabbit Relay. Thank you.

    BCH     bitcoincash:qzw5h5ccfz6v7zzh0vf5pl0eqp3zjmp5us07l72nvv
    BTC     3JUbL3Vsj61VBAmyHtQhyiFJcizEfxAvzV
    ETH     0x3c6C06150B2f24b3179a50b618aD3c0f58CF74FD
    LINK    0xd8Fd4fA3b489861ad6Eb95a0617B4DA7c78123F8
    LTC     MHj8nQcRdJWVVNeHUemSQgzBw3cPrZEtRU
    USDT    0xd8Fd4fA3b489861ad6Eb95a0617B4DA7c78123F8
