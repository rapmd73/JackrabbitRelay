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

## Extras

This folder has some very interesting and useful programs that provide a
wealth of information.

## Videos

[Relay Extras](https://youtu.be/qXykEckzEgs)

## ListMarkets
```bash
ListMarkets <exchange> <ratelimit>
```

**Exchange** is the exchange you want to line, ie ftx

**Rate limit** is a number of 1 or more. This lets you find a good rate limit value your exchange will accept. The program will crash with a rate limit error if your value is too low.

This program lists the markets of a given exchange. Here is an example from FTX:

    LINK/BTC             spot              0.100000           0.000050
    LINK/USD             spot              0.100000           3.094800
    LINK/USDT            spot              0.100000           3.094700

The first column is the pair. The second is the market type. The third is the minimum the exchange will accept. The above example is for the LINK market, so the minimum is expressed in LINK. The forth colum is what the amount would be if expressed is USD or a similar stablecoin.

## AnalyzeAsset

```bash
AnalyzeAsset <exchange> <account or NONE> <asset>
```

This program allows for the examination of a single asset.

```log
2021-11-18 23:01:56.891213 3077942 AnalyzeAsset 0.0.0.0.230
2021-11-18 23:01:56.891631 3077942 |- Exchange: kucoin
2021-11-18 23:01:56.891798 3077942 |- Account: NONE
2021-11-18 23:01:56.892012 3077942 |- Asset: BTC/USDT
2021-11-18 23:01:56.892174 3077942 NO API/Secret loaded, using public API
2021-11-18 23:01:57.852855 3077942 Markets loaded
2021-11-18 23:01:57.853307 3077942 Minimum asset analysis
2021-11-18 23:01:57.853432 3077942 |- Base: BTC
2021-11-18 23:01:58.440601 3077942 | |- Close: 56534.600000
2021-11-18 23:01:58.440977 3077942 | |- Minimum Amount: 0.000010, 0.565346
2021-11-18 23:01:58.441118 3077942 | |- Minimum Cost:   0.010000, 0.000000
2021-11-18 23:01:58.441288 3077942 | |- Minimum Price:  0.100000, 0.000002
2021-11-18 23:01:58.441461 3077942 | |- Minimum: 0.000010
2021-11-18 23:01:58.441684 3077942 | |- Min Cost: 0.565346
2021-11-18 23:01:58.441844 3077942 |- Quote: USDT
2021-11-18 23:01:58.442042 3077942 Exchange required minimum:  0.000010
2021-11-18 23:01:58.442135 3077942 Exchange required min cost: 0.565346
2021-11-18 23:01:58.442291 3077942 Processing Completed: 01.551824 seconds
```

The information provided lists the exact minimum position size (lot) for a given asset.

## RelayPassThru

This program is a bridge between Apache and Jackrabbit Relay. You'll need to add your webhook and copy it into your cgi-bin folder.

## Tester.PineScript.txt

This is the pine script program from the above video on testing Jackrabbit Relay's server.

## Donations

If you would like to help support this project financially, please use
any of the below addresses. Anything donated goes to the costs of
sustaining Jackrabbit Relay. Thank you.

You can subscribe to the Jackrabbit Relay tier for recurring monthly
support:

    https://www.patreon.com/RD3277

If you prefer crypto or just a one time donation, please use any of the
below:
| | |
| :--- | :--- |
| BCH | bitcoincash:qzw5h5ccfz6v7zzh0vf5pl0eqp3zjmp5us07l72nvv|
| BTC | 3JUbL3Vsj61VBAmyHtQhyiFJcizEfxAvzV |
| ETH | 0x3c6C06150B2f24b3179a50b618aD3c0f58CF74FD |
| LINK | 0xd8Fd4fA3b489861ad6Eb95a0617B4DA7c78123F8 |
| LTC | MHj8nQcRdJWVVNeHUemSQgzBw3cPrZEtRU |
| USDT | 0xd8Fd4fA3b489861ad6Eb95a0617B4DA7c78123F8 |
