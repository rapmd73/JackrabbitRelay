#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay, MIMIC framework
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# This is a full virtual exchange frameork designed to pull and use a real broker/exchange as a data source
# to mimic live trading is a completely virtual environment. All aspects of a real broker/exchange will be
# implemented in such a way that tis process is expected to provide meaningful results comparable to a demo
# account.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import random
import atexit
import math
import signal
import json
import time
from datetime import datetime

import JRRsupport
import JackrabbitRelay as JRR

class mimic:
    # Define the special variables for this object. ALL variable WITHIN
    # the class must have the prefix of self. self defines the internal
    # mechanics that help isolate variables.

    # Initialize the object and automatically get everything set up

    # Account ID and bearer token will be in Active. Logging framework and
    # identity are embedded here as well.

    # This framework doesn't need an API/Secret methodology. It must emulate both cryptocurrency exchanges
    # and forex brokers reasonable well.

    # Special situation:

    #   This class must exclusive lock at init to prevent corruption of simulated wallet. If thos were a
    #   standalone server, like locker, thn the method of usage would beserialized.Two processes can NOT
    #   manipulate a wallet at the same time without corrupting the position table and balance. The lock is
    #   placed in init and released at exit.

    def __init__(self,Exchange,Config,Active,DataDirectory=None):
        self.Version="0.0.0.1.770"

        self.StableCoinUSD=['USDT','USDC','BUSD','UST','DAI','FRAX','TUSD', \
                'USDP','LUSD','USDN','HUSD','FEI','TRIBE','RSR','OUSD','XSGD', \
                'GUSD','USDX','SUSD','EURS','CUSD','USD']

        self.DefaultFeeRate=0.0073  # 0.73%

        self.DataDirectory=DataDirectory
        self.Storage=self.DataDirectory+'/Mimic'
        JRRsupport.mkdir(self.Storage)

        self.Framework=None
        self.Config=Config
        self.Active=Active

        # Convience for imternal use
        self.DataExchange=self.Active['DataExchange']
        self.DataAccount=self.Active['DataAccount']

        # Extract for convience and readability

        self.Log=self.Active['JRLog']

        self.Notify=True
        self.Results=None

        # This is where all trades for a given mimic account are tracked in relation to the data source
        self.history=f"{self.Storage}/{self.Active['Account']}.history"
        self.walletFile=f"{self.Storage}/{self.Active['Account']}.wallet"
        self.walletLock=JRRsupport.Locker(self.walletFile,ID=self.walletFile)
        self.Wallet=None

        # Lock it up and set the exit approach

        atexit.register(self.CleanUp)
        self.walletLock.Lock()

        # Login to broker/exchange and pull the market data from the data source

        self.Broker=self.Login()

        # Timeframes must be pulld from the data sorce broker/exchange dynamicly

        self.timeframes=self.Broker.Broker.timeframes

        # Mimic the markets

        self.Markets=self.Broker.Broker.Markets

        if not os.path.exists(self.walletFile):
            self.GetWallet()

    # Unlock the exclusive hold at exit of program.

    def CleanUp(self):
        self.walletLock.Unlock()

    # Register the exchange

    def Login(self,Notify=True,Sandbox=False):
        # Login into broker/exchange we are going to mimic.
        self.Broker=JRR.JackrabbitRelay(exchange=self.DataExchange,account=self.DataAccount)

        self.Framework=self.Broker.Framework
        self.Notify=Notify
        self.Sandbox=Sandbox

        # Copy ratelimits from data source

        self.Active['RateLimit']=self.Broker.Active['RateLimit']
        if 'Retry' in self.Active:
            self.Active['Retry']=self.Broker.Active['Retry']
        else:
            self.Active['Retry']=3

        return self.Broker

    # Get the list of cureent markets allowed to trade.

    def GetMarkets(self):
        self.Markets=self.Broker.Broker.GetMarkets()

    # Get the balance of the account. kwargs is needed for conformity with other
    # exchanges/brokers even though it will never be used by OANDA.

    def GetBalance(self,**kwargs):
        base=kwargs.get('Base')

        self.GetWallet()

        if base==None:
            return self.Wallet['Wallet']
        else:
            base=base.upper()
            if base in self.Wallet['Wallet']:
                return self.Wallet['Wallet'][base]
            else:
                return 0

    # Get general account summary.
    # Need to track:
    #   Balance
    #   Wallet amount
    #   If amount<0, short otherwise long direction
    #   If quote currency <0, account liquidated

    # Order ID: f"{time.time()*10000000:.0f}"

    # Cryptocurrency tracking is only the amount of the asset. Price is not recorded by the cryptocurrency
    # exchange within the wallet. Crypto value is wallet amount * current ticker, no position tracking.

    def GetWallet(self,**kwargs):
        # if wallet file not exists, set up defaults
        if not os.path.exists(self.walletFile):
            # Get list of valid quote currencies
            qList=[]
            for pair in self.Markets.keys():
                if ':' in pair:
                    quote=pair.split(':')[1]
                    if '-' in quote:
                        quote=quote.split('-')[0]
                else:
                    quote=pair.split('/')[1]
                if quote not in qList:
                    qList.append(quote)

            self.Wallet={}
            # A disabled account was liquidated.
            self.Wallet['Enabled']='Y'
            self.Wallet['Fees']=0

            self.Wallet['Wallet']={}
            # Fund all quote pairs on the exchange
            for coin in qList:
                if 'InitialBalance' in self.Active:
                    self.Wallet['Wallet'][coin]=float(self.Active['InitialBalance'])
                else:
                    self.Wallet['Wallet'][coin]=10000

            self.PutWallet()
        else:
            self.Wallet=json.loads(JRRsupport.ReadFile(self.walletFile).strip().split('\n')[0])

        return self.Wallet

    def PutWallet(self,**kwargs):
        JRRsupport.WriteFile(self.walletFile,json.dumps(self.Wallet)+'\n')

    # Get candlestick (OHLCV) data
    # Reoccuring theme...
    # self.Broker is Mimic
    # self.Broker.Broker is layer under Mimic, or the exchange Mimic is shadowing...

    def GetOHLCV(self,**kwargs):
        return self.Broker.Broker.GetOHLCV(**kwargs)

    # Get the current positions list or get an individual and specific position.

    def GetPositions(self,**kwargs):
        return self.Broker.Broker.GetPositions(**kwargs)

    # Get the bid/ask values of the curent ticker

    def GetTicker(self,**kwargs):
        return self.Broker.Broker.GetTicker(**kwargs)

    # Get the order book

    def GetOrderBook(self,**kwargs):
        return self.Broker.Broker.GetOrderBook(**kwargs)

    # To be decided. How advanced do we want this to get? This has a critical point in cryptocurrencies, but may
    # have implications in forex as well.

    # Minimum amount is always 1 (0.001 for BTC).
    # Minimum cost of a market order is always ask price.

    def GetMinimum(self,**kwargs):
        return self.Broker.Broker.GetMinimum(**kwargs)

    # Get a list of pending (open) orders. For Mimic, limit opders are just market orders.
    # If Mimic ever develops into a full standalone exchange, this WILL be a major problem.
    # ... I really despise limit orders ...

    def GetOpenOrders(self,**kwargs):
        return self.GetOpenTrades(**kwargs)

    # List of actual trades from Summary['OpenTrades']

    def GetOpenTrades(self,**kwargs):
        pass

    # Manage the wallet. This is where the dirty side of Mimic takes place.

    def UpdateWallet(self,action,asset,amount,price,fee_rate=0):
        # if the account has already been disabled (liquidated), then don't waste time here
        if self.Wallet['Enabled']=='N':
            return 'Account Disabled From Liquidated!'

        # action is assumed to be only lowercase at this point.
        # Split the asset pair into base and quote currencies
        base,quote=asset.split('/')

        # Time to F* with the trader. Simulate dust.
        # It is very rare that an order is filled exactly as requested.
        rpct=random.uniform(0, 1)
        mda=amount*0.0013
        dust=abs(mda)*rpct
        if amount<0:    # short
            actualAmount=amount+dust
        else:           # long
            actualAmount=amount-dust

        # Need to recheck minimum values

        ticker=self.Broker.GetTicker(symbol=asset)
        if actualAmount<0:
            actualPrice=min(ticker['Bid'],ticker['Ask'])-ticker['Spread']   # Short
        else:
            actualPrice=max(ticker['Bid'],ticker['Ask'])+ticker['Spread']   # Long

        if action=='buy':
            # Calculate the total cost for buying the asset including fees
            total_cost=abs(actualAmount) * actualPrice * (1 + fee_rate)
            # Check if the wallet has enough balance for the purchase including fees
            if quote in self.Wallet['Wallet'] and self.Wallet['Wallet'][quote] >= total_cost:
                # Deduct the total cost including fees from the quote currency balance
                self.Wallet['Wallet'][quote]-=total_cost
                # Add the appropriate amount of the base currency to the base currency wallet.
                # Using negatives as shorts allows position flipping by default.
                if base in self.Wallet['Wallet']:
                    self.Wallet['Wallet'][base]+=actualAmount
                else:
                    self.Wallet['Wallet'][base]=actualAmount  # Initialize the base currency wallet if not present
                # Update fee balance
                fee=round(abs(actualAmount) * actualPrice * fee_rate,8)
                if 'Fees' in self.Wallet['Wallet']:
                    self.Wallet['Fees']+=fee
                else:
                    self.Wallet['Fees']=fee  # Initialize fee balance if not present
                # Update successful
                order={}
                order['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
                order['ID']=f"{time.time()*10000000:.0f}"
                order['Action']=action
                order['Asset']=asset
                order[base]=self.Wallet['Wallet'][base]
                order[quote]=self.Wallet['Wallet'][quote]
                order['Amount']=round(actualAmount,8)
                order['Price']=round(actualPrice,8)
                order['Fee']=round(fee,8)
                # Remove from allet
                if self.Wallet['Wallet'][base]==0.0:
                    self.Wallet['Wallet'].pop(base,None)
                return order
            else:
                # Not enough balance, account liquidated.
                self.Wallet['Enabled']='N'
                return 'Account Liquidated!'
        elif action=='sell':
            # Check if the base currency is present in the base currency wallet and the amount to sell is available
            if base in self.Wallet['Wallet'] and abs(self.Wallet['Wallet'][base])>=abs(actualAmount):
                # Calculate the total proceeds from selling the asset after deducting fees
                total_proceeds=abs(actualAmount) * actualPrice * (1 - fee_rate)
                # Add the total proceeds minus fees to the quote currency balance
                if quote in self.Wallet['Wallet']:
                    self.Wallet['Wallet'][quote]+=total_proceeds
                else:
                    self.Wallet['Wallet'][quote]=total_proceeds  # Initialize quote currency balance if not present
                # Subtract the appropriate amount of the base currency from the base currency wallet
                if actualAmount<0:    # handle shorting
                    if self.Wallet['Wallet'][base]<0:
                        self.Wallet['Wallet'][base]-=actualAmount
                    else:
                        self.Wallet['Wallet'][base]+=actualAmount
                else:
                    if self.Wallet['Wallet'][base]<0:
                        self.Wallet['Wallet'][base]+=actualAmount
                    else:
                        self.Wallet['Wallet'][base]-=actualAmount
                # Update fee balance
                fee = round(abs(actualAmount) * actualPrice * fee_rate,8)
                if 'Fees' in self.Wallet['Wallet']:
                    self.Wallet['Fees']+=fee
                else:
                    self.Wallet['Fees']=fee  # Initialize fee balance if not present
                # Update successful
                order={}
                order['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
                order['ID']=f"{time.time()*10000000:.0f}"
                order['Action']=action
                order['Asset']=asset
                order[base]=self.Wallet['Wallet'][base]
                order[quote]=self.Wallet['Wallet'][quote]
                order['Amount']=round(actualAmount,8)
                order['Price']=round(actualPrice,8)
                order['Fee']=round(fee,8)
                # Remove from allet
                if self.Wallet['Wallet'][base]==0.0:
                    self.Wallet['Wallet'].pop(base,None)
                return order
            else:
                # Not enough balance, but account is not liquidated. Need to cross analyze this on shorting.
                #self.Wallet['Enabled']='N'
                return 'Not enough balance!'
        else:   # Should NEVER happen.
            return 'Invalid action!'

    # Welcome to the nightmare: placing and maintaining orders.

    # From the stand pint of Mimic, this is the most tedious part of the entire framework. There are a lot of
    # moving parts here, including the layout of Mimic itself. Choosing whether to follow the crypto standard vs
    # the forex standard is the most pivotal of the process. Where forex has such refined demo accounts already,
    # I am inclined to focus on a crypto direction. I am leaning towards the more understandable format of forx
    # though for the actual implementation.

    # PlaceOrder(exchange, Active, pair=pair, orderType=orderType,
    #     action=action, amount=amount, close=close, ReduceOnly=ReduceOnly,
    #     LedgerNote=ledgerNote)

    # CRITICAL:

    #   When subtracting amounts for the wallet, the positional tracking system MUST substract from the OLDEST
    #   (first in/first out) position in the list at the CURRENT (ticker) market value. Extensive research in
    #   this shows that FIFO is THE account standard practiced globally.

    #   Cryprocurreny selling never selld by ID, only AMOUNT

    def PlaceOrder(self,**kwargs):
        pair=kwargs.get('pair')
        m=kwargs.get('orderType').lower()
        action=kwargs.get('action').lower()
        price=kwargs.get('price')
        ln=kwargs.get('LedgerNote',None)
        # Shorts are stored as negative numbers
        amount=float(kwargs.get('amount'))
        ro=kwargs.get('ReduceOnly',False)
        Quiet=kwargs.get('Quiet',False)

        # Split the asset pair into base and quote currencies
        base,quote=pair.split('/')

        # simulate a real order
        order={}
        order['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        order['ID']=f"{time.time()*10000000:.0f}"
        order['Action']=action
        order['Asset']=pair
        order['Amount']=round(amount,8)
        order['Price']=round(price,8)

        self.GetWallet()

        # Simulate order of successful transaction
        Fee=None
        if 'Fee' in self.Active:
            if '%' in self.Active['Fee']:
                Fee=float(self.Active['Fee'].replace('%','').strip())/100
            else:
                Fee=float(self.Active['Fee'])
        else:
            Fee=self.DefaultFeeRate

        # Handle ReduceOnly
        if ro==True and action=='sell':
            amount=self.Wallet['Wallet'][base]

        result=self.UpdateWallet(action,pair,amount,price,Fee)

        if 'ID' in result:
            JRRsupport.AppendFile(self.history,json.dumps(result)+'\n')
        self.PutWallet()
        if 'ID' in result and result['ID']!=None:
            # Required because most crypto exchanges don't retain order details after a certain length of time.
            # The details will be embedded into the response. This is CRITICAL for getting the strike price of
            # market orders.
            order['Details']=self.GetOrderDetails(id=result['ID'],symbol=pair)
            if Quiet!=True:
                self.Log.Write("|- Order Confirmation ID: "+result['ID'])

            #JRRledger.WriteLedger(pair, m, action, amount, price, order, ln)
            return order
        else: # We have an error
            self.Log.Error("PlaceOrder",result)

    # Get the details of the completed order. This will reaD from the positions list.

    def GetOrderDetails(self,**kwargs):
        if os.path.exists(self.history):
            id=kwargs.get('id')
            pair=kwargs.get('pair',None)
            cf=open(self.history,'r')
            # We need to go line by line as history file may be too large to load
            for line in cf.readlines():
                line=line.strip()
                if line=='' or (line[0]!='{' and line[-1]!='}'):
                    continue
                try:    # skip non-JSON lines
                    order=json.loads(line)
                except:
                    continue
                if (order['ID']==id and pair!=None and order['Asset']==pair) \
                or (order['ID']==id and pair==None):
                    cf.close()
                    return order
            cf.close()

        return None

    # Make an orphan order. This is a dead paaathru as limit orders are market orders

    def MakeOrphanOrder(self,id,Order):
        pass

    # Create a conditional order and deliver to OliverTwist

    def MakeConditionalOrder(self,id,Order):
        orphanLock=JRRsupport.Locker("OliverTwist")

        resp=Order['Response']
        Order.pop('Response',None)

        # Strip Identity

        Order.pop('Identity',None)

        Conditional={}
        Conditional['Status']='Open'
        Conditional['Framework']='mimic'
        Conditional['ID']=id
        Conditional['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        Conditional['Order']=json.dumps(Order)
        Conditional['Response']=resp
        Conditional['Class']='Conditional'

        nsf=f"{self.DataDirectory}/OliverTwist.Receiver"

        orphanLock.Lock()
        JRRsupport.AppendFile(nsf,json.dumps(Conditional)+'\n')
        orphanLock.Unlock()

    # Make ledger entry with every detail.

    def WriteLedger(self,**kwargs):
        pass
