#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Proxy base class and functionality
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

# Everything in the Jacckrabbit Relay class must be mirrored in the Proxy class. This will allow a client to connect to
# a remote Relay PlaceOrder.proxy and pull exchange data as if it were direct access. Functionality of this is on the
# basis of continued distributed layering.

# the remote system MMMUUSSTT have a virtual exchange configured to allow proxy functionality.

# The API function is really a webhook sender/receiver to the remote Relay system.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import signal
import atexit
import json
import requests
from datetime import datetime

# Framework APIs

import JRRsupport
from JackrabbitRelay import JackrabbitLog

# The proxy class for the system. This IS going to be a royal pain in the ass to
# type, but it also prevent mistakes as the system grows and developes. This
# will also allow me to build in place as I replace one section at a time.

# relay=JackrabbitProxy(framework="ccxt",payload=order)
# relay=JackrabbitProxy(secondary="EquilibriumConfig")

# The config files can also provide the framework and work from the command
# line.

# proxy=JackrabbitProxy()

# Done:
#   { "Action":"GetMarket", "Exchange":"Proxy", "Account":"Sandbox", "Identity":"Redacted" }
#   { "Action":"GetTicker", "Exchange":"bybit", "Account":"Sandbox", "Asset":"TRX/USDT:USDT", "Identity":"Redacted" }

# { "Action":"GetOHLCV", "Exchange":"bybit", "Account":"Sandbox", "Asset":"TRX/USDT:USDT", "TimeFrame":"D", "Identity":"Redacted" }
# { "Action":"GetOrderBook", "Exchange":"bybit", "Account":"Sandbox", "Asset":"TRX/USDT:USDT", "Identity":"Redacted" }

# Action is the Relay function to call

class JackrabbitProxy:
    def __init__(self,framework=None,payload=None,exchange=None,account=None,asset=None,Usage=None):
        # All the default locations
        self.Version="0.0.0.1.505"
        self.BaseDirectory='/home/JackrabbitRelay2/Base'
        self.ConfigDirectory='/home/JackrabbitRelay2/Config'
        self.DataDirectory="/home/JackrabbitRelay2/Data"
        self.LedgerDirectory="/home/JackrabbitRelay2/Ledger"

        # Set up the allowable function jump list.
        self.jumplist={}
        self.BuildJumpList()

        # Set up the usage notes
        self.Usage=None

        if Usage!=None:
            self.Usage=Usage

        # Initialize The log to just the basename of the program.
        self.JRLog=JackrabbitLog(None)

        # the raw payload, or command line
        self.Payload=payload

        # Command line arguments
        self.args=None
        self.argslen=0

        # This is the main exchange configuration structure, including APIs.
        self.Config=[]

        # Convience for uniformity
        self.Exchange=None

        self.Account=None

        self.Asset=None

        # API/Secret for a specific account
        self.Keys=[]

        # This is the Active API set for rotation and rotation count
        self.Active=[]
        self.CurrentKey=-1

        # The current order being processed
        self.Order=None

        # Result from last operation
        self.Results=None

        # Process command line. Must be first function called

        if len(sys.argv)>1:
            self.ProcessCommandLine()

        # if no command line, check for stabdard input, ie. process order

        if self.Payload!=None:
            self.ProcessPayload()

        # Setup the exchange and account passed in to the method. At this point, if we dont have an exchange
        # and account, the information has to have been force fed into the method.

        if self.Exchange==None and self.Account==None:
            if self.Exchange==None and exchange!=None:
                self.Exchange=exchange.lower()
            if self.Account==None and account!=None:
                self.Account=account
            if self.Asset==None and asset!=None:
                self.Asset=asset.upper()
            self.SetupLogging()

        # Process exchange/broker config file

        self.ProcessConfig()

        # Now that all parts are loaded, fully verify the payload for the
        # specific broker

 #       if self.Payload!=None:
 #           self.VerifyPayload()

        # Login to exchange/Broker

        if self.Exchange!=None and self.Account!=None:
            if self.Framework!='virtual':
                self.JRLog.Error("Initialization","Framework must be Virtual for a proxy")
        elif self.Payload!=None:
            if self.Usage:
                self.Usage(self.args,self.argslen)
            else:
                self.JRLog.Error("Initialization","An exchange and an account must be provided")
        else:
            if self.Usage:
                self.Usage(self.args,self.argslen)
            else:
                self.JRLog.Error("Initialization","An exchange and an account must be provided")

    # Build a jump list of acceptable functions

    def BuildJumpList(self):
        for name in dir(self):
            member=getattr(self,name)
            if callable(member) and name.startswith('Read'):
                self.jumplist[name]=member

    def GetExchange(self):
        return self.Exchange

    def GetAccount(self):
        return self.Account

    def GetAsset(self):
        return self.Asset

    def SetAsset(self,asset):
        self.Asset=asset

    # Return command line information to user

    def GetArgsLen(self):
        return self.argslen

    def GetArgs(self,x):
        return self.args[x]

    # Set up logging file to reference exchange, account, and asset

    def SetupLogging(self):
        lname=None
        if self.Exchange!=None and self.Account!=None and self.Asset!=None:
            lname=f"{self.Exchange}.{self.Account}.{self.Asset}"
        elif self.Exchange!=None and self.Account!=None:
            lname=f"{self.Exchange}.{self.Account}"
        elif self.Exchange!=None:
            lname=f"{self.Exchange}"

        if lname!=None:
            self.JRLog.SetLogName(lname)

    # Webhook processing. This unified layer will communicate with Proxy for
    # placing the order and return the results.

    def SendWebhook(self,Order):
        headers={'content-type': 'text/plain', 'Connection': 'close'}

        resp=None
        res=None
        try:
            resp=requests.post(self.Active['Webhook'],headers=headers,data=json.dumps(Order))
            try:
                r=json.loads(resp.text)
                try:
                    res=r['message']
                except:
                    res=json.dumps(r)
            except:
                res=resp.text
        except:
            res=None

        return res

    # Get the order ID. If there isn't an ID, the order FAILED.

    def GetProxyResult(self,res):
        if res==None:
            return None

        try:
            if res.find('ProxyResult: ')>-1:
                s=res.find('ProxyResult:')+13
                for e in range(s,len(res)):
                    if res[e]=='\n':
                        break
                result=res[s:e]

                return result
        except:
            pass
        return None

    # Read the exchange config file and load API/SECRET for a given (sub)account.
    # MAIN is reserved for the main account

    def ProcessConfig(self):
        logProcess={}
        logProcess['JRLog']=self.JRLog
        keys=[]

        # Stop processing here if we don't want to proceed with private
        # API, but want to use only public API.

        if self.Account==None or self.Account.lower()=="none":
            return

        fn=self.ConfigDirectory+'/'+self.Exchange+'.cfg'
        if os.path.exists(fn):
            cf=open(fn,'rt+')
            for line in cf.readlines():
                if len(line.strip())>0 and line[0]!='#':
                    self.Config.append(line)
                    try:
                        key=json.loads(line)
                    except:
                        self.JRLog.Error("Reading Configuration",'damaged: '+line)
                    if key['Account']==self.Account:
                        # Add identity to account reference

                        # Will need to check for identity before adding global
                        # identity.

                        # Add the hooks for the logging process.

                        if 'Identity' not in key:
                            self.JRLog.Error("Reading Configuration",'Proxy identity REQUIRED')
                        else:
                            key={ **key, **logProcess }
                        self.Keys.append(key)
                cf.close()

            if self.Keys==[]:
                self.JRLog.Error("Reading Configuration",self.Account+' reference not found, check spelling/case')
            else:
                # Verify and set framework
                for config in self.Keys:
                    if 'Framework' not in config:
                        self.JRLog.Error("Reading Configuration",f"{self.Exchange}/{self.Account} does no identify the framework")
                self.Framework=self.Keys[0]['Framework'].lower()

                # Initialize to the first key
                self.Active=self.Keys[0]
        else:
            self.JRLog.Error("Reading Configuration",self.Exchange+'.cfg not found in config directory')

    def ProcessCommandLine(self):
        # Deep copy arguments
        self.args=[]
        for i in range(len(sys.argv)):
            self.args.append(sys.argv[i])
        self.argslen=len(self.args)

        # Set up exchange, account and asset
        if self.argslen>=1:
            self.Basename=self.args[0]
        if self.argslen>=2:
            self.Exchange=self.args[1].lower().replace(' ','')
            # Check for and handle an exchange list
            echg=self.args[1].lower().replace(' ','')
            if ',' in echg:
                eList=echg.split(',')
                self.Exchange=eList[0]
                self.ExchangeList=eList[1:]
            else:
                self.Exchange=echg
        if self.argslen>=3:
            self.Account=self.args[2]
        if self.argslen>=4:
            self.Asset=self.args[3].upper()

        self.SetupLogging()

        # Clear the config arguments, otherwise the Proxy method will try to process it.
        # This is a royal PAIN IN THE ASS to debug.
        for i in range(1,len(sys.argv)):
            sys.argv.remove(sys.argv[1])

    # Process and validate the order payload

    def ProcessPayload(self,NewPayload=None):
        if NewPayload!=None:
            self.Payload=NewPayload
        if self.Payload==None or self.Payload.strip()=='':
            self.JRLog.Error('Processing Payload','Empty payload')

        self.Payload=JRRsupport.pFilter(self.Payload)

        try:
            self.Order=json.loads(self.Payload,strict=False)
        except json.decoder.JSONDecodeError as err:
            self.JRLog.Error('Processing Payload','Payload damaged')

        # These are absolutely required to load thwe proper configuration.

        if "Exchange" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing exchange identifier')
        else:
            self.Exchange=self.Order['Exchange']

        if "Account" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing account identifier')
        else:
            self.Account=self.Order['Account']

    # Get the market list from the exchange
    # { "Action":"GetMarket", "Exchange":"Proxy", "Account":"Sandbox", "Identity":"Redacted" }

    def GetMarkets(self):
        cmd={}
        cmd['Action']='GetMarkets'
        cmd['Exchange']=self.Exchange
        cmd['Account']=self.Account
        cmd['Identity']=self.Active['Identity']

        self.Results=self.SendWebhook(cmd)
        if 'GetMarkets/' in self.Results:
            self.Markets=json.loads(self.GetProxyResult(self.Results)[11:])
            return self.Markets

        return None

    # Get the the ticker from the exchange
    # { "Action":"GetTicker", "Exchange":"bybit", "Account":"Sandbox", "Asset":"TRX/USDT:USDT", "Identity":"Redacted" }

    def GetTicker(self,**kwargs):
        cmd={}
        cmd['Action']='GetTicker'
        cmd['Exchange']=self.Exchange
        cmd['Account']=self.Account
        cmd['Asset']=kwargs.get('symbol')
        cmd['Identity']=self.Active['Identity']

        self.Results=self.SendWebhook(cmd)
        if 'GetTicker/' in self.Results:
            self.Ticker=json.loads(self.GetProxyResult(self.Results)[10:])
            return self.Ticker

        return None

    # Get the the ticker from the exchange
    # { "Action":"GetTicker", "Exchange":"bybit", "Account":"Sandbox", "Asset":"TRX/USDT:USDT", "Identity":"Redacted" }

    def GetOrderBook(self,**kwargs):
        cmd={}
        cmd['Action']='GetOrderBook'
        cmd['Exchange']=self.Exchange
        cmd['Account']=self.Account
        cmd['Asset']=kwargs.get('symbol')
        cmd['Identity']=self.Active['Identity']

        self.Results=self.SendWebhook(cmd)
        if 'GetOrderBook/' in self.Results:
            self.OrderBook=json.loads(self.GetProxyResult(self.Results)[13:])
            return self.OrderBook

        return None

    # Get OHLCV data from exchange
    # { "Action":"GetOHLCV", "Exchange":"bybit", "Account":"Sandbox", "Asset":"TRX/USDT:USDT", "TimeFrame":"D", "Candles":"10", "Identity":"Redacted" }

    def GetOHLCV(self,**kwargs):
        cmd={}
        cmd['Action']='GetOHLCV'
        cmd['Exchange']=self.Exchange
        cmd['Account']=self.Account
        cmd['Asset']=kwargs.get('symbol')
        cmd['Timeframe']=kwargs.get('timeframe')
        cmd['Candles']=kwargs.get('limit')
        cmd['Identity']=self.Active['Identity']

        self.Results=self.SendWebhook(cmd)
        if 'GetOHLCV/' in self.Results:
            self.ohlcv=json.loads(self.GetProxyResult(self.Results)[9:])
            return self.ohlcv

        return None

"""

    # Verify the payload based upon a specific broker requirements.

    def VerifyPayload(self):
        if self.Framework=='ccxt':
            if "Market" not in self.Order:
                self.JRLog.Error('Processing Payload','Missing market identifier')
            self.Order['Market']=self.Order['Market'].lower()

        if "Action" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing action (buy/sell/close) identifier')
        self.Order['Action']=self.Order['Action'].lower()
        # Convert version 1 payloads to version 2
        if self.Order['Action']=='long':
            self.Order['Action']='buy'
        if self.Order['Action']=='short':
            self.Order['Action']='sell'
        if self.Order['Action']!='buy' and self.Order['Action']!='sell' and self.Order['Action']!='close':
            self.JRLog.Error('Processing Payload','Action must be one of buy, sell or close')

        if "OrderType" not in self.Order:
            self.Order['OrderType']='market'
        else:
            self.Order['OrderType']=self.Order['OrderType'].lower()

        if "Asset" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing asset identifier')
        else:
            self.Order['Asset']=self.Order['Asset'].upper()
            self.Asset=self.Order['Asset']

        # Set up logging data

        if self.Exchange!=None and self.Account!=None and self.Asset!=None:
            if "Market" in self.Order:
                lname=f"{self.Exchange}.{self.Account}.{self.Order['Market']}.{self.Asset}"
            else:
                lname=f"{self.Exchange}.{self.Account}.{self.Asset}"
            self.JRLog.SetLogName(lname)

        # Verify the Identity within the payload. Identity now REQUIRED.

        # self.Active['Identity'] will either be the global identity of the account identity.

        if self.IdentityVerification==True:
            if "Identity" in self.Active:
                if "Identity" in self.Order:
                    if self.Order['Identity']!=self.Active['Identity']:
                        self.JRLog.Error("Identity verification","FAILED: Identity does not match")
                else:
                    self.JRLog.Error("Identity verification","FAILED: Identity not in payload")
            else:
                self.JRLog.Error("Identity verification","FAILED: Identity.cfg not found")

    # This if where things get messy. The basic API must have calls to
    # each framework buy uniform to the Proxy core.

    # Rotate API key/Secret

    def RotateKeys(self):
        if self.CurrentKey<0:
            self.CurrentKey=(os.getpid()%len(self.Keys))
        else:
            self.CurrentKey=((self.CurrentKey+1)%len(self.Keys))
        self.Active=self.Keys[self.CurrentKey]

        if self.Framework=='ccxt':
            self.ccxt=self.Broker.SetExchangeAPI()

    # Carry out rate limit

    def EnforceRateLimit(self):
        if 'RateLimit' in self.Active:
            ratelimit=int(self.Active['RateLimit'])
        else:
            ratelimit=1000

        while self.Limiter.Lock()!='locked':
            JRRsupport.ElasticSleep(ratelimit/1000)
        JRRsupport.ElasticSleep(ratelimit/1000)
        self.Limiter.Unlock()

    # Function to run at exit.

    def CleanUp(self):
        # Something probably went wrong, such as an exchnge/broker timeout. Remove the rate limit by force. This
        # is neccessary or any program is a rate limited sleep will hold up everything waiting for a dead lock to
        # expire.

        self.Limiter.Unlock()

    # Login to a given exchange

    # Active references must be passed as well.

    def Login(self):
        # Sanity check

        if self.Framework==None:
            if 'Framework' in self.Active:
                self.Framework=self.Active['Framework'].lower()
            else:
                self.JRLog.Error("Login",self.Exchange+' framework not given in configuration')

        # Initialize rate limiting sub-system
        ln="RateLimiter."+self.Exchange
        self.Limiter=JRRsupport.Locker(ln,ID=ln)
        atexit.register(self.CleanUp)

        # Market data is loaded automatically. Pull it into the Proxy object as
        # well.

        if self.Framework=='ccxt':
            self.Broker=JRRccxt.ccxtCrypto(self.Exchange,self.Config,self.Active,DataDirectory=self.DataDirectory)
            self.Timeframes=list(self.Broker.Broker.timeframes.keys())
        elif self.Framework=='oanda':
            self.Broker=JRRoanda.oanda(self.Exchange,self.Config,self.Active,DataDirectory=self.DataDirectory)
            self.Timeframes=list(self.Broker.timeframes.keys())

        self.Markets=self.Broker.Markets

    # Get account balance(s)

    def GetBalance(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.GetBalance(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    # Get the exchange positions. For and non-spot market

    def GetPositions(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.GetPositions(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    # Get OHLCV data from exchange

    def GetOHLCV(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.GetOHLCV(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    # Get ticker data from exchange

    def GetTicker(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.GetTicker(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    # Get orderbook data from exchange

    def GetOrderBook(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.GetOrderBook(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    # Get open orders

    def GetOpenOrders(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.GetOpenOrders(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    # Get open Trades

    def GetOpenTrades(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.GetOpenTrades(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    # Place Order to exchange. Needs to handle buy, sell, close
    # exchange
    # Active, retry limit is in this structure
    # ADA/USD or USD/JPY
    # market or limit
    # 1 or 0.001 ...
    # buy, sell or close
    # 63000
    # Reduce only, true/false
    # Ledger note, if any

    def PlaceOrder(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.PlaceOrder(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    def GetMinimum(self,**kwargs):
        self.RotateKeys()
        minimum,mincost=self.Broker.GetMinimum(**kwargs)
        self.EnforceRateLimit()
        return minimum,mincost

    # Get the exact details of a specific order

    def GetOrderDetails(self,**kwargs):
        self.RotateKeys()
        self.Results=self.Broker.GetOrderDetails(**kwargs)
        self.EnforceRateLimit()
        return self.Results

    # Process the orphan order

    def MakeOrphanOrder(self,id,Order):
        self.Results=self.Broker.MakeOrphanOrder(id,Order)
        self.EnforceRateLimit()

    # Process the conditional order

    def MakeConditionalOrder(self,id,Order):
        self.Results=self.Broker.MakeConditionalOrder(id,Order)
        self.EnforceRateLimit()

    # Make ledger entry

    def WriteLedger(self,**kwargs):
        self.Results=self.Broker.WriteLedger(**kwargs,LedgerDirectory=self.LedgerDirectory)
        self.EnforceRateLimit()

    # See if an order is already in Oliver Twist for Exchange/Account/Pair. This is to allow ONLY ONE order at a time.

    def OliverTwistOneShot(self,CompareOrder):
        fList=[self.DataDirectory+'/OliverTwist.Conditional.Receiver',self.DataDirectory+'/OliverTwist.Conditional.Storehouse']
        orphanLock=JRRsupport.Locker("OliverTwist")

        orphanLock.Lock()
        for fn in fList:
            if os.path.exists(fn):
                buffer=JRRsupport.ReadFile(fn)
                if buffer!=None and buffer!='':
                    Orphans=buffer.split('\n')
                    for Entry in Orphans:
                        # Force set InMotion to False
                        Entry=Entry.strip()
                        if Entry=='':
                            continue
                        # Break down entry and set up memory locker
                        try:
                            Orphan=json.loads(Entry)
                        except:
                            continue

                        if 'Order' in Orphan:
                            if type(Orphan['Order'])==str:
                                order=json.loads(Orphan['Order'])
                            else:
                                order=Orphan['Order']
                            if CompareOrder['Exchange']==order['Exchange'] \
                            and CompareOrder['Account']==order['Account'] \
                            and CompareOrder['Asset']==order['Asset']:
                                orphanLock.Unlock()
                                return True

        # Not Found
        orphanLock.Unlock()
        return False
"""
