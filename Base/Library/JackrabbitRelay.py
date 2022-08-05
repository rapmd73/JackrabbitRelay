#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Relay bas class and functionality
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/GitHub/JackrabbitRelay/Base/Library')
import os
import pathlib
import time
import json
import requests
from datetime import datetime

# This is the logging class
#
# This will all a unified approach to logging individual assets
# JRLog=JackrabbitLog(market+'.'+exchange+'.'+asset)
#   -> spot.kucoin.adausdt

class JackrabbitLog:
    def __init__(self,filename=None):
        self.LogDirectory="/home/JackrabbitRelay/Logs"
        self.StartTime=datetime.now()
        self.basename=os.path.basename(sys.argv[0])
        self.SetLogName(filename)

    def SetLogName(self,filename):
        if filename==None:
            self.logfile=self.basename
        else:
            self.logfile=self.basename+'.'+filename

    def write(self,text):
        pid=os.getpid()
        time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

        s=f'{time} {pid:7.0f} {text}\n'

        fh=open(self.LogDirectory+'/'+self.logfile+'.log','a')
        fh.write(s)
        fh.close()
        print(s.rstrip())
        sys.stdout.flush()

    def Elapsed(self):
        EndTime=datetime.now()
        Elapsed=(EndTime-self.StartTime)
        self.write("Processing Completed: "+str(Elapsed)+" seconds")

    def Error(self,f,s):
        msg=f+' failed with: '+s
        self.write(msg)
        self.Elapsed()
        sys.exit(3)

    def Success(self,f,s):
        msg=f+' successful with: '+s
        self.write(msg)
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
        self.Version="0.0.0.0.1120"
        self.BaseDirectory='/home/JackrabbitRelay/Base'
        self.ConfigDirectory='/home/JackrabbitRelay/Config'
        self.DataDirectory="/home/JackrabbitRelay/Data"
        self.BalancesDirectory='/home/JackrabbitRelay/Statistics/Balances'
        self.ChartsDirectory='/home/JackrabbitRelay/Statistics/Charts'
        self.LedgerDirectory="/home/JackrabbitRelay/Ledger"
        self.StatisticsDirectory='/home/JackrabbitRelay/Extras/Statistics'

        self.NOhtml='<html><title>NO!</title><body style="background-color:#ffff00;display:flex;weight:100vw;height:100vh;align-items:center;justify-content:center"><h1 style="color:#ff0000;font-weight:1000;font-size:10rem">NO!</h1></body></html>'

        self.JRLog=JackrabbitLog(None)
        # the raw payload
        self.Payload=payload
        # This is the main exchange configuration structure, including APIs.
        self.Config=[]
        # Convience for uniformity
        self.Exchange=None
        self.Account=None
        # API/Secret for a specific account
        self.Keys=[]
        # This is the Active API set for rotation and rotation count
        self.Active=[]
        self.CurrentKey=0
        # The current order being processed
        self.Order=None
        # this is the framework that defines the low level API, 
        # ie CCXT, OANDA, ROBINHOOD, FTXSTOCKS
        self.Framework=framework.lower()

        # Process the payload
        self.ProcessPayload()
        self.ProcessConfig()

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
            self.Order=None
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

    def RotateKeys(self):
        self.CurrentKey=(os.getpid()%len(self.keys))
        self.Active=self.Keys[self.CurrentKey]

    # Read the exchange config file and load API/SECRET for a given (sub)account.
    # MAIN is reserved for the main account

    def ProcessConfig(self):
        keys=[]

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
                            key= { **idl, **key }
                        self.Keys.append(key)
                cf.close()

            if self.Keys==[]:
                self.JRLog.Error("Reading Configuration",account+' reference not found, check spelling/case')
            else:
                self.Active=self.Keys[self.CurrentKey]
        else:
            self.JRLog.Error("Reading Configuration",echg+'.cfg not found in config directory')

    def LogIn():
        if self.framework=='ccxt':
            import JRRccxt
            self.ccxt=JRRccxt.ExchangeLogin(self.Exchange,self.Active)

"""
class DList:
    def __init__(self):
        self.head=None
        self.tail=None
        self.sentinel=None
        self.size=0

    def GetHead(self):
        return self.head

    def SetHead(self,head):
        self.head=head

    def GetTail(self):
        return self.tail

    def SetTail(self,tail):
        self.tail=tail

    def Length(self):
        return self.size

    def find(self,data,compare=None):
        if self.head:
            if compare(self.head,data)==0:
                return self.head
            elif compare(self.tail,data)==0:
                return self.tail
            else:
                if self.sentinel==None:
                    self.sentinel=self.head
                res=compare(self.sentinel,data)
                if res>0:
                    while self.sentinel.GetNext()!=None and compare(self.sentinel,data)>0:
                        self.sentinel=self.sentinel.GetNext()
                    if compare(self.sentinel,data)==0:
                        return self.sentinel
                    else:
                        return None
                elif res<0:
                    while self.sentinel.GetPrev()!=None and compare(self.sentinel,data)<0:
                        self.sentinel=self.sentinel.GetPrev()
                    if compare(self.sentinel,data)==0:
                        return self.sentinel
                    else:
                        return None
                else: # res==0
                    return self.sentinel
        else:
            return None

    def insert(self,data,compare=None):
        if self.head:
            # Initialize sentinel ptr. This will move according to direction of
            # comparisons. Will befaster then always starting at head of list.

            # New head of list test
            if compare(self.head,data)<0:
                newNode=DListNode(data)
                newNode.SetNext(self.head)
                newNode.GetNext().SetPrev(newNode)
                self.head=newNode
                self.size+=1
                return
            # New tail of list test
            elif compare(self.tail,data)>0:
                newNode=DListNode(data)
                newNode.SetPrev(self.tail)
                newNode.GetPrev().SetNext(newNode)
                self.tail=newNode
                self.size+=1
                return
            # Add to the middle based on sentinel for locating
            else:
                if self.sentinel==None:
                    self.sentinel=self.head
                res=compare(self.sentinel,data)
                if res>0:
                    while self.sentinel.GetNext()!=None and compare(self.sentinel.GetNext(),data)>0:
                        self.sentinel=self.sentinel.GetNext()
                    newNode=DListNode(data)
                    newNode.SetNext(self.sentinel.GetNext())
                    if self.sentinel.GetNext()!=None:
                        newNode.GetNext().SetPrev(newNode)
                    self.sentinel.SetNext(newNode)
                    newNode.SetPrev(self.sentinel)
                    self.size+=1
                    return
                elif res<0:
                    while self.sentinel.GetPrev()!=None and compare(self.sentinel.GetPrev(),data)<0:
                        self.sentinel=self.sentinel.GetPrev()
                    newNode=DListNode(data)
                    newNode.SetPrev(self.sentinel.GetPrev())
                    if self.sentinel.GetPrev()!=None:
                        newNode.GetPrev().SetNext(newNode)
                    self.sentinel.SetPrev(newNode)
                    newNode.SetNext(self.sentinel)
                    self.size+=1
                    return
        else:
            # Create list with new node
            newNode=DListNode(data)
            self.head=newNode
            self.tail=newNode
            self.sintinel=self.head
            self.size+=1
            return

    def delete(self,data,compare=None):
        if self.head:
            node=self.find(data,compare)
            # Not in list
            if node==None:
                return

            if node==self.head:
                n=self.head.GetNext()
                n.SetPrev(None)
                self.head=n
                self.size-=1
                return
            elif node==self.tail:
                p=self.tail.GetPrev()
                p.SetNext(None)
                self.tail=p
                self.size-=1
                return
            else:
                p=node.GetPrev()
                n=node.GetNext()
                p.SetNext(n)
                n.SetPrev(p)
                self.size-=1
                return
        else:
            return

    def dump(self,current):
        if current==None:
            return

        if self.head!=None:
            h=self.head.GetData()
        else:
            h="None"
        if self.tail!=None:
            t=self.tail.GetData()
        else:
            t="None"
        if current.GetPrev()!=None:
            p=str(current.GetPrev().GetData())
        else:
            p="None"
        if current!=None:
            c=str(current.GetData())
        else:
            c="None"
        if current.GetNext()!=None:
            n=str(current.GetNext().GetData())
        else:
            n="None"
        print(f"H: {h} P: {p} C: {c} N: {n} T: {t}")

    def list(self):
        if self.head:
            current=self.head
            while current:
                self.dump(current)
                current=current.GetNext()
"""

