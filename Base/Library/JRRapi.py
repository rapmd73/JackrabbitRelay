#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
import os
import time
from datetime import datetime
import json
import ccxt

import JRRconfig
import JRRlog

def FindMatchingPair(base,markets):
    for quote in JRRconfig.StableCoinUSD:
        pair=base+'/'+quote
        if pair in markets:
            return pair

    return None

# Place the order

def PlaceOrder(exchange, pair, market, action, amount, close, RetryLimit, ReduceOnly):
    params = { 'reduce_only': ReduceOnly, }

    retry=0
    while retry<RetryLimit:
        try:
            order=exchange.create_order(pair, market, action, amount, close, params)
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Placing Order",e)
            else:
                JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
        except Exception as e:
            JRRlog.ErrorLog("Placing Order",e)
        else:
            JRRlog.WriteLog("|- ID: "+order['id'])
            break
        retry+=1

# If fetch_ohlcv fails, revert to fetch_ticker and parse it manually
# if open is None, use low.

def FetchRetry(exchange,pair,tf,RetryLimit):
    ohlc=[]
    retry=0
    while retry<RetryLimit:
        try:
            ohlcv=exchange.fetch_ohlcv(symbol=pair,timeframe=tf,limit=1)
            if ohlcv==[]:
                ohlcv=None
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
                if retry>=RetryLimit:
                    JRRlog.ErrorLog("Fetching OHLCV",e)
                else:
                    JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
        except Exception as e:
            JRRlog.ErrorLog("Placing Order",e)
        else:
            break
        retry+=1

    retry=0
    while retry<RetryLimit:
        try:
            ticker=exchange.fetch_ticker(pair)
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetching Ticker",e)
            else:
                JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
        except Exception as e:
            JRRlog.ErrorLog("Placing Order",e)
        else:
            break
        retry+=1

    if ohlcv==None:
        ohlc.append(ticker['timestamp'])
        if ticker['open']==None:
            ohlc.append(ticker['low'])
        else:
            ohlc.append(ticker['open'])
        ohlc.append(ticker['high'])
        ohlc.append(ticker['low'])
        ohlc.append(ticker['close'])
    else:
        for i in range(5):
            ohlc.append(ohlcv[0][i])

    return ohlc, ticker

# Fetch the balance of a given BASE of a pair

def GetBalance(exchange,base,RetryLimit):
    retry=0
    while retry<RetryLimit:
        try:
            balance=exchange.fetch_balance()
            if base in balance['total']:
                bal=float(balance['total'][base])
            else:
                bal=float(balance['total']['USD'])
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetching Balance",e)
            else:
                JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
        except Exception as e:
            JRRlog.ErrorLog("Placing Order",e)
        else:
            break
        retry+=1

    return bal

# Fetch the position of a given of a pair

def GetPosition(exchange,pair,RetryLimit):
    retry=0
    while retry<RetryLimit:
        try:
            positions = exchange.fetch_positions()
            positions_by_symbol = exchange.index_by(positions, 'symbol')
            position = exchange.safe_value(positions_by_symbol, pair)
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetching Balance",e)
            else:
                JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
        except Exception as e:
            JRRlog.ErrorLog("Fetching Markets",e)
        else:
            break
        retry+=1

    return position

# Fetch the market list

def GetMarkets(exchange,RetryLimit):
    retry=0
    while retry<RetryLimit:
        try:
            markets=exchange.load_markets()
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetching Markets",e)
            else:
                JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
        except Exception as e:
            JRRlog.ErrorLog("Placing Order",e)
        else:
            break
        retry+=1

    return markets

