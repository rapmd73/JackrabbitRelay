#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay base class and functionality
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay2/Base/Library')
import os
import pathlib
import time
import json
import requests
from datetime import datetime

# Framework APIs
import JRRccxt
import JRRoanda

# This is the logging class
#
# This will all a unified approach to logging individual assets
# JRLog=JackrabbitLog(market+'.'+exchange+'.'+asset)
#   -> spot.kucoin.adausdt

class JackrabbitLog:
    def __init__(self,filename=None):
        self.LogDirectory="/home/JackrabbitRelay2/Logs"
        self.StartTime=datetime.now()
        self.basename=os.path.basename(sys.argv[0])
        self.SetLogName(filename)

    def SetLogName(self,filename):
        if filename==None:
            self.logfile=self.basename
        else:
            self.logfile=self.basename+'.'+filename.replace('/','').replace(':','')

    def Write(self,text):
        pid=os.getpid()
        time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

        s=f'{time} {pid:7.0f} {text}\n'

        fn=self.LogDirectory+'/'+self.logfile+'.log'
        fh=open(fn,'a+')
        fh.write(s)
        fh.close()
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
        sys.exit(3)

    def Success(self,f,s):
        msg=f+' successful with: '+s
        self.Write(msg)
        self.Elapsed()
        sys.exit(0)

# The main class for the system. This IS going to be a royal pain in the
# ass to type, but it also prevent mistakes as the system grows as
# developes. This will also allow me to build in place as I replace one
# section at a time.

# relay=JackrabbitRelay(framework="ccxt",payload=order)

class JackrabbitRelay:
    def __init__(self,framework=None,payload=None):
        # All the default locations
        self.Version="0.0.0.1.0"
        self.BaseDirectory='/home/JackrabbitRelay2/Base'
        self.ConfigDirectory='/home/JackrabbitRelay2/Config'
        self.DataDirectory="/home/JackrabbitRelay2/Data"
        self.BalancesDirectory='/home/JackrabbitRelay2/Statistics/Balances'
        self.ChartsDirectory='/home/JackrabbitRelay2/Statistics/Charts'
        self.LedgerDirectory="/home/JackrabbitRelay2/Ledger"
        self.StatisticsDirectory='/home/JackrabbitRelay2/Extras/Statistics'

        self.NOhtml='<html><title>NO!</title><body style="background-color:#ffff00;display:flex;weight:100vw;height:100vh;align-items:center;justify-content:center"><h1 style="color:#ff0000;font-weight:1000;font-size:10rem">NO!</h1></body></html>'

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
        self.CurrentKey=0
        # The current order being processed
        self.Order=None
        # Result from last operation
        self.Result=None
        # this is the framework that defines the low level API, 
        # ie CCXT, OANDA, ROBINHOOD, FTXSTOCKS
        # Framework can be provided by config file
        if framework!=None:
            self.Framework=framework.lower()
        else:
            self.Framework=None
        # Whether or not to rotate keys after every API call
        self.ForceRotateKeys=True

        # Process the payload and configuration at initialization of structure
        # Must be first function called
        self.ProcessCommandLine()

        # if no command line, check for stabdard input
        if self.argslen==1:
            self.ProcessPayload()

        # Process config file
        self.ProcessConfig()

        # Login to exchange/Broker
        self.Login()

    def GetExchange(self):
        return self.Exchange

    def GetAccount(self):
        return self.Account

    def GetAsset(self):
        return self.Asset

    def SetRotateKeys(self,rk):
        self.ForceRotateKeys=rk

    def GetRotateKeys(self):
        return self.ForceRotateKeys

    def SetFramework(self,framework):
        self.Framework=framework

    def GetFramework(self):
        return self.Framework

    # Filter end of line and hard spaces

    def pFilter(self,s):
        d=s.replace("\\n","").replace("\\t","").replace("\\r","")

        for c in '\t\r\n \u00A0':
            d=d.replace(c,'')

        return(d)

    # Process and validate the order payload

    def ProcessPayload(self):
        if self.Payload==None or self.Payload.strip()=='':
            self.JRLog.Error('Processing Payload','Empty payload')

        try:
            self.Order=json.loads(self.Payload,strict=False)
        except json.decoder.JSONDecodeError as err:
            self.JRLog.Error('Processing Payload','Payload damaged')

        if "Exchange" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing exchange identifier')
        else:
            self.Exchange=self.Order['Exchange']
        if "Account" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing account identifier')
        else:
            self.Account=self.Order['Account']
        if "Market" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing market identifier')
        if "Action" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing action (buy/sell/close) identifier')
        if "Asset" not in self.Order:
            self.JRLog.Error('Processing Payload','Missing asset identifier')
        self.Order['Asset']=self.Order['Asset'].upper()

        # Set up logging data

        if self.Exchange!=None and self.Account!=None and self.Asset!=None:
            lname=f"{self.Exchange}.{self.Account}.{self.Asset}"
            self.JRLog.SetLogName(lname.replace('/','').replace(':',''))

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

        idl=None
        idf=self.ConfigDirectory+'/Identity.cfg'
        if os.path.exists(idf):
            cf=open(idf,'rt+')
            try:
                idl=json.loads(cf.readline())
            except:
                self.JRLog.Error("Reading Configuration",'identity damaged')
            cf.close()

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
                        if idl!=None:
                            key={ **idl, **key, **logProcess }
                        self.Keys.append(key)
                cf.close()

            if self.Keys==[]:
                self.JRLog.Error("Reading Configuration",account+' reference not found, check spelling/case')
            else:
                self.Active=self.Keys[self.CurrentKey]
        else:
            self.JRLog.Error("Reading Configuration",echg+'.cfg not found in config directory')

    def ProcessCommandLine(self):
        self.args=sys.argv
        self.argslen=len(sys.argv)

        # Set up exchange, account and asset
        if self.argslen>=1:
            self.Basename=self.args[0]
        if self.argslen>=2:
            self.Exchange=self.args[1].lower()
        if self.argslen>=3:
            self.Account=self.args[2]
        if self.argslen>=4:
            self.Asset=self.args[3].upper()

        # Set up logging file to reference exchange, account, and asset
        if self.Exchange!=None and self.Account!=None and self.Asset!=None:
            lname=f"{self.Exchange}.{self.Account}.{self.Asset}"
        elif self.Exchange!=None and self.Account!=None:
            lname=f"{self.Exchange}.{self.Account}"
        elif self.Exchange!=None:
            lname=f"{self.Exchange}"

        self.JRLog.SetLogName(lname.replace('/',''))

    def GetArgsLen(self):
        return self.argslen

    def GetArgs(self,x):
        return self.args[x]

    # This if where things get messy. The basic API must have calls to
    # each framework buy uniform to the Relay core.

    # Rotate API key/Secret

    def RotateKeys(self):
        self.CurrentKey=(os.getpid()%len(self.Keys))
        self.Active=self.Keys[self.CurrentKey]

        if self.Framework=='ccxt':
            self.ccxt=JRRccxt.SetExchangeAPI(self.ccxt,self.Active,notify=False)

    # Login to a given exchange

    def Login(self):
        if self.Framework==None:
            if 'Framework' in self.Active:
                self.Framework=self.Active['Framework']
            else:
                self.JRLog.Error("Login",self.Exchange+' framework not given')

        if self.Framework=='ccxt':
            self.ccxt=JRRccxt.ExchangeLogin(self.Exchange,self.Config,self.Active)
        elif self.Framework=='oanda':
            self.oanda=JRRoanda.ExchangeLogin(self.Exchange,self.Config,self.Active)

    # Get the market list from the exchange

    def GetMarkets(self):
        self.RotateKeys()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.ccxtAPI("load_markets",self.ccxt,self.Active)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetMarkets(self.oanda,self.Active)
            return self.Result

    # Get the exchange balances. Spot or base market

    def GetBalances(self):
        self.RotateKeys()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.ccxtAPI("fetch_balance",self.ccxt,self.Active)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetBalances(self.oanda,self.Active)
            return self.Result

    def GetBalance(self,asset):
        self.RotateKeys()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.ccxtAPI("fetch_balance",self.ccxt,self.Active)
            self.Result=JRRccxt.GetBalance(self.Result,asset)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetBalance(self.oanda,self.Active)
            return self.Result

    # Get the exchange positions. For and non-spot market

    def GetPositions(self):
        self.RotateKeys()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.ccxtAPI("fetch_positions",self.ccxt,self.Active)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetPositions(self.oanda,self.Active)
            return self.Result

    # Get a single positions. For and non-spot market

    def GetPosition(self,Asset):
        self.RotateKeys()
        self.Result=self.GetPositions()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.GetContracts(self.Result,Asset)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetPosition(self.oanda,self.Active,Asset)
            return self.Result

    # Get OHLCV data from exchange

    def GetOHLCV(self,**kwargs):
        self.RotateKeys()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.ccxtAPI("fetch_ohlcv",self.ccxt,self.Active,**kwargs)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetOHLCV(self.oanda,self.Active,**kwargs)
            return self.Result

    # Get ticker data from exchange

    def GetTicker(self,**kwargs):
        self.RotateKeys()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.ccxtAPI("fetch_ticker",self.ccxt,self.Active,**kwargs)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetTicker(self.oanda,self.Active,**kwargs)
            return self.Result

    # Get orderbook data from exchange

    def GetOrderBook(self,**kwargs):
        self.RotateKeys()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.GetOrderBook(self.ccxt,self.Active,**kwargs)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetOrderBook(self.oanda,self.Active,**kwargs)
            return self.Result

    # Get open orders

    def GetOpenOrders(self,**kwargs):
        self.RotateKeys()
        if self.Framework=='ccxt':
            self.Result=JRRccxt.GetOpenOrders(self.ccxt,self.Active,**kwargs)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.GetOpenOrders(self.oanda,self.Active,**kwargs)
            return self.Result

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
        if self.Framework=='ccxt':
            self.Result=JRRccxt.PlaceOrder(self.ccxt,self.Active,**kwargs)
            return self.Result
        elif self.Framework=='oanda':
            self.Result=JRRoanda.PlaceOrder(self.oanda,self.Active,**kwargs)
            return self.Result

"""

Needs support for these functions as unified base.
Exchange response goes in self.Order['Result']

ccxt.fetchOrder         self.Order['Result']=GetOrder
ccxt.cancel_order       CancelOrder
ccxt.create_order       CreateOrder
"""

