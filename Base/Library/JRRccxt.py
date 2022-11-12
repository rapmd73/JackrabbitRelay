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
from datetime import datetime

import ccxt

import JRRsupport

# Class name MUST be different then above import reference.

class ccxtCrypto:
    def __init__(self,Exchange,Config,Active,Notify=True,Sandbox=False,DataDirectory=None):

        # This is sorted by market cap. Hopefully it will speed up the
        # conversion process. Coins only with 100 million or more listed.

        self.StableCoinUSD=['USDT','USDC','BUSD','UST','DAI','FRAX','TUSD', \
                'USDP','LUSD','USDN','HUSD','FEI','TRIBE','RSR','OUSD','XSGD', \
                'GUSD','USDX','SUSD','EURS','CUSD','USD']

        # Extract for convience and readability

        self.Exchange=Exchange
        self.Config=Config
        self.Active=Active

        self.Notify=Notify
        self.Sandbox=Sandbox

        # This s an absolute bastardation of passing a directory from a upper
        # level to a lower one for a one off situation. The method used for
        # logging is the best approach, but not appropriate for a signle use
        # case.

        self.DataDirectory=DataDirectory
        self.Log=self.Active['JRLog']

        self.Notify=True
        self.Sandbox=False
        self.Results=None

        # Deal with kucoin gracefully

        self.KuCoinSuppress429=True

        # Login to crypto exchange and pull the market data

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
                if self.Exchange=="kucoin" or self.Exchange=="kucoinfutures":
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
            self.Log.Error('Get Markets',pair+" is not tradable on this exchange")

        if pair not in exchange.markets:
            self.Log.Error('Get Markets',pair+" is not traded on this exchange")

        if 'active' in exchange.markets[pair]:
            if self.Markets[pair]['active']==False:
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
            # No results means a 0 balance
            if self.Results==None:
                return 0
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
        error=kwargs.get('Error')
        self.Results=self.API("fetch_ticker",**kwargs)

        # Kucoin Sandbox system doesn't always give complete data

        if (self.Results['ask']==None or self.Results['bid']==None):
            if  error==True:
                self.Log.Error('GetTicker',"ticker data is incomplete")
            else:
                return None

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

    # Place order. Return order ID and DON'T wait on limit orders. That needs to
    # be a separate functionality.

    # Market - LimitTaker - IOC true, limit orders with taker fee, psuedo market
    #                       orders
    #          LimitMaker - PostOnly true, full limit orders with maker fee

    # Arg sequence:
    #   symbol, type, side (action), amount, price, params

    # PlaceOrder(exchange, Active, pair=pair, orderType=orderType,
    #     action=action, amount=amount, close=close, ReduceOnly=ReduceOnly, 
    #     LedgerNote=ledgerNote)

    def PlaceOrder(self,**kwargs):
        pair=kwargs.get('pair')
        m=kwargs.get('orderType').lower()
        action=kwargs.get('action').lower()
        amount=float(kwargs.get('amount'))
        price=kwargs.get('price')
        ro=kwargs.get('ReduceOnly')
        ln=kwargs.get('LedgerNote')

        params = {}
        order=None

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
                params['reduce_only']=ro

        # Shorts are stored as negative numbers, abs() is a safety catch

        if params!={}:
            order=self.API("create_order",symbol=pair,type=m,side=action,amount=abs(amount),price=price,params=params)
        else:
            order=self.API("create_order",symbol=pair,type=m,side=action,amount=abs(amount),price=price)

        if order['id']!=None:
            self.Log.Write("|- Order Confirmation ID: "+order['id'])

            #JRRledger.WriteLedger(pair, m, action, amount, price, order, ln)
            return order

        return None

    # Find the minimum amount/price. This is one of the mot complex areas of
    # cryptocurrency markets. Each exchange and market can has its own minimum
    # amout (units/shares) and price decided either of the base (left) or quote
    # (right) currency.

    # Get asset information

    def GetMinimum(self,**kwargs):
        symbol=kwargs.get('symbol')
        forceQuote=kwargs.get('forceQuote')
        diagnostics=kwargs.get('diagnostics')

        base=self.Markets[symbol]['base']
        quote=self.Markets[symbol]['quote']

        minimum,mincost=self.GetAssetMinimum(symbol,diagnostics)

        # Get BASE minimum. This is all that is needed if quote is
        # USD/Stablecoins

        if diagnostics:
            self.Log.Write("Minimum asset analysis")
            self.Log.Write("|- Base: "+base)
            self.Log.Write(f"| |- Minimum: {minimum:.8f}")
            self.Log.Write(f"| |- Min Cost: {mincost:.8f}")

            # If quote is NOT USD/Stablecoin. NOTE: This is an API penalty
            # for the overhead of pulling quote currency. Quote currency
            # OVERRIDES base ALWAYS.

            self.Log.Write("|- Quote: "+quote)

        if quote not in self.StableCoinUSD or forceQuote:
            bpair=self.FindMatchingPair(quote)
            if bpair!=None:
                minimum,mincost=self.GetAssetMinimum(bpair,diagnostics)

                if diagnostics:
                    self.Log.Write(f"| |- Minimum: {minimum:.8f}")
                    self.Log.Write(f"| |- Min Cost: {mincost:.8f}")

        if minimum==0.0:
            self.Log.Error("Asset Analysis","minimum position size returned as 0")
        if mincost==0.0:
            self.Log.Error("Asset Analysis","minimum cost per position returned as 0")

        return minimum,mincost

    # Check for an overide value or pull exchange data to calculatethe minimum
    # amount and cost.

    def GetAssetMinimum(self,pair,diagnostics):
        exchangeName=self.Broker.name.lower().replace(' ','')
        ticker=self.GetTicker(symbol=pair)

        # This is the lowest accepted price of market order

        close=ticker['Ask']

        # Check if there is an overide in place

        minimum=self.LoadMinimum(exchangeName,pair)
        if minimum>0.0:
            mincost=round(minimum*close,8)

            if diagnostics:
                self.Log.Write(f"| |- Close: {close:.8f}")
                self.Log.Write(f"| |- (Table)Minimum Amount: {minimum:.8f}")
                self.Log.Write(f"| |- (Table)Minimum Cost:   {mincost:.8f}")
        else:
            # Find the minimum amount and price of this asset.

            minimum1=self.Markets[pair]['limits']['amount']['min']
            minimum2=self.Markets[pair]['limits']['cost']['min']
            minimum3=self.Markets[pair]['limits']['price']['min']

            # Check if this is a futures market

            if minimum1==None or minimum1==0:
                if 'contractSize' in self.Markets[pair]:
                    minimum1=self.Markets[pair]['contractSize']
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
                if self.Broker.precisionMode==ccxt.TICK_SIZE:
                    minimum=float(self.Markets[pair]['precision']['amount'])
                    mincost=minimum*close
                else:
                    z='000000000'
                    factor=max(self.Broker.precisionMode,ccxt.TICK_SIZE)
                    minimum=float('0.'+str(z[:factor-1])+'1')
                    mincost=minimum*close

            if diagnostics:
                self.Log.Write(f"| |- Close: {close:.8f}")
                self.Log.Write(f"| |- Minimum Amount: {minimum1:.8f}, {m1:.8f}")
                self.Log.Write(f"| |- Minimum Cost:   {minimum2:.8f}, {m2:.8f}")
                self.Log.Write(f"| |- Minimum Price:  {minimum3:.8f}, {m3:.8f}")

        return minimum,mincost

    # if quote is UDSC, find a market that provides a close price comparision
    # that is on the exchange, ie... USDT. For example BTC/USDC compares to
    # BTC/USDT is terms of both quote currenciesbeing pegged to the USD as
    # stable.

    def FindMatchingPair(base):
        for quote in self.StableCoinUSD:
            pair=base+'/'+quote
            if pair in self.Markets:
                return pair

        return None

    # Pull the information about the asset minimums from the exchange.

    # Amount is the minimum amount in the ASSET, if TRX/BTC, amount is always
    # BASE value

    # Cost in USD/Stablecoins
    # Price in USD/Stablecoins

    def LoadMinimum(self,exchangeName,pair):
        minlist={}
        amount=0
        fn=self.DataDirectory+'/'+exchangeName+'.minimum'
        if os.path.exists(fn):
            try:
                raw=JRRsupport.ReadFile(fn)
            except:
                self.Log.Error("Minimum List",f"Can't read minimum list for {exchangeName}")

            minlist=json.loads(raw)
            if pair in minlist:
                amount=minlist[pair]

        return amount

    # This is used to update the minimum amount list. 

    def UpdateMinimum(self,exchangeName,pair,amount):
        minlist={}
        fn=self.DataDirectory+'/'+exchangeName+'.minimum'
        if os.path.exists(fn):
            try:
                raw=JRRsupport.ReadFile(fn)
            except:
                self.Log.Error("Minimum List",f"Can't read minimum list for {exchangeName}")

        minlist=json.loads(raw)

        minlist[pair]=amount
        fh=open(fn,'w')
        fh.write(json.dumps(minlist))
        fh.close()

    # Get details of a specific order by ID

    def GetOrderDetails(self,**kwargs):
        if self.Broker.has['fetchOrder']:
            self.Results=self.API("fetchOrder",**kwargs)
        else:
            self.Results=self.API("fetchClosedOrder",**kwargs)
        return self.Results

    # Create an orphan order and deliver to OliverTwist

    def MakeOrphanOrder(self,id,Order):
        OrphanReceiver=self.DataDirectory+'/OliverTwist.Receiver'
        orphanLock=JRRsupport.Locker("OliverTwist")

        Orphan={}
        Orphan['Status']='Open'
        Orphan['Framework']='ccxt'
        Orphan['ID']=id
        Orphan['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        Orphan['Order']=json.dumps(Order)

        orphanLock.Lock()
        JRRsupport.AppendFile(OrphanReceiver,json.dumps(Orphan))
        orphanLock.Unlock()

    # Make ledger entry. Record everything for accounting purposes

    def WriteLedger(self,**kwargs):
        Order=kwargs.get('Order')
        Response=kwargs.get('Response')
        LedgerDirectory=kwargs.get('LedgerDirectory')

        if Response!=None:
            id=Response['id']
        else:
            id=Order['ID']

        detail=self.GetOrderDetails(id=id)

        ledger={}
        ledger['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        ledger['ID']=id
        ledger['Order']=Order
        if Response!=None:
            ledger['Response']=Response
        ledger['Detail']=detail

        # We need the embedded order reference if comming from OliverTwist
        if 'Order' in Order:
            subOrder=json.loads(Order['Order'])
        else:
            subOrder=Order
        if subOrder['Exchange']!=None and subOrder['Account']!=None and subOrder['Asset']!=None:
            if "Market" in subOrder:
                fname=subOrder['Exchange']+'.'+subOrder['Market']+'.'+subOrder['Account']+'.'+subOrder['Asset']
            else:
                fname=sbOrder['Exchange']+'.'+subOrder['Account']+'.'+subOrder['Market']+'.'+subOrder['Asset']
            fname=fname.replace('/','').replace('-','').replace(':','').replace(' ','')
            lname=LedgerDirectory+'/'+fname+'.ledger'

            ledgerLock=JRRsupport.Locker(lname)
            ledgerLock.Lock()
            JRRsupport.AppendFile(lname,json.dumps(ledger)+'\n')
            ledgerLock.Unlock()

