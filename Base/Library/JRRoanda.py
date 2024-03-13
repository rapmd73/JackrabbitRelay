#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay, OANDA framework
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import math
import signal
import json
from datetime import datetime

import oandapyV20
import oandapyV20.definitions as V20Definitions
import oandapyV20.endpoints
import oandapyV20.contrib
import oandapyV20.endpoints.accounts as v20Accounts
import oandapyV20.endpoints.instruments as v20Instruments
import oandapyV20.endpoints.pricing as v20Pricing
import oandapyV20.endpoints.orders as v20Orders
import oandapyV20.endpoints.positions as v20Positions
import oandapyV20.endpoints.trades as v20Trades
import oandapyV20.endpoints.transactions as v20Transactions
import oandapyV20.contrib.requests as v20Requests

import JRRsupport

class oanda:
    # Define the special variables for this object. ALL variable WITHIN
    # the class must have the prefix of self. self defines the internal
    # mechanics that help isolate variables.

    # Initialize the object and automatically get everything set up

    # Account ID and bearer token will be in Active. Logging framework and
    # identity are embedded here as well.

    # OANDA does NOT support API key rotation so this will not effect long term
    # stability.

    # AccessToken (Bearer) is API

    def __init__(self,Exchange,Config,Active,DataDirectory=None):
        self.DataDirectory=DataDirectory

        self.Exchange=Exchange
        self.Config=Config
        self.Active=Active

        # Extract for convience and readability

        self.AccountID=self.Active['AccountID']
        self.AccessToken=self.Active['API']
        self.Log=self.Active['JRLog']

        self.timeframes=V20Definitions.instruments.definitions['CandlestickGranularity']
        self.Notify=True
        self.Sandbox=False
        self.Results=None

        # Login to OANDA and pull the market data

        self.Broker=self.Login()
        self.Summary=self.GetSummary()
        self.Currency=None
        self.Markets=self.GetMarkets()

        self.onePip=None

    # Set the value of one pip

    def SetPipValue(self,asset):
        # Value needed to calculate 1 pip for this pair
        if self.onePip==None:
            if abs(float(self.Markets[asset.replace('_','/')]['pipLocation']))==2:
                self.onePip=0.01
            else:
                self.onePip=0.0001

    # Handle the retry functionality and send the request to the broker.

    def API(self,function,**kwargs):
        req=kwargs.get('request')
        noError=kwargs.get('noError')
        retry=0

        # Sanity check
        if 'Retry' in self.Active:
            RetryLimit=int(self.Active['Retry'])
        else:
            RetryLimit=3

        done=False
        while not done:
            try:
                self.Results=self.Broker.request(req)
            except Exception as e:
                if retry<RetryLimit:
                    if noError==True:
                        # Market is closed, no orders
                        if function=='GetOrderBook':
                            return []
                        else:
                            self.Log.Error(function,JRRsupport.StopHTMLtags(str(e)))
                    else:
                        self.Log.Error(function,JRRsupport.StopHTMLtags(str(e)))
                else:
                    if noError==False:
                        self.Log.Write(function+' Retrying ('+str(retry+1)+'), '+JRRsupport.StopHTMLtags(str(e)))
            else:
                done=True
            retry+=1

        return self.Results

    # Register the exchange

    def Login(self,Notify=True,Sandbox=False):
        if Sandbox==True or "Sandbox" in self.Active:
            Sandbox=True
            envTrade="practice"
        else:
            envTrade="live"
        try:
            self.Broker=oandapyV20.API(access_token=self.AccessToken,environment=envTrade)
        except Exception as e:
            self.Log.Error("Login",JRRsupport.StopHTMLtags(str(e)))

        self.Notify=Notify
        self.Sandbox=Sandbox

        return self.Broker

    # Get general account sumerary

    def GetSummary(self,**kwargs):
        res=v20Accounts.AccountSummary(accountID=self.AccountID)
        self.Results=self.API("GetBalance",request=res)
        self.Currency=self.Results['account']['currency']
        return self.Results

    # Get the list of cureent markets allowed to trade.

    def GetMarkets(self):
        markets={}
        res=v20Accounts.AccountInstruments(accountID=self.AccountID)
        self.Results=self.API("GetMarkets",request=res)
        for cur in self.Results['instruments']:
            asset=cur['name'].upper().replace('_','/')
            markets[asset]=cur
        return markets

    # Get the balance of the account. kwargs is needed for conformity with other
    # exchanges/brokers even though it will never be used by OANDA.

    def GetBalance(self,**kwargs):
        res=v20Accounts.AccountSummary(accountID=self.AccountID)
        self.Results=self.API("GetBalance",request=res)
        self.Currency=self.Results['account']['currency']
        return float(self.Results['account']['balance'])

    # Get the current positions list or
    # get an individual and specific position. In OANDA, a position may be one
    # or more actual trades.

    # Shorts are negative

    def GetPositions(self,**kwargs):
        res=v20Positions.OpenPositions(accountID=self.AccountID)
        self.Results=self.API("GetPositions",request=res)

        symbol=kwargs.get('symbol')
        if symbol==None:
            return self.Results['positions']
        else:
            symbol=symbol.upper()
            position=0.0
            for pos in self.Results['positions']:
                asset=pos['instrument'].replace('_','/')
                if symbol==asset:
                    self.SetPipValue(symbol)
                    if 'averagePrice' in pos['long']:
                        units=int(pos['long']['units'])
                        position=float(pos['long']['averagePrice'])*units
                    else: # shorts already negative
                        units=int(pos['short']['units'])
                        position=(float(pos['short']['averagePrice']))*units
                    # Access the Results to get units
                    self.Results['Units']=units
                    return position
            self.Results['Units']=0
            return 0

    # Get candlestick (OHLCV) data

    def GetOHLCV(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')
        timeframe=kwargs.get('timeframe')
        limit=str(kwargs.get('limit'))
        params={"granularity":timeframe.upper(), "count":limit }
        candles=[]
        self.SetPipValue(symbol)

        res=v20Instruments.InstrumentsCandles(instrument=symbol,params=params)
        self.Results=self.API("GetOHLCV",request=res)
        for cur in self.Results['candles']:
            candle=[]
            candle.append(int(datetime.strptime(cur['time'],'%Y-%m-%dT%H:%M:%S.000000000Z').timestamp())*1000)
            candle.append(float(cur['mid']['o']))
            candle.append(float(cur['mid']['h']))
            candle.append(float(cur['mid']['l']))
            candle.append(float(cur['mid']['c']))
            candle.append(float(cur['volume']))
            candles.append(candle)
        return candles

    # Get the bid/ask values of the curent ticker

    def GetTicker(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')
        params={"instruments":symbol }
        self.SetPipValue(symbol)

        res=v20Pricing.PricingInfo(accountID=self.AccountID,params=params)
        self.Results=self.API("GetTicker",request=res)

        # Build the forex pair dictionary

        b=round(float(self.Results['prices'][0]['bids'][0]['price']),5)
        a=round(float(self.Results['prices'][0]['asks'][0]['price']),5)
        s=abs(b-a)

        Pair={}
        Pair['DateTime']=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        Pair['Bid']=max(b,a)
        Pair['Ask']=min(b,a)
        Pair['Spread']=round(s,5)

        return Pair

    # Get the order book

    def GetOrderBook(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')
        self.SetPipValue(symbol)

        req=v20Instruments.InstrumentsOrderBook(instrument=symbol,params={})
        self.Results=self.API("GetOrderBook",request=req,noError=True)
        if self.Results!=[]:
            return self.Results['orderBook']['buckets']
        else:
            return self.Results

    # Get a list of pending (open) orders.

    def GetOpenOrders(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')

        req=v20Orders.OrdersPending(accountID=self.AccountID)
        self.Results=self.API("GetOpenOrders",request=req)

        if symbol==None:
            return self.Results['orders']
        else:
            symbol=symbol.upper().replace('/','_')
            oList=[]
            for order in self.Results['orders']:
                if symbol==order['instrument']:
                    oList.append(order)

        self.SetPipValue(symbol)
        return oList

    # As references in GetPosition, a position may consist of one or more actual
    # trades. This is NOT the same as an open list of limit orders.
    # count is maximum number o allowed open trades.

    def GetOpenTrades(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')
        params={"instrument":symbol,"count":500 }
        self.SetPipValue(symbol)

        req=v20Trades.TradesList(accountID=self.AccountID,params=params)
        self.Results=self.API("GetOpenTrades",request=req)
        return self.Results['trades']

    # Place order. Return order ID and DON'T wait on limit orders. That needs to
    # be a separate functionality.

    # Arg sequence:
    #   symbol, type, side (action), amount, price, params

    # PlaceOrder(pair=pair, orderType=orderType, action=action, amount=amount, 
    #   close=close, Ticket=45, ReduceOnly=ReduceOnly, LedgerNote=ledgerNote)

    # IMPORTANT: buy and sell are TWO DIFFERENT END POINTS

    # Market orders are fill or kill (FOK) for timeInForce by default. GTC will
    # NOT work.

    # OANDA requires that units or amount of purchase be a whole number. Partial
    # shares/unts are NOT allowed.

    # There are actually THREE API end points involved in placing an order,
    # buying, selling from the entire position (FIFO rule), selling an
    # individual trade with an explicit ticket number.

    def PlaceOrder(self,**kwargs):
        pair=kwargs.get('pair').replace('/','_')
        m=kwargs.get('orderType').upper()
        action=kwargs.get('action').lower()
        amount=kwargs.get('amount')
        price=kwargs.get('price')
        ro=kwargs.get('ReduceOnly')
        ln=kwargs.get('LedgerNote')
        ticket=kwargs.get('ticket')
        Quiet=kwargs.get('Quiet')

        if(action=='buy'):
            order={}
            if m=='LIMIT':
                order['price']=str(price)
                order['timeInForce']='GTC'
            order['units']=str(amount)
            order['instrument']=pair
            order['type']=m
            order['positionFill']='DEFAULT'
            params={}
            params['order']=order

            res=v20Orders.OrderCreate(accountID=self.AccountID,data=params)
            self.Results=self.API("OrderCreate",request=res)

            if 'orderCreateTransaction' in self.Results:
                if 'orderCancelTransaction' in self.Results:
                    if Quiet!=True:
                        self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                else:
                    if Quiet!=True:
                        self.Log.Write("|- Order Confirmation ID: "+self.Results['orderCreateTransaction']['id'])
            elif 'longOrderCreateTransaction' in self.Results:
                if 'orderCancelTransaction' in self.Results:
                    if Quiet!=True:
                        self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                else:
                    if Quiet!=True:
                        self.Log.Write("|- Order Confirmation ID: "+self.Results['longOrderCreateTransaction']['id'])
            elif 'shortOrderCreateTransaction' in self.Results:
                if 'orderCancelTransaction' in self.Results:
                    if Quiet!=True:
                        self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                else:
                    if Quiet!=True:
                        self.Log.Write("|- Order Confirmation ID: "+self.Results['shortOrderCreateTransaction']['id'])
        elif (action=='sell'):
            params={}
            if ticket==None:
                if 'ALL' not in str(amount).upper():
                    # amount is STR, need int for abs()
                    amount=int(amount)
                    if amount>=0:
                        params['longUnits']=str(int(abs(amount)))
                    else:
                        params['shortUnits']=str(int(abs(amount)))
                else:
                    if '-' in str(amount):
                        params['shortUnits']="ALL"
                    else:
                        params['longUnits']="ALL"
                res=v20Positions.PositionClose(accountID=self.AccountID,instrument=pair,data=params)
                self.Results=self.API("PositionClose",request=res)

                if 'orderCreateTransaction' in self.Results:
                    if 'orderCancelTransaction' in self.Results:
                        if Quiet!=True:
                            self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                    else:
                        if Quiet!=True:
                            self.Log.Write("|- Order Confirmation ID: "+self.Results['orderCreateTransaction']['id'])
                elif 'longOrderCreateTransaction' in self.Results:
                    if 'orderCancelTransaction' in self.Results:
                        if Quiet!=True:
                            self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                    else:
                        if Quiet!=True:
                            self.Log.Write("|- Order Confirmation ID: "+self.Results['longOrderCreateTransaction']['id'])
                elif 'shortOrderCreateTransaction' in self.Results:
                    if 'orderCancelTransaction' in self.Results:
                        if Quiet!=True:
                            self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                    else:
                        if Quiet!=True:
                            self.Log.Write("|- Order Confirmation ID: "+self.Results['shortOrderCreateTransaction']['id'])
            else:
                if 'ALL' not in str(amount).upper():
                    # amount is STR, need float for abs()
                    amount=int(amount)
                    if float(amount)>=0:
                        params['units']=str(math.floor(abs(amount)))
                else:
                    if '-' in str(amount):
                        params['shortUnits']="ALL"
                    else:
                        params['longUnits']="ALL"
                res=v20Trades.TradeClose(accountID=self.AccountID,tradeID=ticket,data=params)
                self.Results=self.API("TradeClose",request=res)

                if 'orderCreateTransaction' in self.Results:
                    if 'orderCancelTransaction' in self.Results:
                        if Quiet!=True:
                            self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                    else:
                        if Quiet!=True:
                            self.Log.Write("|- Order Confirmation ID: "+self.Results['orderCreateTransaction']['id'])
                elif 'longOrderCreateTransaction' in self.Results:
                    if 'orderCancelTransaction' in self.Results:
                        if Quiet!=True:
                            self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                    else:
                        if Quiet!=True:
                            self.Log.Write("|- Order Confirmation ID: "+self.Results['longOrderCreateTransaction']['id'])
                elif 'shortOrderCreateTransaction' in self.Results:
                    if 'orderCancelTransaction' in self.Results:
                        if Quiet!=True:
                            self.Log.Write("|- Order CANCELLED: "+self.Results['orderCancelTransaction']['reason'])
                    else:
                        if Quiet!=True:
                            self.Log.Write("|- Order Confirmation ID: "+self.Results['shortOrderCreateTransaction']['id'])
        else:
            self.Log.Error("PlaceOrder","Action is neither BUY nor SELL")

        return self.Results

    # This is mostly a place holder and not used for OANDA as the minimum units
    # is always 1. Minimum cost of a market order is always ask price.

    def GetMinimum(self,**kwargs):
        symbol=kwargs.get('symbol')
        self.SetPipValue(symbol)

        minimum=1
        mincost=self.GetTicker(symbol=symbol)['Ask']
        return minimum,mincost

    # Get an order's details by ticket number. If current ID is not last ID,
    # search and match "orderID" for the completed transaction. order ID will
    # match the placed order. OANDA puts sequwential ID on EVERY action, pending
    # will have separate ID from a fully filled trade.

    def GetOrderDetails(self,**kwargs):
        FinalResults=[]

        ticket=kwargs.get('OrderID')
        res=v20Transactions.TransactionDetails(accountID=self.AccountID,transactionID=ticket)
        self.Results=self.API("OrderDetails",request=res)

        # Check for a "chain" sequence order and find the beginning

        # These elements occur WITH orderID

        # 'tradeReduced' if we reduce a trade size
        # 'tradeClose' if we close a trade altogether

#        if 'tradeClose' in self.Results['transaction']:
#            nid=int(self.Results['transaction']['tradeClose']['tradeID'])
#            if nid<int(ticket):
#                FinalResults.append(self.GetOrderDetails(OrderID=str(nid)))

        if 'transaction' not in self.Results:
            return None

        if 'replacesOrderID' in self.Results['transaction']:
            nid=int(self.Results['transaction']['replacesOrderID'])
            if nid<int(ticket):
                return self.GetOrderDetails(OrderID=str(nid))

        if 'orderID' in self.Results['transaction']:
            nid=int(self.Results['transaction']['orderID'])
            if nid<int(ticket):
                return self.GetOrderDetails(OrderID=str(nid))

        FinalResults.append(self.Results['transaction'])

#        return FinalResults

        tid=int(self.Results['transaction']['id'])
        ltid=int(self.Results['lastTransactionID'])

        # Order is still pending, no details available
        if tid==ltid and 'orderID' not in self.Results['transaction']:
            return None

        sid=tid
        id=tid+1
        done=False
        while not done:
            res=v20Transactions.TransactionDetails(accountID=self.AccountID,transactionID=str(id))
            self.Results=self.API("OrderDetails",request=res)

            # Always update last ID
            ltid=int(self.Results['lastTransactionID'])

            # Checkfor the order ID matching the original ID (tid) of the first
            # order.

            if 'orderID' in self.Results['transaction']:
                if int(self.Results['transaction']['orderID'])==sid:
                    if 'replacedByOrderID' in self.Results['transaction']:
                        FinalResults.append(self.Results['transaction'])
                        sid=int(self.Results['transaction']['replacedByOrderID'])

                        # Intremediary order, needs to be trackd as well
                        res=v20Transactions.TransactionDetails(accountID=self.AccountID,transactionID=str(sid))
                        self.Results=self.API("OrderDetails",request=res)
                        FinalResults.append(self.Results['transaction'])
                    else:
                        FinalResults.append(self.Results['transaction'])
                        return FinalResults

            id+=1
            if id>ltid:
                done=True

        return None

    # Make an orphan order

    def MakeOrphanOrder(self,id,Order):
        orphanLock=JRRsupport.Locker("OliverTwist")

        # Strip Identity

        Order.pop('Identity',None)

        Orphan={}
        Orphan['Status']='Open'
        Orphan['Framework']='oanda'
        Orphan['ID']=id
        Orphan['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        Orphan['Order']=json.dumps(Order)
        Orphan['Class']='Orphan'

        f=Orphan['Framework']
        e=Orphan['Order']['Exchange']
        a=Orphan['Order']['Account']
        nsf=f"{DataDirectory}/OliverTwist/{f}.{e}.{a}.receiver"

        orphanLock.Lock()
        JRRsupport.AppendFile(nsf,json.dumps(Orphan)+'\n')
        orphanLock.Unlock()

    # Create a conditional order and deliver to OliverTwist

    def MakeConditionalOrder(self,id,Order):
        orphanLock=JRRsupport.Locker("OliverTwist")

        resp=Order['Response']
        Order.pop('Response',None)

        # Strip Identity

        Order.pop('Identity',None)

        Conditional={}
        Conditional['Status']='Open'
        Conditional['Framework']='oanda'
        Conditional['ID']=id
        Conditional['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        Conditional['Order']=json.dumps(Order)
        Conditional['Response']=resp
        Conditional['Class']='Conditional'

        f=Orphan['Framework']
        e=Orphan['Order']['Exchange']
        a=Orphan['Order']['Account']
        nsf=f"{DataDirectory}/OliverTwist/{f}.{e}.{a}.receiver"

        orphanLock.Lock()
        JRRsupport.AppendFile(nsf,json.dumps(Conditional)+'\n')
        orphanLock.Unlock()

    # Make ledger entry with every detail.

    def WriteLedger(self,**kwargs):
        Order=kwargs.get('Order')
        Response=kwargs.get('Response')
        IsLog=kwargs.get('Log')
        LedgerDirectory=kwargs.get('LedgerDirectory')

        if 'ID' in Order:
            id=Order['ID']
        if Response!=None:
            if 'orderCreateTransaction' in Response:
                id=Response['orderCreateTransaction']['id']
            elif 'longOrderCreateTransaction' in Response:
                id=Response['longOrderCreateTransaction']['id']
            elif 'shortOrderCreateTransaction' in Response:
                id=Response['shortOrderCreateTransaction']['id']

        detail=self.GetOrderDetails(OrderID=id)

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
            fname=subOrder['Exchange']+'.'+subOrder['Account']+'.'+subOrder['Asset']
            fname=fname.replace('/','').replace('-','').replace(':','').replace(' ','')
            lname=LedgerDirectory+'/'+fname+'.ledger'

            # Strip Identity
            ledger.pop('Identity',None)

            ledgerLock=JRRsupport.Locker(lname)
            ledgerLock.Lock()
            JRRsupport.AppendFile(lname,json.dumps(ledger)+'\n')
            ledgerLock.Unlock()

            if type(IsLog)==bool and IsLog==True:
                self.Log.Write(f"Ledgered: {subOrder['Exchange']}:{id}",stdOut=False)
