#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay base class and functionality
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import signal
import json
import requests
from datetime import datetime

# Framework APIs

import JRRccxt
import JRRoanda
import JRRsupport

# This is the logging class
#
# This will all a unified approach to logging individual assets
# JRLog=JackrabbitLog(market+'.'+exchange+'.'+asset)
#   -> spot.kucoin.adausdt

class JackrabbitLog:
    def __init__(self,filename=None,Base=None):
        self.LogDirectory="/home/JackrabbitRelay2/Logs"
        self.StartTime=datetime.now()
        self.logfile=None
        self.filename=filename
        self.basename=Base
        if self.basename==None:
            self.basename=os.path.basename(sys.argv[0])

        self.SetLogName(filename)

    def SetBaseName(self,basename):
        if basename==None:
            self.basename=os.path.basename(sys.argv[0])
        else:
            self.basename=basename
        self.SetLogName(self.filename)

    def SetLogName(self,filename):
        if filename!=self.filename:
            self.filename=filename
        if filename==None:
            self.logfile=self.basename
        else:
            self.logfile=self.basename+'.'+filename.replace('/','').replace('-','').replace(':','').replace(' ','')

    def Write(self,text,stdOut=True):
        pid=os.getpid()
        time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

        s=f'{time} {pid:7.0f} {text}\n'

        fn=self.LogDirectory+'/'+self.logfile+'.log'
        fh=open(fn,'a+')
        fh.write(s)
        fh.close()
        if stdOut==True:
            print(s.rstrip())
            sys.stdout.flush()

    def Elapsed(self):
        EndTime=datetime.now()
        Elapsed=(EndTime-self.StartTime)
        self.Write("Processing Completed: "+str(Elapsed)+" seconds")

    def Error(self,f,s):
        msg=f+' failed with: '+s
        self.Write(msg)
        self.Elapsed()
        JRRsupport.ForceExit(3)

    def Success(self,f,s):
        msg=f+' successful with: '+s
        self.Write(msg)
        self.Elapsed()
        JRRsupport.ForceExit(0)

# The main class for the system. This IS going to be a royal pain in the ass to
# type, but it also prevent mistakes as the system grows and developes. This
# will also allow me to build in place as I replace one section at a time.

# relay=JackrabbitRelay(framework="ccxt",payload=order)
# relay=JackrabbitRelay(secondary="EquilibriumConfig")

# The config files can also provide the framework and work from the command
# line.

# relay=JackrabbitRelay()

class JackrabbitRelay:
    def __init__(self,framework=None,payload=None,exchange=None,account=None,asset=None,secondary=None):
        # All the default locations
        self.Version="0.0.0.1.305"
        self.BaseDirectory='/home/JackrabbitRelay2/Base'
        self.ConfigDirectory='/home/JackrabbitRelay2/Config'
        self.DataDirectory="/home/JackrabbitRelay2/Data"
        self.BalancesDirectory='/home/JackrabbitRelay2/Statistics/Balances'
        self.ChartsDirectory='/home/JackrabbitRelay2/Statistics/Charts'
        self.LedgerDirectory="/home/JackrabbitRelay2/Ledger"
        self.StatisticsDirectory='/home/JackrabbitRelay2/Extras/Statistics'
        self.Identity=None

        self.NOhtml='<html><title>NO!</title><body style="background-color:#ffff00;display:flex;weight:100vw;height:100vh;align-items:center;justify-content:center"><h1 style="color:#ff0000;font-weight:1000;font-size:10rem">NO!</h1></body></html>'

        # This will be the connector point to any exchange/broker
        self.Broker=None

        # This is for the rate limiting sub-system
        self.Limiter=None

        # Initialize The log to just the basename of the program.
        self.JRLog=JackrabbitLog(None)

        # the raw payload, or command line
        self.Payload=payload

        # Command line arguments
        self.args=None
        self.argslen=0

        # This is the main exchange configuration structure, including APIs.
        self.Config=[]

        # Secondary config reader for Equilibrium or any other external program
        # hooking into Relay. This will be responsible for the same
        # functionality as the payload or commandline methods. Exchange,
        # Account, Asset, etc must be set up.

        self.Secondary=secondary

        # Convience for uniformity
        self.Exchange=None

        # Break down any chained lists. Exchange will be first, rest of chain
        # will be in the list. Exchange place order MUST be last. With the below
        # example, Exchange will contain dsr and ExchangeList will contain
        # kucoin. It is the responsibility of the PlaceOrder for dsr (this
        # example) to build the order for kucoin (this example) and feed it back
        # into the Relay Server with SendWebhook.
        #    "Exchange":"dsr,kucoin",

        self.ExchangeList=None

        # Account must also be a list reference to coinside with the coresponding
        # exchange.
        #    "Account":"Sandbox,MAIN",

        self.Account=None
        self.AccountList=None

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

        # this is the framework that defines the low level API,
        # ie CCXT, OANDA, ROBINHOOD, FTXSTOCKS
        # Framework can be provided by config file

        self.Framework=None
        if framework!=None:
            self.Framework=framework.lower()

        # Whether or not to rotate keys after every API call. Does NOT apply to
        # OANDA.

        self.ForceRotateKeys=True

        # Read global identty

        self.ReadGlobalIdentity()

        # Process command line. Must be first function called

        if len(sys.argv)>1:
            self.ProcessCommandLine()

        # if no command line, check for stabdard input, ie. process order

        if self.Payload!=None:
            self.ProcessPayload()

        # Process secondary config file. Exchange, Account, and Asset must be
        # defined.

        if self.Secondary!=None:
            self.Secondary()

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

        if self.Payload!=None:
            self.VerifyPayload()

        # Login to exchange/Broker

        if self.Exchange!=None and self.Account!=None:

            # Do NOT automatically log into a virtual exchange. This is
            # responsibility of calling program (the virtual exchange).

            if self.Framework!='virtual':
                self.Login()
        elif self.Payload!=None:
            self.JRLog.Error("Login","An exchange and an account must be provided")
        else:
            self.JRLog.Error("Initialization","An exchange and an account must be provided")

    def GetExchange(self):
        return self.Exchange

    def GetExchangeList(self):
        return ','.join(self.ExchangeList)

    def GetExchangeNext(self):
        if self.ExchangeList!=None and len(self.ExchangeList)>0:
            return self.ExchangeList[0]
        else:
            return None

    def GetExchangeAfterNext(self):
        if self.ExchangeList!=None and len(self.ExchangeList)>1:
            return self.ExchangeList[1:]
        else:
            return None

    def GetExchangeLast(self):
        if self.ExchangeList!=None and len(self.ExchangeList)>0:
            return self.ExchangeList[-1]
        else:
            return None

    def GetAccount(self):
        return self.Account

    def GetAccountList(self):
        return ','.join(self.AccountList)

    def GetAccountNext(self):
        if self.AccountList!=None and len(self.AccountList)>0:
            return self.AccountList[0]
        else:
            return None

    def GetAccountAfterNext(self):
        if self.AccountList!=None and len(self.AccountList)>1:
            return self.AccountList[1:]
        else:
            return None

    def GetAccountLast(self):
        if self.AccountList!=None and len(self.AccountList)>0:
            return self.AccountList[-1]
        else:
            return None

    def GetAsset(self):
        return self.Asset

    def SetAsset(self,asset):
        self.Asset=asset

    def SetRotateKeys(self,rk):
        self.ForceRotateKeys=rk

    def GetRotateKeys(self):
        return self.ForceRotateKeys

    def SetFramework(self,framework):
        self.Framework=framework

    def GetFramework(self):
        return self.Framework

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

    # Read global Identity

    def ReadGlobalIdentity(self):
        idf=self.ConfigDirectory+'/Identity.cfg'
        if os.path.exists(idf):
            cf=open(idf,'rt+')
            try:
                self.Identity=json.loads(cf.readline())
            except:
                self.JRLog.Error("Reading Configuration",'identity damaged')
            cf.close()
        else:
            self.JRLog.Error("Reading Configuration",'Identity.cfg not found')

    # Webhook processing. This unified layer will communicate with Relay for
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

    # Remap TradingView symbol to the exchange symbol/broker

    def TradingViewRemap(self):
        if self.Asset!=self.Order['Asset']:
            self.JRLog.Errr("TradingViewRemap",'internal asset conflict. Report this error.')

        NewPair=self.Asset
        self.JRLog.Write('TradingView Symbol Remap')
        self.JRLog.Write('|- In: '+self.Asset)

        fn=self.DataDirectory+'/'+self.Exchange+'.'+self.Account+'.symbolmap'
        if os.path.exists(fn):
            try:
                raw=JRRsupport.ReadFile(fn)
            except Exception as e:
                self.JRLog.Error("TradingView Remap",f"Can't read symbol map for {self.Exchange}")

            TVlist=json.loads(raw)
            if self.Asset in TVlist:
                NewPair=TVlist[self.Asset]
            else:
                self.JRLog.Write('|- Pair not in symbol file')
                return
        else:
            self.JRLog.Write('|- No symbol file')
            return

        self.JRLog.Write('|- Out: '+NewPair)

        self.Asset=NewPair
        self.Order['Asset']=NewPair

    # Process and validate the order payload

    def ProcessPayload(self):
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
            # Check for and handle an exchange list
            echg=self.Order['Exchange'].lower().replace(' ','')
            if ',' in echg:
                eList=echg.split(',')
                self.Order['Exchange']=eList[0]
                self.ExchangeList=eList[1:]
            self.Exchange=self.Order['Exchange']

        if "Account" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing account identifier')
        else:
            # Check for and handle an account list
            acct=self.Order['Account'].replace(' ','')
            if ',' in acct:
                aList=acct.split(',')
                self.Order['Account']=aList[0]
                self.AccountList=aList[1:]
            self.Account=self.Order['Account']

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

        if "Identity" in self.Active:
            if "Identity" in self.Order:
                if self.Order['Identity']!=self.Active['Identity']:
                    self.JRLog.Error("Identity verification","FAILED: Identity does not match")
            else:
                self.JRLog.Error("Identity verification","FAILED: Identity not in payload")
        else:
            self.JRLog.Error("Identity verification","FAILED: Identity.cfg not found")

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
                            key={ **key, **self.Identity, **logProcess }
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
        self.args=sys.argv
        self.argslen=len(sys.argv)

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

    # This if where things get messy. The basic API must have calls to
    # each framework buy uniform to the Relay core.

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

        # Market data is loaded automatically. Pull it into the Relay object as
        # well.

        if self.Framework=='ccxt':
            self.Broker=JRRccxt.ccxtCrypto(self.Exchange,self.Config,self.Active,DataDirectory=self.DataDirectory)
        elif self.Framework=='oanda':
            self.Broker=JRRoanda.oanda(self.Exchange,self.Config,self.Active,DataDirectory=self.DataDirectory)

        self.Markets=self.Broker.Markets

    # Get the market list from the exchange

    def GetMarkets(self):
        self.RotateKeys()
        self.Markets=self.Broker.GetMarkets()
        self.EnforceRateLimit()
        return self.Markets

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
        self.EnforceRateLimit()
        self.Results=self.Broker.GetOrderBook(**kwargs)
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
