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
import json
import ccxt

import JRRconfig
import JRRlog

# Register the exchange

def ExchangeLogin(exchangeName,Active):
    if exchangeName in ccxt.exchanges:
        try:
            exchange=getattr(ccxt,exchangeName)( \
                { 'apiKey': Active['API'],'secret': Active['SECRET'] })
        except Exception as e:
            JRRlog.ErrorLog("Connecting to exchange",e)
    else:
        if exchangeName=="ftxus":
            try:
                exchange=ccxt.ftx({ 'hostname': 'ftx.us', \
                    'apiKey': Active['API'],'secret': Active['SECRET'] })
            except Exception as e:
                JRRlog.ErrorLog("Connecting to exchange",e)
        else:
            JRRlog.ErrorLog(exchangeName,"Exchange not supported")

    SetExchangeAPI(exchangeName,exchange,Active,notify=True)

    return(exchange)

def SetExchangeAPI(exchangeName,exchange,Active,notify=False):
    if "createMarketBuyOrderRequiresPrice" in exchange.options:
        JRRlog.ErrorLog(exchangeName,"Exchange not supported")

    # Set FTX and FTX US subaccount. Not sure if I need to reset API/secret yet.

    if exchangeName=="ftx" and Active['Account']!='MAIN':
        exchange.headers['FTX-SUBACCOUNT']=Active['Account']
        exchange.apiKey=Active['API']
        exchange.secret=Active['SECRET']
    else:
        if exchangeName=="ftxus" and Active['Account']!='MAIN':
            exchange.headers['FTXUS-SUBACCOUNT']=Active['Account']
            exchange.apiKey=Active['API']
            exchange.secret=Active['SECRET']
        else:
            if exchangeName=="kucoin":
                if 'Passphrase' in Active:
                    exchange.password=Active['Passphrase']
                else:
                    JRRlog.ErrorLog("Connecting to exchange","Kucoin requires a passphrase as well")

    exchange.verbose=False

    if "RateLimit" in Active:
        exchange.enableRateLimit=True
        exchange.rateLimit=int(Active['RateLimit'])
        if notify:
            JRRlog.WriteLog("|- Rate limit set to "+str(Active['RateLimit'])+' ms')
    else:
        exchange.enableRateLimit=False

    return(exchange)

def FindMatchingPair(base,markets):
    for quote in JRRconfig.StableCoinUSD:
        pair=base+'/'+quote
        if pair in markets:
            return pair

    return None

# Pull the information about the asset minimums from the exchangew.
# Amount is the minimum amount in the ASSET, it TRX/BTC, amount is always BASE value
# Cost in USD/Stablecoins
# Price in USD/Stablecoins

def GetAssetMinimum(exchange,pair,diagnostics,RetryLimit):
    ohlcv,ticker=FetchRetry(exchange,pair,"1m",RetryLimit)

    close=ohlcv[4]

    minimum1=exchange.markets[pair]['limits']['amount']['min']
    minimum2=exchange.markets[pair]['limits']['cost']['min']
    if minimum2==None:
        minimum2=0
    minimum3=exchange.markets[pair]['limits']['price']['min']
    if minimum3==None:
        minimum3=0

    minimum=max(minimum1,minimum2/close,minimum3/close)
    mincost=max(minimum1*close,minimum2,minimum3)

    if diagnostics:
        JRRlog.WriteLog(f"| |- Close: {close:.6f}")
        JRRlog.WriteLog(f"| |- Minimum Amount: {minimum1:.6f}, {minimum1*close:.6f}")
        JRRlog.WriteLog(f"| |- Minimum Cost:   {minimum2:.6f}, {minimum2/close:.6f}")
        JRRlog.WriteLog(f"| |- Minimum Price:  {minimum3:.6f}, {minimum3/close:.6f}")

    return(minimum, mincost)

# Get asset information

def GetMinimum(exchange,pair,forceQuote,diagnostics,RetryLimit):
    base=exchange.markets[pair]['base']
    quote=exchange.markets[pair]['quote']

# Get BASE minimum. This is all that is needed if quote is USD/Stablecoins

    if diagnostics:
        JRRlog.WriteLog("Minimum asset analysis")
        JRRlog.WriteLog("|- Base: "+base)
    minimum,mincost=GetAssetMinimum(exchange,pair,diagnostics,RetryLimit)
    if diagnostics:
        JRRlog.WriteLog("| |- Minimum: "+f"{minimum:.6f}")
        JRRlog.WriteLog("| |- Min Cost: "+f"{mincost:.6f}")

# If quote is NOT USD/Stablecoin. NOTE: This is an API penality for the
# overhead of pulling quote currency. Quote currenct OVERRIDES base ALWAYS.

    if diagnostics:
        JRRlog.WriteLog("|- Quote: "+quote)

    if quote not in JRRconfig.StableCoinUSD or forceQuote:
        bpair=FindMatchingPair(quote,exchange.markets)
        if bpair!=None:
            minimum,mincost=GetAssetMinimum(exchange,bpair,diagnostics,RetryLimit)

            if diagnostics:
                JRRlog.WriteLog("| |- Minimum: "+f"{minimum:.6f}")
                JRRlog.WriteLog("| |- Min Cost: "+f"{mincost:.6f}")

    return minimum,mincost

# Place the order

def PlaceOrder(exchange, pair, market, action, amount, close, RetryLimit, ReduceOnly):
    params = { 'reduce_only': ReduceOnly, }
    order=None

    retry=0
    while retry<RetryLimit:
        try:
            if ReduceOnly==True:
                order=exchange.create_order(pair, market, action, amount, close, params)
            else:
                order=exchange.create_order(pair, market, action, amount, close)
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Placing Order",e)
            else:
                JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
        except Exception as e:
            JRRlog.ErrorLog("Placing Order",e)
        else:
            JRRlog.WriteLog("|- ID: "+order['id'])
            return order
        finally:
            retry+=1

    if retry>=RetryLimit:
        JRRlog.ErrorLog("Placing Order","order unsuccessful")
    return order

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
            JRRlog.ErrorLog("Fetching OHLCV",e)
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
            JRRlog.ErrorLog("Fetching Ticker",e)
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
    bal=-1
    retry=0
    while retry<RetryLimit:
        try:
            balance=exchange.fetch_balance()
            if base in balance['total']:
                bal=float(balance['total'][base])
            else:
                if 'USD' in balance['total']:
                    bal=float(balance['total']['USD'])
                else:
                    bal=0
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetching Balance",e)
            else:
                JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
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
                JRRlog.ErrorLog("Fetching Position",e)
            else:
                JRRlog.WriteLog('Retrying ('+str(retry+1)+'), '+str(e))
        except Exception as e:
            JRRlog.ErrorLog("Fetching Position",e)
        else:
            break
        retry+=1

    return position

# Fetch the market list

def GetMarkets(exchange,pair,RetryLimit):
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
            JRRlog.ErrorLog("Fetching Markets",e)
        else:
            break
        retry+=1

    JRRlog.WriteLog("Markets loaded")

    if pair[0]=='.' or pair.find(".d")>-1:
        JRRlog.ErrorLog('Get Markets',pair+" is not tradable on this exchange")

    if pair not in exchange.markets:
        JRRlog.ErrorLog('Get Markets',pair+" is not traded on this exchange")

    if 'active' in exchange.markets[pair]:
        if exchange.markets[pair]['active']==False:
            JRRlog.ErrorLog('Get Markets',pair+" is not active on this exchange")

    return markets

