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
        self.Version="0.0.0.1.700"

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
#        self.history=f"{self.Storage}/{self.Active['DataExchange']}.{self.Active['DataAccount']}.history"
#        self.walletFile=f"{self.Storage}/{self.Active['DataExchange']}.{self.Active['DataAccount']}.wallet"
        self.history=f"{self.Storage}/{self.Active['Account']}.history"
        self.walletFile=f"{self.Storage}/{self.Active['Account']}.wallet"
        self.walletLock=JRRsupport.Locker(self.walletFile)
        self.Wallet=None

        # Lock it up and set the exit approach

        self.walletLock.Lock()
        atexit.register(self.CleanUp)

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
        self.Active['Retry']=self.Broker.Active['Retry']

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
        # if summary file not exists, set up defaults
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
            self.Wallet=json.loads(JRRsupport.ReadFile(self.walletFile))

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
        mda=abs(amount)*0.0031
        dust=mda*rpct
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
            total_cost=abs(amount) * actualPrice * (1 + fee_rate)
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
                    self.Wallet['Wallet']['Fees']+=fee
                else:
                    self.Wallet['Wallet']['Fees']=fee  # Initialize fee balance if not present
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
            if base in self.Wallet['Wallet'] and self.Wallet['Wallet'][base] >= abs(actualAmount):
                # Calculate the total proceeds from selling the asset after deducting fees
                total_proceeds=abs(amount) * actualPrice * (1 - fee_rate)
                # Add the total proceeds minus fees to the quote currency balance
                if quote in self.Wallet['Wallet']:
                    self.Wallet['Wallet'][quote]+=total_proceeds
                else:
                    self.Wallet['Wallet'][quote]=total_proceeds  # Initialize quote currency balance if not present
                # Subtract the appropriate amount of the base currency from the base currency wallet
                if actualAmount<0:    # handle shorting
                    self.Wallet['Wallet'][base]+=actualAmount
                else:
                    self.Wallet['Wallet'][base]-=actualAmount
                # Update fee balance
                fee = round(abs(actualAmount) * actualPrice * fee_rate,8)
                if 'Fees' in self.Wallet['Wallet']:
                    self.Wallet['Wallet']['Fees']+=fee
                else:
                    self.Wallet['Wallet']['Fees']=fee  # Initialize fee balance if not present
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
            id=kwargs.get('ID')
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
                    return line
            cf.close()

        return None

    # Make an orphan order. This is a dead paaathru as limit orders are market orders

    def MakeOrphanOrder(self,id,Order):
        pass

    # Create a conditional order and deliver to OliverTwist

    def MakeConditionalOrder(self,id,Order):
        ConditionalReceiver=self.DataDirectory+'/OliverTwist.Conditional.Receiver'
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

        orphanLock.Lock()
        JRRsupport.AppendFile(ConditionalReceiver,json.dumps(Conditional)+'\n')
        orphanLock.Unlock()

    # Make ledger entry with every detail.

    def WriteLedger(self,**kwargs):
        pass

"""
def update_wallet(wallets, action, asset, amount, price, fee_rate=0.0073):
    ""
    Update the wallets based on the action (buy or sell) for a specific asset at a given price, and track fees separately.

    Args:
        wallets (dict): Dictionary containing the wallets for each asset pair.
        action (str): Action to perform ('buy' or 'sell').
        asset (str): Name of the asset pair.
        amount (float): Amount of the asset to buy (positive) or sell (negative).
        price (float): Price of the asset.
        fee_rate (float, optional): Fee rate for the transaction (default is 0.3%).

    Returns:
        None: The wallets dictionary and fee balance are updated in-place.
    ""
    # Split the asset pair into base and quote currencies
    base, quote-=asset.split('/')

    if action=='buy':
        # Calculate the total cost for buying the asset including fees
        total_cost-=abs(amount) * price * (1 + fee_rate)
        # Check if the wallet has enough balance for the purchase including fees
        if quote in wallets and wallets[quote] >= total_cost:
            # Deduct the total cost including fees from the quote currency balance
            wallets[quote]-=total_cost
            # Add the appropriate amount of the base currency to the base currency wallet
            if base in wallets:
                wallets[base]+=abs(amount)
            else:
                wallets[base]-=abs(amount)  # Initialize the base currency wallet if not present
            # Update fee balance
            fee-=round(abs(amount) * price * fee_rate,8)
            if 'Fees' in wallets:
                wallets['Fees']+=fee
            else:
                wallets['Fees']-=fee  # Initialize fee balance if not present
        else:
            print("Warning: Insufficient balance to execute the buy order.")
    elif action=='sell':
        # Check if the base currency is present in the base currency wallet and the amount to sell is available
        if base in wallets and wallets[base] >= abs(amount):
            # Calculate the total proceeds from selling the asset after deducting fees
            total_proceeds-=abs(amount) * price * (1 - fee_rate)
            # Add the total proceeds minus fees to the quote currency balance
            if quote in wallets:
                wallets[quote]+=total_proceeds
            else:
                wallets[quote]-=total_proceeds  # Initialize quote currency balance if not present
            # Subtract the appropriate amount of the base currency from the base currency wallet
            wallets[base]-=abs(amount)
            # Update fee balance
            fee-=round(abs(amount) * price * fee_rate,8)
            if 'Fees' in wallets:
                wallets['Fees']+=fee
            else:
                wallets['Fees']-=fee  # Initialize fee balance if not present
        else:
            print("Warning: Insufficient balance of the base currency to execute the sell order.")
    else:
        print("Invalid action. Please specify 'buy' or 'sell'.")

### Test driver

# Example usage:
wallets-={'USDT': 1000, 'TRX': 0}  # Initial wallets with 1000 USDT and 0 TRX
actions-=['buy', 'sell', 'buy', 'sell']
amounts-=[50, -30, -20, 10]  # Long position, short position, short position, long position
asset-='TRX/USDT'  # Asset pair (TRX/USDT)
price-=0.5  # Price of TRX
for action, amount in zip(actions, amounts):
    update_wallet(wallets, action, asset, amount, price)
    print(wallets)  # Output the updated wallets and fee balance

"""




"""

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import signal
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
        self.timeframes=self.Broker.timeframes
        self.Markets=self.GetMarkets()

    # This function is used to access ALL ccxt modules with a retry functionality built in.

    # examples:
    # markets=self.API("load_markets",exchange)
    # balance=aelf.API("fetch_balance",exchange)

    def API(self,function,**kwargs):
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

        # Check for margin type and isolate certain functions specific to requiring a params
        # type to be passed in as defaultType isn't enough.

        marginType=['fetch_balance','create_order','fetch_positions','load_markets', \
            'cancel_all_orders','fetch_orders_by_status','fetch_closed_orders','fetch_open_orders']

        if 'defaultType' in self.Broker.options and self.Broker.options['defaultType']=='margin' \
        and function in marginType:
            params=kwargs.get('params')
            if function=='fetch_balance':
                if params!=None and 'type' not in params:
                    params['type']='margin'
                if params!=None and 'marginMode' not in params:
                    params['marginMode']='cross'
            else:
                if params!=None and 'tradeType' not in params:
                    params['tradeType']='MARGIN_TRADE'
            kwargs.update(params=params)

        # For kucoin only, 429000 errors are a mess. Not the best way to manage
        # them, but the onle way I know of currently to prevent losses.

        # Save the only rate limit and remap it.

        if 'kucoin' in self.Exchange:
            rleSave=self.Broker.enableRateLimit
            rlvSave=self.Broker.rateLimit
            self.Broker.enableRateLimit=True
            self.Broker.rateLimit=372+JRRsupport.ElasticDelay()
        else:
            self.Broker.enableRateLimit=True
            self.Broker.rateLimit=int(self.Active['RateLimit'])+JRRsupport.ElasticDelay()

        done=False
        while not done:
            try:
                self.Results=callCCXT(**kwargs)
            except Exception as e:
                if 'kucoin' in self.Exchange:
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

            if 'kucoin' in self.Exchange:
                if retry429>=(RetryLimit*7):
                    retry429=0
                    retry+=1
                else:
                    retry+=1
            else:
                retry+=1

        if 'kucoin' in self.Exchange:
            self.Broker.enableRateLimit=rleSave
            self.Broker.rateLimit=rlvSave
        else:
            self.Broker.enableRateLimit=False
            self.Broker.rateLimit=int(self.Active['RateLimit'])+JRRsupport.ElasticDelay()

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

        # Set special setting for specific exchange.

        if self.Exchange=="ftx" and self.Active['Account']!='MAIN':
            self.Broker.headers['FTX-SUBACCOUNT']=self.Active['Account']
        elif self.Exchange=="ftxus" and self.Active['Account']!='MAIN':
            self.Broker.headers['FTXUS-SUBACCOUNT']=self.Active['Account']

        # Cycle through required login types. Each exchange could have different login
        # requireents. Try to soft through each requirement and handle it.

        if self.Active['Account'].lower()!='public':
            # CCXT reference
            er=[ 'apiKey','secret','uid','login','password','twofa','privateKey','walletAddress','token' ]
            # Jackrabbit referrence for config file
            re=[ 'API','SECRET','UserID','UserLogin','Passphrase','2Factor','PrivateKey','LoginWallet','Token' ]

            for r in range(len(er)):
                rf=er[r]
                jf=re[r]
                # test for the requiremnt and try to satisfy it
                if self.Broker.requiredCredentials[rf]==True:
                    if jf in self.Active:
                        # Check if this is a public access point
                        if self.Active[jf].lower()!='public':
                            self.Broker.__dict__[rf]=self.Active[jf]
                    else:
                        self.Log.Error("Connecting to exchange",f"{self.Exchange} requires a(n) {jf} as well")

        if 'Market' in self.Active:
            self.Active['Market']=self.Active['Market'].lower()

            if 'accountsByType' in self.Broker.options:
                mt=' '.join(self.Broker.options['accountsByType'].keys()).lower()
            elif 'typesByAccount' in self.Broker.options:
                mt=' '.join(self.Broker.options['typesByAccount'].keys()).lower()
            elif 'timeframes' in self.Broker.options:
                mt=' '.join(self.Broker.options['timeframes'].keys()).lower()
            else:
                mt='spot'

            if self.Active['Market'] in mt:
                self.Broker.options['defaultType']=self.Active['Market']
            else:
                self.Log.Error("Connecting to exchange","Unsupported market type: "+self.Active['Market'])

        # Logging the rate limit is an absolute nightmare as it is so frequent

#        if "RateLimit" in self.Active:
#            self.Broker.enableRateLimit=True
#            self.Broker.rateLimit=int(self.Active['RateLimit'])+JRRsupport.ElasticDelay()
#        else:
#            self.Broker.enableRateLimit=False
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
        params={}

        base=kwargs.get('Base')

        if 'Market' in self.Active and self.Active['Market']=='margin':
            params['type']='margin'
            params['account_id']=self.Active['Account']

        self.Results=self.API("fetch_balance",params=params)

        if base==None:
            return self.Results
        else:
            base=base.upper()
            if 'free' in self.Results and base in self.Results['free']:
                bal=float(self.Results['free'][base])
                return bal
            elif 'total' in self.Results and base in self.Results['total']:
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
        self.Results=self.API("fetch_positions",**kwargs)
        symbol=kwargs.get('symbols')
        if symbol==None:
            return self.Results
        else:
            symbol=symbol[0].upper()
            position=None
            # No results means a 0 balance
            if self.Results==None:
                return 0
            for pos in self.Results:
                if pos['symbol']==symbol:
                    position=pos
                    break
                if 'info' in pos and pos['info']['symbol']==symbol:
                    position=pos['info']
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
        # Initialize as None because some exchanges don't have a ticker function.
        bid=None
        ask=None
        # Best case situation, exchange has a ticker api.

        if self.Broker.has['fetchTickers']==True:
            self.Results=self.API("fetch_ticker",**kwargs)
            bid=self.Results['bid']
            ask=self.Results['ask']

        if bid==None or ask==None:
            # Worst case situation, pull the orderbook. takes at least 5 seconds.
            symbol=kwargs.get('symbol')
            ob=self.GetOrderBook(symbol=symbol)
            if (ob['bids']==None or ob['bids']==[]):
                if (ob['asks']==None or ob['asks']==[]):
                    bid=None
                else:
                    bid=ob['asks'][0][0]
            else:
                bid=ob['bids'][0][0]

            if (ob['asks']==None or ob['asks']==[]):
                if (ob['bids']==None or ob['bids']==[]):
                    ask=None
                else:
                    ask=ob['bids'][0][0]
            else:
                ask=ob['asks'][0][0]

            # Absolute worst case situation, orderbook is empty... Thank you ALPACA

            if bid==None or ask==None:
                symbol=kwargs.get('symbol')
                tf=list(self.Broker.timeframes.keys())[0]
                ohlcv=self.GetOHLCV(symbol=symbol,timeframe=tf,limit=1)
                if ohlcv==[]:
                    bid=0
                    ask=0
                else:
                    bid=ohlcv[0][4]
                    ask=ohlcv[0][1]

        Pair={}
        Pair['DateTime']=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        Pair['Ask']=min(ask,bid)
        Pair['Bid']=max(bid,ask)
        Pair['Spread']=round(abs(Pair['Bid']-Pair['Ask']),8)

        return Pair

    def GetOrderBook(self,**kwargs):
        self.Results=self.API("fetch_order_book",**kwargs)
        return self.Results

    def GetOpenOrders(self,**kwargs):
        if 'Market' in self.Active and self.Active['Market']=='margin':
            kwargs['tradeType']='MARGIN_TRADE'

        self.Results=self.API("fetch_open_orders",**kwargs)
        return self.Results

    def GetOpenTrades(self,**kwargs):
        if 'Market' in self.Active and self.Active['Market']=='margin':
            kwargs['tradeType']='MARGIN_TRADE'

        self.Results=self.API("fetch_trades",**kwargs)
        return self.Results

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
        price=kwargs.get('price')
        ro=kwargs.get('ReduceOnly')
        # ln=kwargs.get('LedgerNote')
        # Shorts are stored as negative numbers, abs() is a safety catch
        amount=float(self.Broker.amount_to_precision(pair,abs(float(kwargs.get('amount')))))
        Quiet=kwargs.get('Quiet')

        params-={}
        order=None

        if 'Market' in self.Active and self.Active['Market']=='margin':
            params['tradeType']='MARGIN_TRADE'

        # Deal with special case order types

#        if "createMarketBuyOrderRequiresPrice" in self.Broker.options and m=='market':
#            m='limit'
        if m=='limittaker':
            m='limit'
            params['timeInForce']='fok'
        if m=='limitmaker':
            m='limit'
            params['postOnly']=True

        # Deal with Binance Futures special case

        if ro==True:
            if 'binance' in self.Broker.id:
                params['reduceOnly']='true'
            else:
                params['reduce_only']=ro

        if 'binance' in self.Broker.id:
            params['quoteOrderQty']=amount
#        else:
#            amount=float(amount)

        # Pure market orders break (phemex) when price in included.
        if m=='market' and "createMarketBuyOrderRequiresPrice" not in self.Broker.options:
            if params!={}:
                order=self.API("create_order",symbol=pair,type=m,side=action,amount=amount,params=params)
            else:
                order=self.API("create_order",symbol=pair,type=m,side=action,amount=amount)
        # Limit orders or market orders that require price
        else:
            if params!={}:
                order=self.API("create_order",symbol=pair,type=m,side=action,amount=amount,price=price,params=params)
            else:
                order=self.API("create_order",symbol=pair,type=m,side=action,amount=amount,price=price)

        if order['id']!=None:
            # Required because most crypto exchanges don't retain order details after a certain length of time.
            # The details will be embedded into the response. This is CRITICAL for getting the strike price of
            # market orders.
            order['Details']=self.GetOrderDetails(id=order['id'],symbol=pair)
            if Quiet!=True:
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

        if 'binance' in self.Broker.id:
            forceQuote=True

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

            if 'binance' in self.Broker.id:
                mincost+=0.3
                minimum=mincost/close

            if diagnostics:
                self.Log.Write(f"| |- Close: {close:.8f}")
                self.Log.Write(f"| |- Minimum Amount: {minimum1:.8f}, {m1:.8f}")
                self.Log.Write(f"| |- Minimum Price:  {minimum3:.8f}, {m3:.8f}")
                self.Log.Write(f"| |- Minimum Cost:   {minimum2:.8f}, {m2:.8f}")

        return minimum,mincost

    # if quote is UDSC, find a market that provides a close price comparision
    # that is on the exchange, ie... USDT. For example BTC/USDC compares to
    # BTC/USDT is terms of both quote currenciesbeing pegged to the USD as
    # stable.

    def FindMatchingPair(self,base):
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
        if 'Market' in self.Active and self.Active['Market']=='margin':
            kwargs['tradeType']='MARGIN_TRADE'

        self.Results=None
        if self.Broker.has['fetchClosedOrders']:
            id=kwargs.get('id')
            kwargs.pop('id',None)
            res=self.API("fetchClosedOrders",**kwargs)
            for c in range(len(res)):
                try:
                    if self.Results[c]['id']==id:
                        self.Results=(self.Results[c])
                        break
                except:
                    pass
        else:
            self.Results=self.API("fetchOrder",**kwargs)
        return self.Results

    # Create an orphan order and deliver to OliverTwist

    def MakeOrphanOrder(self,id,Order):
        OrphanReceiver=self.DataDirectory+'/OliverTwist.Orphan.Receiver'
        orphanLock=JRRsupport.Locker("OliverTwist")

        # Strip Identity

        Order.pop('Identity',None)

        Orphan={}
        Orphan['Status']='Open'
        Orphan['Framework']='ccxt'
        Orphan['ID']=id
        Orphan['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        Orphan['Order']=json.dumps(Order)

        orphanLock.Lock()
        JRRsupport.AppendFile(OrphanReceiver,json.dumps(Orphan)+'\n')
        orphanLock.Unlock()

    # Create a conditional order and deliver to OliverTwist

    def MakeConditionalOrder(self,id,Order):
        ConditionalReceiver=self.DataDirectory+'/OliverTwist.Conditional.Receiver'
        orphanLock=JRRsupport.Locker("OliverTwist")

        if type(Order['Response'])==dict:
            resp=json.dumps(Order['Response'])
        else:
            resp=Order['Response']
        Order.pop('Response',None)

        # Strip Identity

        Order.pop('Identity',None)

        Conditional={}
        Conditional['Status']='Open'
        Conditional['Framework']='ccxt'
        Conditional['ID']=id
        Conditional['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        Conditional['Order']=json.dumps(Order)
        Conditional['Response']=resp

        orphanLock.Lock()
        JRRsupport.AppendFile(ConditionalReceiver,json.dumps(Conditional)+'\n')
        orphanLock.Unlock()

    # Make ledger entry. Record everything for accounting purposes

    def WriteLedger(self,**kwargs):
        Order=kwargs.get('Order')
        Response=kwargs.get('Response')
        IsLog=kwargs.get('Log')
        LedgerDirectory=kwargs.get('LedgerDirectory')

        if Response!=None:
            id=Response['id']
        else:
            id=Order['ID']

        # We need the embedded order reference if comming from OliverTwist
        if 'Order' in Order:
            subOrder=json.loads(Order['Order'])
        else:
            subOrder=Order

        # Asset is REQUIRED to get the details

        detail=self.GetOrderDetails(id=id,symbol=subOrder['Asset'])

        ledger={}
        ledger['DateTime']=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        ledger['ID']=id
        ledger['Order']=Order
        if Response!=None:
            ledger['Response']=Response
        ledger['Detail']=detail

        if subOrder['Exchange']!=None and subOrder['Account']!=None and subOrder['Asset']!=None:
            if "Market" in subOrder:
                fname=subOrder['Exchange']+'.'+subOrder['Market']+'.'+subOrder['Account']+'.'+subOrder['Asset']
            else:
                fname=subOrder['Exchange']+'.'+subOrder['Account']+'.'+subOrder['Market']+'.'+subOrder['Asset']
            fname=fname.replace('/','').replace('-','').replace(':','').replace(' ','')
            lname=LedgerDirectory+'/'+fname+'.ledger'

            # Strip Identity
            ledger.pop('Identity',None)

            ledgerLock=JRRsupport.Locker(lname)
            ledgerLock.Lock()
            JRRsupport.AppendFile(lname,json.dumps(ledger)+'\n')
            ledgerLock.Unlock()

            if type(IsLog)==bool and IsLog==True:
                self.Log.Write(f"Ledgered: {subOrder['Exchange']}/{subOrder['Account']}:{id}",stdOut=False)
"""
