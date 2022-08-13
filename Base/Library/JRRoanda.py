#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
import os
import json
import pathlib
from datetime import datetime

import oandapyV20
import oandapyV20.endpoints
import oandapyV20.endpoints.accounts as v20Accounts
import oandapyV20.endpoints.instruments as v20Instruments
import oandapyV20.endpoints.pricing as v20Pricing
import oandapyV20.endpoints.orders as v20Orders
import oandapyV20.endpoints.positions as v20Positions

import JRRconfig
import JRRlog
import JRRledger
import JRRsupport

# Register the exchange

def ExchangeLogin(exchangeName,Config,Active,Notify=True,Sandbox=False):
    try:
        exchange=oandapyV20.API(access_token=Active['API'])
    except Exception as e:
        Active['JRLog'].Error("Login",JRRsupport.StopHTMLtags(str(e)))

    return(exchange)

def GetMarkets(exchange,Active):
    try:
        markets={}
        res=v20Accounts.AccountInstruments(accountID=Active['AccountID'])
        results=exchange.request(res)
        for cur in results['instruments']:
            asset=cur['name'].upper().replace('_','')
            markets[asset]=cur
        return markets
    except Exception as e:
        Active['JRLog'].Error("GetMarkets",JRRsupport.StopHTMLtags(str(e)))

    return None

def GetBalances(exchange,Active):
    try:
        res=v20Accounts.AccountSummary(accountID=Active['AccountID'])
        results=exchange.request(res)
        return results['account']
    except Exception as e:
        Active['JRLog'].Error("GetBalances",JRRsupport.StopHTMLtags(str(e)))

    return None

def GetPositions(exchange,Active):
    try:
        res=v20Positions.OpenPositions(accountID=Active['AccountID'])
        results=exchange.request(res)
        return results['positions']
    except Exception as e:
        Active['JRLog'].Error("GetPositions",JRRsupport.StopHTMLtags(str(e)))

    return None

#   Tme Epoch MS   Open      High      Low       Close     Volume
# [[1660416600000, 0.554891, 0.554891, 0.554516, 0.554573, 10010.83555758]]

# {'instrument': 'EUR_USD', 'granularity': 'M5', 
#'candles': [{'complete':True, 'volume': 297, 'time': '2022-08-12T20:55:00.000000000Z', 
# 'mid':{'o': '1.02566', 'h': '1.02616', 'l': '1.02558', 'c': '1.02590'}}]}

def GetOHLCV(exchange,Active,**kwargs):
    symbol=kwargs.get('symbol').replace('/','_')
    timeframe=kwargs.get('timeframe')
    limit=str(kwargs.get('limit'))
    params={"granularity":timeframe.upper(), "count":limit }
    candles=[]

    try:
        res=v20Instruments.InstrumentsCandles(instrument=symbol,params=params)
        results=exchange.request(res)
        for cur in results['candles']:
            candle=[]
            candle.append(int(datetime.strptime(cur['time'],'%Y-%m-%dT%H:%M:%S.000000000Z').timestamp())*1000)
            candle.append(float(cur['mid']['o']))
            candle.append(float(cur['mid']['h']))
            candle.append(float(cur['mid']['l']))
            candle.append(float(cur['mid']['c']))
            candle.append(float(cur['volume']))
            candles.append(candle)
        return candles
    except Exception as e:
        Active['JRLog'].Error("GetOHLCV",JRRsupport.StopHTMLtags(str(e)))

    return None


"""
# Fetch the position of a given of a pair
# CCXT only

def GetPosition(Positions,Asset):
    for pos in Positions:
        if pos['symbol']==Asset:
            return pos
    return None

def GetContracts(Positions,Asset):
    position=GetPosition(Positions,Asset)
    if position is None:
        bal=0
    else:
        bal=position['contracts']

    return bal

# Fetch the balance of a given BASE of a pair

def GetBalance(balances,base):
    if base in balances['total']:
        bal=float(balances['total'][base])
    else:
        # This is an absolute horrible way to handle this, but unfortunately the only way.
        # Many exchanges don't report a balance at all if an asset hasn't been traded in
        # a given timeframe (usually fee based tier resets designate the cycle).
        bal=0

    return bal

# Fetch the market list

def GetMarkets(exchange,pair,RetryLimit,Notify=True):
    markets=LoadMarkets(exchange,RetryLimit,Notify)

    if pair[0]=='.' or pair.find(".d")>-1:
        JRRlog.ErrorLog('Get Markets',pair+" is not tradable on this exchange")

    if pair not in exchange.markets:
        JRRlog.ErrorLog('Get Markets',pair+" is not traded on this exchange")

    if 'active' in exchange.markets[pair]:
        if exchange.markets[pair]['active']==False:
            JRRlog.ErrorLog('Get Markets',pair+" is not active on this exchange")

    return markets

def LoadMarkets(exchange,RetryLimit,Notify=True):
    markets=ccxtAPI("load_markets",exchange,RetryLimit)

    if Notify:
        JRRlog.WriteLog("Markets loaded")

    return markets

# This function is used to access ALL ccxt modules with a retry
# functionality built in.
#
# examples:
# markets=ccxtAPI("load_markets",exchange,RetryLimit)
# balance=ccxtAPI("fetch_balance",exchange,RetryLimit)

def ccxtAPI(function,exchange,Active,**args):
    exchangeName=exchange.name.lower()
    ohlcv=[]
    retry429=0
    retry=0

    # Sanity check
    if 'Retry' in Active:
        RetryLimit=int(Active['Retry'])
    else:
        RetryLimit=3

    # Convert function to a CCXT module
    try:
        callCCXT=getattr(exchange,function)
    except Exception as e:
        x=str(e)
        # Kucoin don not support this, but don't break program
        if function=='fetch_positions' and exchangeName=='kucoin':
            return None
        Active['JRLog'].Error(function,JRRsupport.StopHTMLtags(x))

    # For kucoin only, 429000 errors are a mess. Not the best way to
    # manage them, but the onle way I know of currently to prevent losses.

    # Save the only rate limit and remap it.

    if exchangeName=='kucoin':
        rleSave=exchange.enableRateLimit
        rlvSave=exchange.rateLimit
        exchange.enableRateLimit=True
        exchange.rateLimit=372+JRRsupport.ElasticDelay()

    done=False
    while not done:
        try:
            #ohlcv=exchange.fetch_ohlcv(symbol=pair,timeframe=tf,limit=1)
            result=callCCXT(**args)
        except Exception as e:
            if exchangeName=='kucoin':
                x=str(e)
                if x.find('429000')>-1:
                    retry429+=1
            if retry>=RetryLimit:
                JRRlog.ErrorLog(function,JRRsupport.StopHTMLtags(e))
            else:
                if not KuCoinSuppress429:
                    JRRlog.WriteLog(function+' Retrying ('+str(retry+1)+'), '+JRRsupport.StopHTMLtags(str(e)))
        else:
            done=True

        if exchangeName=='kucoin':
            if retry429>=(RetryLimit*7):
                retry429=0
                retry+=1
        else:
            retry+=1

    if exchangeName=='kucoin':
        exchange.enableRateLimit=rleSave
        exchange.rateLimit=rlvSave

    return result
"""
