#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
import ccxt
from datetime import datetime

import JRRconfig
import JRRlog
import JRRledger
import JRRsupport

KuCoinSuppress429=True

msec = 1000
minute = 60 * msec
hour = 60 * minute
day = 24 * hour
hold = 30

# Dirty support function to block HTML exchange payloads

def StopHTMLtags(txt):
    try:
        p=txt.find('<')
        if p>-1:
            return txt[:p]
    except:
        pass
    return txt

# Register the exchange

def ExchangeLogin(exchangeName,Active,Notify=True):
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

    SetExchangeAPI(exchange,Active,Notify)

    return(exchange)

def SetExchangeAPI(exchange,Active,notify=False):
    exchangeName=exchange.name.lower()

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
            if exchangeName=="kucoin":
                if 'Passphrase' in Active:
                    exchange.password=Active['Passphrase']
                else:
                    JRRlog.ErrorLog("Connecting to exchange","Kucoin requires a passphrase as well")

    exchange.verbose=False

    if "RateLimit" in Active:
        exchange.enableRateLimit=True
        exchange.rateLimit=int(Active['RateLimit'])+JRRsupport.ElasticDelay()
        if notify:
            JRRlog.WriteLog("|- Rate limit set to "+str(exchange.rateLimit)+' ms')
    else:
        exchange.enableRateLimit=False

    return(exchange)

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

def GetAssetMinimum(exchange,pair,diagnostics,RetryLimit):
    ohlcv,ticker=FetchRetry(exchange,pair,"1m",RetryLimit)

    close=ohlcv[4]

    minimum1=exchange.markets[pair]['limits']['amount']['min']
    if minimum1==None:
        minimum1=0.0
    minimum2=exchange.markets[pair]['limits']['cost']['min']
    if minimum2==None:
        minimum2=0.0
    minimum3=exchange.markets[pair]['limits']['price']['min']
    if minimum3==None:
        minimum3=0.0

    if minimum1==0:
        m1=0.0
    else:
        m1=float(minimum1)*close
    if minimum2==0:
        m2=0.0
    else:
        m2=float(minimum2)/close
    if minimum3==0:
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
        JRRlog.WriteLog(f"| |- Close: {close:.8f}")
        JRRlog.WriteLog(f"| |- Minimum Amount: {minimum1:.8f}, {m1:.8f}")
        JRRlog.WriteLog(f"| |- Minimum Cost:   {minimum2:.8f}, {m2:.8f}")
        JRRlog.WriteLog(f"| |- Minimum Price:  {minimum3:.8f}, {m3:.8f}")

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
        JRRlog.WriteLog("| |- Minimum: "+f"{minimum:.8f}")
        JRRlog.WriteLog("| |- Min Cost: "+f"{mincost:.8f}")

# If quote is NOT USD/Stablecoin. NOTE: This is an API penalty for the
# overhead of pulling quote currency. Quote currency OVERRIDES base ALWAYS.

    if diagnostics:
        JRRlog.WriteLog("|- Quote: "+quote)

    if quote not in JRRconfig.StableCoinUSD or forceQuote:
        bpair=FindMatchingPair(quote,exchange.markets)
        if bpair!=None:
            minimum,mincost=GetAssetMinimum(exchange,bpair,diagnostics,RetryLimit)

            if diagnostics:
                JRRlog.WriteLog("| |- Minimum: "+f"{minimum:.8f}")
                JRRlog.WriteLog("| |- Min Cost: "+f"{mincost:.8f}")

    if minimum==0.0:
        JRRlog.ErrorLog("Asset Analysis","minimum position size returmed as 0")
    if mincost==0.0:
        JRRlog.ErrorLog("Asset Analysis","minimum cost per position returmed as 0")

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
            fo=exchange.fetchOrder(oi,symbol=pair)
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
    JRRlog.WriteLog("|- Waiting for limit order")
    ohist=FetchExchangeOrderHistory(exchange,oi,pair,RetryLimit)

    # cancel the order
    if ohist==False:
        try:
            ct=exchange.cancel_order(oi,pair)
        except:
            pass
    else:
        return True

def PlaceOrder(exchange, account, pair, market, action, amount, close, RetryLimit, ReduceOnly):
    params = {}
    order=None

    m=market.lower()
    if "createMarketBuyOrderRequiresPrice" in exchange.options and m=='market':
        m='limit'
    if m=='limittaker':
        m='limit'
        params['timeInForce']='fok'
    if m=='limitmaker':
        m='limit'
        params['postOnly']=True

    retry=0
    done=False
    while not done:
        try:
            if ReduceOnly==True:
                if exchange.id=='binanceusdm':
                    params['reduceOnly']='true'
                else:
                    params['reduce_only']=ReduceOnly
                order=exchange.create_order(pair, m, action, amount, close, params)
            else:
                if m=='limit':
                    order=exchange.create_order(pair, m, action, amount, close, params)
                else:
                    order=exchange.create_order(pair, m, action, amount, close)
        except Exception as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Placing Order",e)
            else:
                JRRlog.WriteLog('Place Order Retrying ('+str(retry+1)+'), '+StopHTMLtags(str(e)))
        else:
            done=True
            if m=='limit':
                # wait no more then 3 minutes
                successful=WaitLimitOrder(exchange,order['id'],pair,15)
                if successful==True:
                    JRRlog.WriteLog("|- Order Confirmation ID: "+order['id'])
                else:
                    JRRlog.ErrorLog("Placing Order","limit order unsuccessful")
            else:
                JRRlog.WriteLog("|- Order Confirmation ID: "+order['id'])

            JRRledger.WriteLedger(exchange, account, pair, market, action, amount, close, order, RetryLimit)
            return order
        retry+=1

    if retry>=RetryLimit:
        JRRlog.ErrorLog("Placing Order","order unsuccessful")

# Customized fetch OHLCV. Fetches an entire page

def FetchCandles(exchange,pair,tf,CandleCount,RetryLimit):
    exchangeName=exchange.name.lower()
    ohlcv=[]
    retry429=0
    retry=0

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
            if CandleCount>0:
                ohlcv=exchange.fetch_ohlcv(symbol=pair,timeframe=tf,limit=CandleCount)
            else:
                ohlcv=exchange.fetch_ohlcv(symbol=pair,timeframe=tf)
            if ohlcv==[]:
                ohlcv=None
        except Exception as e:
            if exchangeName=='kucoin':
                x=str(e)
                if x.find('429000')>-1:
                    retry429+=1
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetching OHLCV",e)
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

    return ohlcv

def FetchCandles_interval(exchange,pair,tf,start_date_time,end_date_time,RetryLimit):
    exchangeName=exchange.name.lower()
    ohlcv=[]
    data=[]
    retry429=0
    retry=0
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

            ohlcvs = exchange.fetch_ohlcv(pair,tf,from_timestamp)
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
                JRRlog.ErrorLog("Fetching OHLCV",e)
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

# If fetch_ohlcv fails, revert to fetch_ticker and parse it manually
# if open is None, use low.

def FetchRetry(exchange,pair,tf,RetryLimit):
    exchangeName=exchange.name.lower()
    ohlcv=[]
    retry429=0
    retry=0

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
            ohlcv=exchange.fetch_ohlcv(symbol=pair,timeframe=tf,limit=1)
            if ohlcv==[]:
                ohlcv=None
        except Exception as e:
            if exchangeName=='kucoin':
                x=str(e)
                if x.find('429000')>-1:
                    retry429+=1
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetching OHLCV",StopHTMLtags(e))
            else:
                if not KuCoinSuppress429:
                    JRRlog.WriteLog('Fetch OHLCV Retrying ('+str(retry+1)+'), '+StopHTMLtags(str(e)))
        else:
            done=True

        if exchangeName=='kucoin':
            if retry429>=(RetryLimit*7):
                retry429=0
                retry+=1
        else:
            retry+=1

    ticker=None
    retry=0
    retry429=0
    done=False
    while not done:
        try:
            ticker=exchange.fetch_ticker(pair)
        except Exception as e:
            if exchangeName=='kucoin':
                x=str(e)
                if x.find('429000')>-1:
                    retry429+=1
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetching Ticker",StopHTMLtags(e))
            else:
                if not KuCoinSuppress429:
                    JRRlog.WriteLog('Fetch Ticker Retrying ('+str(retry+1)+'), '+StopHTMLtags(str(e)))
        else:
            done=True

        if exchangeName=='kucoin':
            if retry429>=(RetryLimit*7):
                retry429=0
                retry+=1
        else:
            retry+=1

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

    if exchangeName=='kucoin':
        exchange.enableRateLimit=rleSave
        exchange.rateLimit=rlvSave

    return ohlc, ticker

# Fetch the balance of a given BASE of a pair

def GetBalance(exchange,base,RetryLimit):
    retry=0
    done=False
    while not done:
        try:
            balance=exchange.fetch_balance()
            if base in balance['total']:
                bal=float(balance['total'][base])
            else:
                # This is an absolute horrible way to handle this, but unfortunately the only way.
                # Many exchanges don't report a balance at all if an asset hasn't been traded in
                # a given timeframe (usually fee based tier resets designate the cycle).
                bal=0
        except (ccxt.DDoSProtection, ccxt.RequestTimeout, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.ExchangeError, ccxt.NetworkError) as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetch Balance",e)
            else:
                JRRlog.WriteLog('Fetch Balance Retrying ('+str(retry+1)+'), '+StopHTMLtags(str(e)))
        else:
            done=True
        retry+=1

    return bal

# Fetch the position of a given of a pair

def GetPosition(exchange,pair,RetryLimit):
    retry=0
    done=False
    while not done:
        try:
            positions = exchange.fetch_positions()
            positions_by_symbol = exchange.index_by(positions, 'symbol')
            position = exchange.safe_value(positions_by_symbol, pair)
        except Exception as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetch Position",e)
            else:
                JRRlog.WriteLog('Fetch Position Retrying ('+str(retry+1)+'), '+StopHTMLtags(str(e)))
        else:
            done=True
        retry+=1

    return position

# Fetch the market list

def GetMarkets(exchange,pair,RetryLimit,Notify=True):
    retry=0
    done=False
    while not done:
        try:
            markets=exchange.load_markets()
        except Exception as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetch Markets",e)
            else:
                if Notify:
                    JRRlog.WriteLog('Fetch Markets Retrying ('+str(retry+1)+'), '+StopHTMLtags(str(e)))
        else:
            done=True
        retry+=1

    if Notify:
        JRRlog.WriteLog("Markets loaded")

    if pair[0]=='.' or pair.find(".d")>-1:
        JRRlog.ErrorLog('Get Markets',pair+" is not tradable on this exchange")

    if pair not in exchange.markets:
        JRRlog.ErrorLog('Get Markets',pair+" is not traded on this exchange")

    if 'active' in exchange.markets[pair]:
        if exchange.markets[pair]['active']==False:
            JRRlog.ErrorLog('Get Markets',pair+" is not active on this exchange")

    return markets

def LoadMarkets(exchange,RetryLimit,Notify=True):
    retry=0
    done=False
    while not done:
        try:
            markets=exchange.load_markets()
        except Exception as e:
            if retry>=RetryLimit:
                JRRlog.ErrorLog("Fetch Markets",e)
            else:
                if Notify:
                    JRRlog.WriteLog('Fetch Markets Retrying ('+str(retry+1)+'), '+StopHTMLtags(str(e)))
        else:
            done=True
        retry+=1

    if Notify:
        JRRlog.WriteLog("Markets loaded")

    return markets
