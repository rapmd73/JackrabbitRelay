#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
import os
import ccxt

import JRRlog
import JRRsupport

###
### Main code base. Place order on exchange
###

if len(sys.argv) > 2:
    exchangeName=sys.argv[1].lower()
    account=sys.argv[2]
else:
    print("An exchange and a (sub)account must be provided.")
    sys.exit(1)

# Load the API/Secret information

keys=JRRsupport.ReadConfig(exchangeName,account)

CurrentKey=(os.getpid()%len(keys))
Active=keys[CurrentKey]

if exchangeName in ccxt.exchanges:
    try:
        exchange=getattr(ccxt,exchangeName)( \
            { 'apiKey': Active['API'],'secret': Active['SECRET'] })
    except Exception as e:
        print("Connecting to exchange",e)
        sys.exit(1)
else:
    if exchangeName=="ftxus":
        try:
            exchange=ccxt.ftx({ 'hostname': 'ftx.us', \
                'apiKey': Active['API'],'secret': Active['SECRET'] })
        except Exception as e:
            ptint("Connecting to exchange",e)
            sys.exit(1)
    else:
        print(exchangeName,"Exchange not supported")
        sys.exit(1)

# Special settings

if "createMarketBuyOrderRequiresPrice" in exchange.options:
    JRRlog.ErrorLog(exchangeName,"Exchange not supported")

# Set FTX and FTX US subaccount. Not sure if I need to reset API/secret yet.
exchange.apiKey=Active['API']
exchange.secret=Active['SECRET']

if exchangeName=="ftx" and Active['Account']!='MAIN':
    exchange.headers['FTX-SUBACCOUNT']=Active['Account']
else:
    if exchangeName=="ftxus" and Active['Account']!='MAIN':
        exchange.headers['FTXUS-SUBACCOUNT']=Active['Account']
    else:
        if exchangeName=="kucoin":
            if 'Passphrase' in Active:
                exchange.password=Active['Passphrase']
            else:
                print("Connecting to exchange","Kucoin requires a passphrase as well")
                sys.exit(1)

if "RateLimit" in Active:
    exchange.enableRateLimit=True
    exchange.rateLimit=int(Active['RateLimit'])
else:
    exchange.enableRateLimit=False

if "Retry" in Active:
    RetryLimit=int(Active['Retry'])
else:
    RetryLimit=1000

exchange.verbose=False

done=False
while not done:
    try:
        markets=exchange.load_markets()
    except:
        pass
    else:
        done=True

balance = exchange.fetch_balance()

coinList=balance['total']
for coin in coinList:
    bal=float(balance['total'][coin])

    if bal>0.0:
        print(f"{coin:12} {bal:12.8f}")

if exchange.has['fetchPositions']:
    try:
        positions = exchange.fetch_positions()
        for pos in positions:
            bal=float(pos['contracts'])
            if bal>0.0:
                print(f"{pos['symbol']:12} {bal:12.8f} {pos['side']:5}")
    except:
        pass