#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay, OANDA framework
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import json
import pathlib
import math
from datetime import datetime

import oandapyV20
import oandapyV20.endpoints
import oandapyV20.contrib
import oandapyV20.endpoints.accounts as v20Accounts
import oandapyV20.endpoints.instruments as v20Instruments
import oandapyV20.endpoints.pricing as v20Pricing
import oandapyV20.endpoints.orders as v20Orders
import oandapyV20.endpoints.positions as v20Positions
import oandapyV20.endpoints.trades as v20Trades
import oandapyV20.contrib.requests as v20Requests

import JRRconfig
import JRRlog
import JRRledger
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

    def __init__(self,Exchange,Config,Active):
        self.Exchange=Exchange
        self.Config=Config
        self.Active=Active

        # Extract for convience and readability

        self.AccountID=self.Active['AccountID']
        self.AccessToken=self.Active['API']
        self.Log=self.Active['JRLog']

        self.Notify=True
        self.Sandbox=False
        self.results=None

        # Login to OANDA and pull the market data

        self.Broker=self.Login()
        self.Markets=self.GetMarkets()

    # Register the exchange

    def Login(self,Notify=True,Sandbox=False):
        try:
            self.Broker=oandapyV20.API(access_token=self.AccessToken)
        except Exception as e:
            self.Log.Error("Login",JRRsupport.StopHTMLtags(str(e)))

        self.Notify=Notify
        self.Sandbox=Sandbox

        return self.Broker

    # Get the list of cureent markets allowed to trade.

    def GetMarkets(self):
        markets={}
        res=v20Accounts.AccountInstruments(accountID=self.AccountID)
        self.results=self.API("GetMarkets",request=res)
        for cur in self.results['instruments']:
            asset=cur['name'].upper().replace('_','/')
            markets[asset]=cur
        return markets

    # Get the balance of the account

    def GetBalance(self):
        res=v20Accounts.AccountSummary(accountID=self.AccountID)
        self.results=self.API("GetBalances",request=res)
        return float(self.results['account']['balance'])

    # Get the current positions list

    def GetPositions(self):
        res=v20Positions.OpenPositions(accountID=self.AccountID)
        self.results=self.API("GetPositions",request=res)
        return self.results['positions']

    # Get an individual and specific position. In OANDA, a position may be one
    # or more actual trades.

    # Shorts are negative

    def GetPosition(self,Asset):
        positions=self.GetPositions()
        position=0.0
        if positions!=None:
            for pos in positions:
                asset=pos['instrument'].replace('_','/')
                if Asset.upper()==asset:
                    if 'averagePrice' in pos['long']:
                        position=float(pos['long']['averagePrice'])*float(pos['long']['units'])
                    else:
                        position=-(float(pos['short']['averagePrice']))*float(pos['short']['units'])
                    return position
        return 0

    # Get candlestick (OHLCV) data

    def GetOHLCV(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')
        timeframe=kwargs.get('timeframe')
        limit=str(kwargs.get('limit'))
        params={"granularity":timeframe.upper(), "count":limit }
        candles=[]

        res=v20Instruments.InstrumentsCandles(instrument=symbol,params=params)
        self.results=self.API("GetOHLCV",request=res)
        for cur in self.results['candles']:
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

        res=v20Pricing.PricingInfo(accountID=self.AccountID,params=params)
        self.results=self.API("GetTicker",request=res)

        # Build the forex pair dictionary

        ForexPair={}
        ForexPair['Ask']=round(float(self.results['prices'][0]['asks'][0]['price']),5)
        ForexPair['Bid']=round(float(self.results['prices'][0]['bids'][0]['price']),5)
        ForexPair['Spread']=round(ForexPair['Ask']-ForexPair['Bid'],5)

        return ForexPair

    # Get the order book

    def GetOrderBook(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')

        req=v20Instruments.InstrumentsOrderBook(instrument=symbol,params={})
        self.results=self.API("GetOrderBook",request=req)
        return self.results['orderBook']['buckets']

    # As references in GetPosition, a position may consist ofone or more actual
    # trades. This is NOT the same as an open list of limit orders.

    def GetOpenTrades(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')
        params={"instruments":symbol }

        req=v20Trades.TradesList(accountID=self.AccountID,params=params)
        self.results=self.API("GetOpenTrades",request=req)
        return self.results['trades']

    # Get a list of pending (open) orders.

    def GetOpenOrders(self,**kwargs):
        symbol=kwargs.get('symbol').replace('/','_')

        req=v20Orders.OrdersPending(accountID=self.AccountID)
        self.results=self.API("GetOpenOrders",request=req)

#        if positions!=None:
#            for pos in positions:
#                asset=pos['instrument'].replace('_','/')
#                if Asset.upper()==asset:
#                    if 'averagePrice' in pos['long']:
#                        position=float(pos['long']['averagePrice'])*float(pos['long']['units'])
#                    else:
#                        position=-(float(pos['short']['averagePrice']))*float(pos['short']['units'])
#                    return position


        return self.results['orders']

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
            self.results=self.API("OrderCreate",request=res)
        elif (action=='sell'):
            params={}
            if ticket==None:
                if str(amount).upper()!='ALL':
                    # amount is STR, need float for abs()
                    amount=int(amount)
                    if float(amount)>=0:
                        params['longUnits']=str(math.floor(abs(amount)))
                    else:
                        params['shortUnits']=str(math.floor(abs(amount)))
                else:
                    params['longUnits']="ALL"
                res=v20Positions.PositionClose(accountID=self.AccountID,instrument=pair,data=params)
                self.results=self.API("PositionClose",request=res)
            else:
                if str(amount).upper()!='ALL':
                    # amount is STR, need float for abs()
                    amount=int(amount)
                    if float(amount)>=0:
                        params['units']=str(math.floor(abs(amount)))
                else:
                    params['units']="ALL"
                res=v20Trades.TradeClose(accountID=self.AccountID,tradeID=ticket,data=params)
                self.results=self.API("TradeClose",request=res)
        else:
            self.Log.Error("PlaceOrder","Action is neither BUY nor SELL")

        return self.results

    # Handle the retry functionality and send the request to the broker.

    def API(self,function,**kwargs):
        req=kwargs.get('request')
        retry=0

        # Sanity check
        if 'Retry' in self.Active:
            RetryLimit=int(self.Active['Retry'])
        else:
            RetryLimit=3

        done=False
        while not done:
            try:
                self.results=self.Broker.request(req)
            except Exception as e:
                if retry<RetryLimit:
                    self.Log.Error(function,JRRsupport.StopHTMLtags(str(e)))
                else:
                    self.Log.Write(function+' Retrying ('+str(retry+1)+'), '+JRRsupport.StopHTMLtags(str(e)))
            else:
                done=True
            retry+=1

        return self.results
