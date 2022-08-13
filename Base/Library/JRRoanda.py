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
    markets={}
    res=v20Accounts.AccountInstruments(accountID=Active['AccountID'])
    results=oandaAPI("GetMarkets",exchange,Active,request=res)
    for cur in results['instruments']:
        asset=cur['name'].upper().replace('_','')
        markets[asset]=cur
    return markets

def GetBalances(exchange,Active):
    res=v20Accounts.AccountSummary(accountID=Active['AccountID'])
    results=oandaAPI("GetBalances",exchange,Active,request=res)
    return results['account']

def GetPositions(exchange,Active):
    res=v20Positions.OpenPositions(accountID=Active['AccountID'])
    results=oandaAPI("GetPositions",exchange,Active,request=res)
    return results['positions']

def GetOHLCV(exchange,Active,**kwargs):
    symbol=kwargs.get('symbol').replace('/','_')
    timeframe=kwargs.get('timeframe')
    limit=str(kwargs.get('limit'))
    params={"granularity":timeframe.upper(), "count":limit }
    candles=[]

    res=v20Instruments.InstrumentsCandles(instrument=symbol,params=params)
    results=oandaAPI("GetOHLCV",exchange,Active,request=res)
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

def GetTicker(exchange,Active,**kwargs):
    symbol=kwargs.get('symbol').replace('/','_')
    params={"instruments":symbol }

    res=v20Pricing.PricingInfo(accountID=Active['AccountID'],params=params)
    results=oandaAPI("GetTicker",exchange,Active,request=res)
    return results

def oandaAPI(function,exchange,Active,**kwargs):
    req=kwargs.get('request')
    retry=0

    # Sanity check
    if 'Retry' in Active:
        RetryLimit=int(Active['Retry'])
    else:
        RetryLimit=3

    done=False
    while not done:
        try:
            result=exchange.request(req)
        except Exception as e:
            if retry<RetryLimit:
                Active['JRLog'].Error(function,JRRsupport.StopHTMLtags(str(e)))
            else:
                Active['JRLog'].Write(function+' Retrying ('+str(retry+1)+'), '+JRRsupport.StopHTMLtags(str(e)))
        else:
            done=True
        retry+=1

    return result

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
