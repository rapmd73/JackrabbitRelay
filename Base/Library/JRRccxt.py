#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import ccxt
import json
import pathlib
from datetime import datetime

import JRRconfig
import JRRlog
import JRRledger
import JRRsupport

KuCoinSuppress429=True

def FindMatchingPair(base,markets):
    for quote in JRRconfig.StableCoinUSD:
        pair=base+'/'+quote
        if pair in markets:
            return pair

    return None

# Pull the information about the asset minimums from the exchange.
# Amount is the minimum amount in the ASSET, it TRX/BTC, amount is always BASE value
# Cost in USD/Stablecoins
# Price in USD/Stablecoins

def LoadMinimum(exchangeName,pair):
    minlist={}
    amount=0
    fn=JRRconfig.DataDirectory+'/'+exchangeName+'.minimum'
    if os.path.exists(fn):
        try:
            raw=pathlib.Path(fn).read_text()
        except:
            Active['JRLog'].Error("Minimum List",f"Can't read minimum list for {exchangeName}")

        minlist=json.loads(raw)
        if pair in minlist:
            amount=minlist[pair]

    return amount

def UpdateMinimum(exchangeName,pair,amount):
    minlist={}
    fn=JRRconfig.DataDirectory+'/'+exchangeName+'.minimum'
    if os.path.exists(fn):
        try:
            raw=pathlib.Path(fn).read_text()
        except:
            Active['JRLog'].Error("Minimum List",f"Can't read minimum list for {exchangeName}")

        minlist=json.loads(raw)

    minlist[pair]=amount
    fh=open(fn,'w')
    fh.write(json.dumps(minlist))
    fh.close()

def GetAssetMinimum(exchange,pair,diagnostics,RetryLimit):
    exchangeName=exchange.name.lower().replace(' ','')
    ohlcv,ticker=FetchRetry(exchange,pair,"1m",RetryLimit)

    close=ohlcv[4]
    if close==None:
        if ticker['close']==None:
            close=float(ticker['ask'])
        else:
            close=float(ticker['close'])

    minimum=LoadMinimum(exchangeName,pair)
    if minimum>0.0:
        mincost=round(minimum*close,8)

        if diagnostics:
            Active['JRLog'].Write(f"| |- Close: {close:.8f}")
            Active['JRLog'].Write(f"| |- (Table)Minimum Amount: {minimum:.8f}")
            Active['JRLog'].Write(f"| |- (Table)Minimum Cost:   {mincost:.8f}")
    else:
        minimum1=exchange.markets[pair]['limits']['amount']['min']
        minimum2=exchange.markets[pair]['limits']['cost']['min']
        minimum3=exchange.markets[pair]['limits']['price']['min']

        if minimum1==None or minimum1==0:
            if 'contractSize' in exchange.markets[pair]:
                minimum1=exchange.markets[pair]['contractSize']
                m1=float(minimum1)*close
            else:
                minimum1=0
                m1=0.0
        else:
            m1=float(minimum1)*close
        if minimum2==None or minimum2==0:
            minimum2=0
            m2=0.0
        else:
            m2=float(minimum2)/close
        if minimum3==None or minimum3==0:
            minimum3=0
            m3=0.0
        else:
            m3=float(minimum3)/close

        minimum=max(float(minimum1),m2,m3)
        mincost=max(m1,float(minimum2),float(minimum3))

        if minimum==0.0 or mincost==0.0:
            if exchange.precisionMode==ccxt.TICK_SIZE:
                minimum=float(exchange.markets[pair]['precision']['amount'])
                mincost=minimum*close
            else:
                z='000000000'
                factor=max(exchange.precisionMode,ccxt.TICK_SIZE)
                minimum=float('0.'+str(z[:factor-1])+'1')
                mincost=minimum*close

        if diagnostics:
            Active['JRLog'].Write(f"| |- Close: {close:.8f}")
            Active['JRLog'].Write(f"| |- Minimum Amount: {minimum1:.8f}, {m1:.8f}")
            Active['JRLog'].Write(f"| |- Minimum Cost:   {minimum2:.8f}, {m2:.8f}")
            Active['JRLog'].Write(f"| |- Minimum Price:  {minimum3:.8f}, {m3:.8f}")

    return(minimum, mincost)

# Get asset information

def GetMinimum(exchange,pair,forceQuote,diagnostics,RetryLimit):
    base=exchange.markets[pair]['base']
    quote=exchange.markets[pair]['quote']

    minimum,mincost=GetAssetMinimum(exchange,pair,diagnostics,RetryLimit)

# Get BASE minimum. This is all that is needed if quote is USD/Stablecoins

    if diagnostics:
        Active['JRLog'].Write("Minimum asset analysis")
        Active['JRLog'].Write("|- Base: "+base)
        Active['JRLog'].Write("| |- Minimum: "+f"{minimum:.8f}")
        Active['JRLog'].Write("| |- Min Cost: "+f"{mincost:.8f}")
        # If quote is NOT USD/Stablecoin. NOTE: This is an API penalty
        # for the overhead of pulling quote currency. Quote currency
        # OVERRIDES base ALWAYS.
        Active['JRLog'].Write("|- Quote: "+quote)

    if quote not in JRRconfig.StableCoinUSD or forceQuote:
        bpair=FindMatchingPair(quote,exchange.markets)
        if bpair!=None:
            minimum,mincost=GetAssetMinimum(exchange,bpair,diagnostics,RetryLimit)

            if diagnostics:
                Active['JRLog'].Write("| |- Minimum: "+f"{minimum:.8f}")
                Active['JRLog'].Write("| |- Min Cost: "+f"{mincost:.8f}")

    if minimum==0.0:
        Active['JRLog'].Error("Asset Analysis","minimum position size returned as 0")
    if mincost==0.0:
        Active['JRLog'].Error("Asset Analysis","minimum cost per position returned as 0")

    return minimum,mincost

# Place the order
# Market - LimitTaker - IOC true, limit orders with taker fee, psuedo market orders
#          LimitMaker - PostOnly true, full limit orders with maker fee

def FetchExchangeOrderHistory(exchange, oi, pair, RetryLimit):
    # Give the exchange time to settle
    JRRsupport.ElasticSleep(1)

    retry=0
    done=False
    fo=None
    while not done:
        try:
            fo=ccxtAPI("fetchOrder",exchange,RetryLimit,oi,symbol=pair)
        except Exception as e:
            if retry>=RetryLimit:
                done=True
                fo=None
        else:
            if fo['status']=='closed':
                return True
            if retry>=RetryLimit:
                done=True
        retry+=1
        if not done and retry<RetryLimit:
            JRRsupport.ElasticSleep(10)

    return False

def WaitLimitOrder(exchange,oi,pair,RetryLimit):
    Active['JRLog'].Write("|- Waiting for limit order")
    ohist=FetchExchangeOrderHistory(exchange,oi,pair,RetryLimit)

    # cancel the order
    if ohist==False:
        try:
            ct=ccxtAPI("cancel_order",exchange,RetryLimit,oi,pair)
        except:
            pass
    else:
        return True

def FetchCandles_interval(exchange,pair,tf,start_date_time,end_date_time,RetryLimit):
    from_timestamp = exchange.parse8601(start_date_time)
    to_timestamp = exchange.parse8601(end_date_time)

    # For kucoin only, 429000 errors are a mess. Not the best way to
    # manage them, but the onle way I know of currently to prevent losses.
    # Save the only rate limit and remap it.

    if exchangeName=='kucoin':
        rleSave=exchange.enableRateLimit
        rlvSave=exchange.rateLimit
        exchange.enableRateLimit=True
        exchange.rateLimit=372+JRRsupport.ElasticDelay()

    done=False
    while from_timestamp < to_timestamp:
        try:
            ohlcvs=ccxtAPI("fetch_ohlcv",exchange,RetryLimit,pair,tf,from_timestamp)
            first = ohlcvs[0][0]
            last = ohlcvs[-1][0]
            if tf == "1m":
                from_timestamp += len(ohlcvs) * minute 
            if tf == "5m":
                from_timestamp += len(ohlcvs) * 5 * minute 
            if tf == "15m":
                from_timestamp += len(ohlcvs) * 15 * minute 
            if tf == "1h":
                from_timestamp += len(ohlcvs) * hour
            if tf == "1d":
                from_timestamp += len(ohlcvs) * day
            data += ohlcvs
        except Exception as e:
            if exchangeName=='kucoin':
                x=str(e)
                if x.find('429000')>-1:
                    retry429+=1
            if retry>=RetryLimit:
                Active['JRLog'].Error("Fetching OHLCV",e)
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

    return data

###
### Rewritten for single retry loop and JRR class
###

# Register the exchange

def ExchangeLogin(exchangeName,Config,Active,Notify=True,Sandbox=False):
    if exchangeName in ccxt.exchanges:
        try:
            exchange=getattr(ccxt,exchangeName)()
        except Exception as e:
            Active['JRLog'].Error("Connecting to exchange",e)
    else:
        if exchangeName=="ftxus":
            try:
                exchange=ccxt.ftx({ 'hostname': 'ftx.us', })
            except Exception as e:
                Active['JRLog'].Error("Connecting to exchange",e)
        else:
            Active['JRLog'].Error(exchangeName,"Exchange not supported")

    # If Active is empty, then use only PUBLIC API
    if Active!=[]:
        SetExchangeAPI(exchange,Active,Notify)

    return(exchange)

def SetExchangeAPI(exchange,Active,notify=False):
    exchangeName=exchange.name.lower()

    if "Sandbox" in Active:
        exchange.setSandboxMode(True)

    # Set API/Secret for every exchange

    exchange.apiKey=Active['API']
    exchange.secret=Active['SECRET']

    # Set special setting for specific exchange.

    if exchangeName=="ftx" and Active['Account']!='MAIN':
        exchange.headers['FTX-SUBACCOUNT']=Active['Account']
    else:
        if exchangeName=="ftxus" and Active['Account']!='MAIN':
            exchange.headers['FTXUS-SUBACCOUNT']=Active['Account']
        else:
            if exchangeName=="kucoin" or exchangeName=="kucoin futures":
                if 'Passphrase' in Active:
                    exchange.password=Active['Passphrase']
                else:
                    Active['JRLog'].Error("Connecting to exchange","Kucoin requires a passphrase as well")

    if "RateLimit" in Active:
        exchange.enableRateLimit=True
        exchange.rateLimit=int(Active['RateLimit'])+JRRsupport.ElasticDelay()
        if notify:
            Active['JRLog'].Write("|- Rate limit set to "+str(exchange.rateLimit)+' ms')
    else:
        exchange.enableRateLimit=False

    return(exchange)

# If fetch_ohlcv fails, revert to fetch_ticker and parse it manually
# if open is None, use low.

def FetchRetry(exchange,pair,tf,RetryLimit):
    ohlcv=GetOHLCV(exchange,pair,tf,RetryLimit)
    ticker=GetTicker(exchange,pair,RetryLimit)

    ohlc=[]
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
        for i in range(6):
            ohlc.append(ohlcv[0][i])

    return ohlc,ticker

def GetOHLCV(exchange,Active,**kwargs):
    ohlcv=ccxtAPI("fetch_ohlcv",exchange,Active,**kwargs)
    print(ohlcv)

    ohlc=[]
    if ohlcv==None:
        ohlc.append(ticker['timestamp'])
        if ticker['open']==None:
            ohlc.append(ticker['low'])
        else:
            ohlc.append(ticker['open'])
        ohlc.append(ticker['high'])
        ohlc.append(ticker['low'])
        ohlc.append(ticker['close'])

    return ohlc

def GetTicker(exchange,Active,**kwargs):
    ticker=ccxtAPI("fetch_ticker",exchange,Active,**kwargs)

    ohlc=[]
    for i in range(6):
        ohlc.append(ohlcv[0][i])

    return ticker

def GetOrderBook(exchange,Active,**kwargs):
    return ccxtAPI("fetch_order_book",exchange,Active,**kwargs)

def GetOpenOrders(exchange,Active,**kwargs):
    return ccxtAPI("fetch_open_orders",exchange,Active,**kwargs)

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
        if position['side']=='short':
            bal=-bal

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

def LoadMarkets(exchange,RetryLimit,Notify=True):
    markets=ccxtAPI("load_markets",exchange,RetryLimit)

    if Notify:
        Active['JRLog'].Write("Markets loaded")

    return markets

def GetMarkets(exchange,pair,RetryLimit,Notify=True):
    markets=LoadMarkets(exchange,RetryLimit,Notify)

    if pair[0]=='.' or pair.find(".d")>-1:
        Active['JRLog'].Error('Get Markets',pair+" is not tradable on this exchange")

    if pair not in exchange.markets:
        Active['JRLog'].Error('Get Markets',pair+" is not traded on this exchange")

    if 'active' in exchange.markets[pair]:
        if exchange.markets[pair]['active']==False:
            Active['JRLog'].Error('Get Markets',pair+" is not active on this exchange")

    return markets

# Place order. Return order ID and DON'T wait on limit orders. That needs
# to be a separate functionality.
#
# Arg sequence:
#   symbol, type, side (action), amount, price, params
#
# PlaceOrder(exchange, Active, pair=pair, orderType=orderType, action=action, amount=amount, 
#   close=close, ReduceOnly=ReduceOnly, LedgerNote=ledgerNote)

def PlaceOrder(exchange,Active,**kwargs):
    params = {}
    order=None
    pair=kwargs.get('pair')
    m=kwargs.get('orderType').lower()
    action=kwargs.get('action').lower()
    amount=kwargs.get('amount')
    price=kwargs.get('price')
    ro=kwargs.get('ReduceOnly')
    ln=kwargs.get('LedgerNote')

    if "createMarketBuyOrderRequiresPrice" in exchange.options and m=='market':
        m='limit'
    if m=='limittaker':
        m='limit'
        params['timeInForce']='fok'
    if m=='limitmaker':
        m='limit'
        params['postOnly']=True

    if kwargs.get('ReduceOnly')==True:
        if exchange.id=='binanceusdm':
            params['reduceOnly']='true'
        else:
            params['reduce_only']=ReduceOnly

    if params!={}:
        order=ccxtAPI("create_order",exchange, Active, symbol=pair, type=m, side=action, amount=amount, price=price, params=params)
    else:
        order=ccxtAPI("create_order",exchange, Active, symbol=pair, type=m, side=action, amount=amount, price=price)

    if order['id']!=None:
        Active['JRLog'].Write("|- Order Confirmation ID: "+order['id'])

        #JRRledger.WriteLedger(exchange, Active, pair, m, action, amount, price, order, ln)
        return order

    return None

# This function is used to access ALL ccxt modules with a retry
# functionality built in.
#
# examples:
# markets=ccxtAPI("load_markets",exchange)
# balance=ccxtAPI("fetch_balance",exchange)

def ccxtAPI(function,exchange,Active,**kwargs):
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
            result=callCCXT(**kwargs)
        except Exception as e:
            if exchangeName=='kucoin':
                x=str(e)
                if x.find('429000')>-1:
                    retry429+=1
            if retry>=RetryLimit:
                Active['JRLog'].Error(function,JRRsupport.StopHTMLtags(e))
            else:
                if not KuCoinSuppress429:
                    Active['JRLog'].Write(function+' Retrying ('+str(retry+1)+'), '+JRRsupport.StopHTMLtags(str(e)))
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
