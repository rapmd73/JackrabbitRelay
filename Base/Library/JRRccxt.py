#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import json
import pathlib
from datetime import datetime

import ccxt

import JRRsupport

# Class name MUST be different then above import reference.

class ccxtCrypto:
    def __init__(self,Exchange,Config,Active,Notify=True,Sandbox=False):
        # Extract for convience and readability

        self.Exchange=Exchange
        self.Config=Config
        self.Active=Active

        self.Notify=Notify
        self.Sandbox=Sandbox

        self.Log=self.Active['JRLog']

        self.Notify=True
        self.Sandbox=False
        self.Results=None

        # Deal with kucoin gracefully

        self.KuCoinSuppress429=True

        # Login to OANDA and pull the market data

        self.Broker=self.Login()
        self.Markets=self.GetMarkets()

    # This function is used to access ALL ccxt modules with a retry functionality built in.

    # examples:
    # markets=self.API("load_markets",exchange)
    # balance=aelf.API("fetch_balance",exchange)

    def API(self,function,**kwargs):
        # Kucoin don not support this, but don't break program
        if function=='fetch_positions' and self.Exchange=='kucoin':
            self.Results=None
            return self.Results

        retry429=0
        retry=0

        # Sanity check
        if 'Retry' in self.Active:
            RetryLimit=int(self.Active['Retry'])
        else:
            RetryLimit=3

        # Convert function to a CCXT module
        try:
            callCCXT=getattr(self.Broker,function)
        except Exception as e:
            x=str(e)
            self.Log.Error(function,JRRsupport.StopHTMLtags(x))

        # For kucoin only, 429000 errors are a mess. Not the best way to manage
        # them, but the onle way I know of currently to prevent losses.

        # Save the only rate limit and remap it.

        if self.Exchange=='kucoin':
            rleSave=self.Broker.enableRateLimit
            rlvSave=self.Broker.rateLimit
            self.Broker.enableRateLimit=True
            self.Broker.rateLimit=372+JRRsupport.ElasticDelay()

        done=False
        while not done:
            try:
                self.Results=callCCXT(**kwargs)
            except Exception as e:
                if self.Exchange=='kucoin':
                    x=str(e)
                    if x.find('429000')>-1:
                        retry429+=1
                if retry>=RetryLimit:
                    self.Log.Error(function,JRRsupport.StopHTMLtags(str(e)))
                else:
                    if not self.KuCoinSuppress429:
                        self.Log.Write(function+' Retrying ('+str(retry+1)+'), '+JRRsupport.StopHTMLtags(str(e)))
            else:
                done=True

            if self.Exchange=='kucoin':
                if retry429>=(RetryLimit*7):
                    retry429=0
                    retry+=1
                else:
                    retry+=1

        if self.Exchange=='kucoin':
            self.Broker.enableRateLimit=rleSave
            self.Broker.rateLimit=rlvSave

        return self.Results

    # Log into the exchange

    def Login(self):
        if self.Exchange in ccxt.exchanges:
            try:
                self.Broker=getattr(ccxt,self.Exchange)()
            except Exception as e:
                self.Log.Error("Connecting to exchange",str(e))
        else:
            if self.Exchange=="ftxus":
                try:
                    self.Broker=ccxt.ftx({ 'hostname': 'ftx.us', })
                except Exception as e:
                    self.Log.Error("Connecting to exchange",str(e))
            else:
                self.Log.Error(exchangeName,"Exchange not supported")

        # If Active is empty, then use only PUBLIC API
        if self.Active!=[]:
            self.SetExchangeAPI()

        return self.Broker

    def SetExchangeAPI(self):
        if "Sandbox" in self.Active:
            self.Broker.setSandboxMode(True)

        # Set API/Secret for every exchange

        self.Broker.apiKey=self.Active['API']
        self.Broker.secret=self.Active['SECRET']

        # Set special setting for specific exchange.

        if self.Exchange=="ftx" and self.Active['Account']!='MAIN':
            self.Broker.headers['FTX-SUBACCOUNT']=self.Active['Account']
        else:
            if self.Exchange=="ftxus" and self.Active['Account']!='MAIN':
                self.Broker.headers['FTXUS-SUBACCOUNT']=self.Active['Account']
            else:
                if self.Exchange=="kucoin" or self.exchange=="kucoin futures":
                    if 'Passphrase' in self.Active:
                        self.Broker.password=self.Active['Passphrase']
                    else:
                        self.Log.Error("Connecting to exchange","Kucoin requires a passphrase as well")

        # Logging the rate limit is an absolute nightmare as it is so frequent

        if "RateLimit" in self.Active:
            self.Broker.enableRateLimit=True
            self.Broker.rateLimit=int(self.Active['RateLimit'])+JRRsupport.ElasticDelay()
        else:
            self.Broker.enableRateLimit=False

    # Get the market list. Notifications is a waste of logging.

    def GetMarkets(self):
        self.Markets=self.API("load_markets")

        return self.Markets

    def VerifyMarket(self,pair):
        self.Markets=self.GetMarkets()

        if pair[0]=='.' or pair.find(".d")>-1:
            swelf.Log.Error('Get Markets',pair+" is not tradable on this exchange")

        if pair not in exchange.markets:
            self.Log.Error('Get Markets',pair+" is not traded on this exchange")

        if 'active' in exchange.markets[pair]:
            if self.Broker.markets[pair]['active']==False:
                self.Log.Error('Get Markets',pair+" is not active on this exchange")

        return True

    # Fetch the balance(s) of a given BASE of a pair

    def GetBalance(self,**kwargs):
        base=kwargs.get('Base')

        self.Results=self.API("fetch_balance")

        if base==None:
            return self.Results
        else:
            base=base.upper()
            if base in self.Results['total']:
                bal=float(self.Results['total'][base])
                return bal
            else:
                # This is an absolute horrible way to handle this, but
                # unfortunately the only way. Many exchanges don't report a
                # balance at all if an asset hasn't been traded in a given
                # timeframe (usually fee based tier resets designate the cycle).
                return 0

    # Get positions

    def GetPositions(self,**kwargs):
        self.Results=self.API("fetch_positions")

        symbol=kwargs.get('symbol')
        if symbol==None:
            return self.Results
        else:
            symbol=symbol.upper()
            position=None
            for pos in self.Results:
                if pos['symbol']==symbol:
                    position=pos
                    break
            if position!=None:
                bal=position['contracts']
                if position['side']=='short':
                    bal=-bal
                return bal
            else:
                return 0

    def GetOHLCV(self,**kwargs):
        self.Results=self.API("fetch_ohlcv",**kwargs)
        return self.Results

    def GetTicker(self,**kwargs):
        self.Results=self.API("fetch_ticker",**kwargs)

        Pair={}
        Pair['Ask']=self.Results['ask']
        Pair['Bid']=self.Results['bid']
        Pair['Spread']=Pair['Ask']-Pair['Bid']

        return Pair

    def GetOrderBook(self,**kwargs):
        self.Results=self.API("fetch_order_book",**kwargs)
        return self.Results

    def GetOpenOrders(self,**kwargs):
        self.Results=self.API("fetch_open_orders",**kwargs)
        return self.Results

    # Most brokers track individual trades, as well as the average. Cryptocurrency exchanges
    # track only averages, but this is needed for conformity with the main Relay structure.

    def GetOpenTrades(self,**kwargs):
        return None

    # Place order. Return order ID and DON'T wait on limit orders. That needs to be a separate
    # functionality.

    # Arg sequence:
    #   symbol, type, side (action), amount, price, params

    # PlaceOrder(exchange, Active, pair=pair, orderType=orderType, action=action, amount=amount, 
    #   close=close, ReduceOnly=ReduceOnly, LedgerNote=ledgerNote)

    def PlaceOrder(self,**kwargs):
        params = {}
        order=None
        pair=kwargs.get('pair')
        m=kwargs.get('orderType').lower()
        action=kwargs.get('action').lower()
        amount=kwargs.get('amount')
        price=kwargs.get('price')
        ro=kwargs.get('ReduceOnly')
        ln=kwargs.get('LedgerNote')

        # Deal with special case order types

        if "createMarketBuyOrderRequiresPrice" in self.Broker.options and m=='market':
            m='limit'
        if m=='limittaker':
            m='limit'
            params['timeInForce']='fok'
        if m=='limitmaker':
            m='limit'
            params['postOnly']=True

        # Deal with Binance Futures special case

        if kwargs.get('ReduceOnly')==True:
            if self.Broker.id=='binanceusdm':
                params['reduceOnly']='true'
            else:
                params['reduce_only']=ReduceOnly

        if params!={}:
            order=self.API("create_order",symbol=pair,type=m,side=action,amount=amount,price=price,params=params)
        else:
            order=self.API("create_order",symbol=pair,type=m,side=action,amount=amount,price=price)

        if order['id']!=None:
            self.Log.Write("|- Order Confirmation ID: "+order['id'])

            #JRRledger.WriteLedger(pair, m, action, amount, price, order, ln)
            return order

        return None






















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
