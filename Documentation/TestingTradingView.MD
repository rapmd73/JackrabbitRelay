# Testing TradingView connection

This file details the steps and configuration neccessary to test the
connection between TradingView and Jackrabbot Relay.

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

## Testing method

Jackrabbit Relay provides both a TradingView script and place order
program to facilitate testing.

In the Extras folder is the script that can be copied/pasted into
TradingView's pine editor, ot you can use this link,

[Pine Script Signal Generator](https://www.tradingview.com/script/xBRGQTy0-Signal-generator/)

## Setup

Use the following or something similar for your TradingView alert message,

```json
{ "Exchange":"tester","Market":"Spot","Account":"MAIN","Action":"Buy","Asset":"AAVE/USD" }
```

the **tester** exchange allow the tester place order program to be used.
It simple logs the message in the Logs folder.

## Donations

Information regarding donations and supporting Jackrabbit Relay can be
found [here](./Documentation/Donations.MD).

