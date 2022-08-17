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
        asset=cur['name'].upper().replace('_','/')
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

# Shorts are negative

def GetPosition(positions,Asset):
    position=0.0
    if positions!=None:
        for pos in positions:
            asset=pos['instrument'].replace('_','/')
            if Asset.upper()==asset:
                if 'averagePrice' in pos['long']:
                    position=float(pos['long']['averagePrice'])
                else:
                    position=-(float(pos['short']['averagePrice']))
            return position
    return None

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

