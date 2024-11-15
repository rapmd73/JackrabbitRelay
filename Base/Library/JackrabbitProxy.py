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
#   { "Action":"GetOHLCV", "Exchange":"bybit", "Account":"Sandbox", "Asset":"TRX/USDT:USDT", "TimeFrame":"D", "Identity":"Redacted" }
#   { "Action":"GetOrderBook", "Exchange":"bybit", "Account":"Sandbox", "Asset":"TRX/USDT:USDT", "Identity":"Redacted" }

# Action is the Relay function to call

class JackrabbitProxy:
    def __init__(self,framework=None,payload=None,exchange=None,account=None,asset=None,Usage=None):
        # All the default locations
        self.Version="0.0.0.1.1020"
        self.BaseDirectory='/home/JackrabbitRelay2/Base'
        self.ConfigDirectory='/home/JackrabbitRelay2/Config'
        self.DataDirectory="/home/JackrabbitRelay2/Data"
        self.LedgerDirectory="/home/JackrabbitRelay2/Ledger"

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

        if self.Account==None or self.Account.lower()=="public":
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
                        self.JRLog.Error("Reading Configuration",f'damaged: {line}')
                    if key['Account']==self.Account:
                        # Add identity to account reference

                        # Will need to check for identity before adding global
                        # identity.

                        # Add the hooks for the logging process.

                        if 'Identity' not in key:
                            self.JRLog.Error("Reading Configuration",'Proxy identity REQUIRED')
                        else:
                            if len(key['Identity'])<1024:
                                self.JRLog.Error("Reading Configuration",'Proxy identity too short')
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

