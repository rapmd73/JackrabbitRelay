#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Jackrabbit Equilibrium support library
# 2021 Copyright © Robert APM Darin
# All rights reserved unconditionally.

import sys
sys.path.append('/home/JackrabbitRelay/Base/Library')
import os
from datetime import datetime
import pathlib
import time
import requests
import json

import JRRconfig
import JRRlog
import JRRapi
import JRRsupport

def IncreaseLongTradeTable(Trade,close,pct):
    if Trade['PCTValue']==0 or Trade['Counter']==0:
        Trade['PCTValue']=round(close*pct,8)
        Trade['Close']=round(close,8)
    else:
        Trade['Close']=round(Trade['Buy'],8)
    Trade['Buy']=round(Trade['Close']-Trade['PCTValue'],8)
    Trade['Sell']=round(Trade['Close']+Trade['PCTValue'],8)
    Trade['Counter']+=1

    return(Trade)

def IncreaseTradeTable(Trade,close,pct,direction,AllTimeHigh):
    # for futures, setup is very different for initial grid.

    if Trade['PCTValue']==0 or Trade['Counter']==0:
        Trade['PCTValue']=round(close*pct,8)
        Trade['Close']=round(close,8)
        if direction=='short':
            Trade['Buy']= round(Trade['Close']-(AllTimeHigh*(pct*4)),8)
        else:
            Trade['Buy']= round(Trade['Close']-Trade['PCTValue'],8)
        Trade['Sell']=round(Trade['Close']+Trade['PCTValue'],8)
    else:
        if direction=='long':
            Trade['Close']=round(Trade['Buy'],8)
            Trade['Buy']=  round(Trade['Close']-Trade['PCTValue'],8)
        else:
            Trade['Close']=round(Trade['Sell'],8)
            Trade['Buy']= round(Trade['Close']-(AllTimeHigh*(pct*4)),8)
        Trade['Sell']= round(Trade['Close']+Trade['PCTValue'],8)

    Trade['Counter']+=1

    return(Trade)

def DecreaseLongTradeTable(Trade,close,SellAMT):
    if SellAMT>0.0:
        Trade['Profit']+=round((close-Trade['Close'])*SellAMT,8)
    Trade['Close']=round(Trade['Sell'],8)
    Trade['Buy']=round(Trade['Close']-Trade['PCTValue'],8)
    Trade['Sell']=round(Trade['Close']+Trade['PCTValue'],8)
    Trade['Counter']-=1

    return(Trade)

def DecreaseTradeTable(Trade,close,SellAMT,direction,AllTimeHigh):
    if SellAMT>0.0:
        Trade['Profit']+=round((close-Trade['Close'])*SellAMT,8)
    if direction=='long':
        Trade['Close']=round(Trade['Sell'],8)
    else:
        Trade['Close']=round(Trade['Buy'],8)
    if direction=='short':
        Trade['Buy']= round(Trade['Close']-(AllTimeHigh*(pct*4)),8)
    else:
        Trade['Buy']= round(Trade['Close']-Trade['PCTValue'],8)
    Trade['Sell']=round(Trade['Close']+Trade['PCTValue'],8)
    Trade['Counter']-=1

    return(Trade)

def GetOrderID(res):
    s=res.find('ID:')+4
    for e in range(s,len(res)):
        if res[e]=='\n':
            break
    oid=res[s:e]

    return oid

def CheckStopTracer(exchangeName,account,Asset):
    fn=exchangeName+'.'+account+'.'+Asset.replace("-","").replace("/","").replace(':','')+'.stop'
    if os.path.exists(fn):
        JRRlog.SuccessLog("STOP", "tracer detected")

def CheckHaltTracer(exchangeName,account,Asset):
    fn=exchangeName+'.'+account+'.'+Asset.replace("-","").replace("/","").replace(':','')+'.halt'
    if os.path.exists(fn):
        JRRlog.SuccessLog("HALT", "tracer detected")

def ReadGrid(exchangeName,account,Asset):
    fn=exchangeName+'.'+account+'.'+Asset.replace("-","").replace("/","").replace(':','')+'.grid'
    if os.path.exists(fn):
        JRRlog.WriteLog("Reading Grid file")
        fh=open(fn,'r')
        for line in fh:
            Trade={}
            Trade=json.loads(line.rstrip())
        fh.close()
        JRRlog.WriteLog(f"|- {Asset:10} {Trade['Buy']:.8f} {Trade['Close']:.8f} {Trade['Sell']:.8f}")
    else:
        Trade={}
        Trade['PCTValue']=0.0
        Trade['Close']=0.0
        Trade['Buy']=0.0
        Trade['Sell']=0.0
        Trade['Counter']=0
        Trade['Profit']=0.0

    return(Trade)

def EraseGrid(exchangeName,account,Asset):
    fn=exchangeName+'.'+account+'.'+Asset.replace("-","").replace("/","").replace(':','')+'.grid'

    if os.path.exists(fn):
        os.remove(fn)

def WriteGrid(exchangeName,account,Trade,Asset):
    fn=exchangeName+'.'+account+'.'+Asset.replace("-","").replace("/","").replace(':','')+'.grid'

    fh=open(fn,'w')
    fh.write(json.dumps(Trade)+"\n")
    fh.close()

def WriteSpotLog(e,a,p,msg):
    PlaceOrderName=os.path.basename(sys.argv[0])
    pn=e+'.'+a+'.'+p.replace("-","").replace("/","").replace(':','')

    pid=os.getpid()
    time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

    s=f'{time} {pid:7.0f} {msg}\n'

    fh=open(JRRconfig.LogDirectory+'/'+PlaceOrderName+'.'+pn+'.log','a')
    fh.write(s)
    fh.close()
    print(s.rstrip())
    sys.stdout.flush()

def WriteFutureLog(e,a,p,d,msg):
    PlaceOrderName=os.path.basename(sys.argv[0])
    pn=e+'.'+a+'.'+p.replace("-","").replace("/","").replace(':','')

    pid=os.getpid()
    time=(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

    s=f'{time} {pid:7.0f} {msg}\n'

    fh=open(JRRconfig.LogDirectory+'/'+PlaceOrderName+'.'+d+'.'+pn+'.log','a')
    fh.write(s)
    fh.close()
    print(s.rstrip())
    sys.stdout.flush()

# Convert account balance to lots in steps

def Balance2Lots(exchange,pair,pct,RetryLimit):
    quote=exchange.markets[pair]['quote']
    if quote not in JRRconfig.StableCoinUSD:
        hasQuote=True
    else:
        hasQuote=False

# Get exchange required minimums

    minimum,mincost=JRRapi.GetMinimum(exchange,pair,hasQuote,False,RetryLimit)

# Convert balance to number of steps and lots

    bal=JRRapi.GetBalance(exchange,quote,RetryLimit)
    steps=100/(pct*100)
    priceStep=bal/steps
    Lots=priceStep/mincost

    if Lots<1:
        Lots=1

    return Lots

# Read CFG file

def ReadConfig(fn,Header):
    Required=[ "Exchange", "Account", "Asset", "Boundary", "BuyLots" ]

    Config={}

    JRRlog.WriteLog("Reading configuration file")

    if os.path.exists(fn):
        try:
            raw=pathlib.Path(fn).read_text()
        except:
            JRRlog.ErrorLog("ReadConfig",f"Can't read {fn}")

        txt=JRRsupport.pFilter(raw)

        try:
            Config=json.loads(txt)
        except:
            JRRlog.ErrorLog("ReadConfig",f"Damaged JSON: {txt}")
    else:
        JRRlog.ErrorLog("ReadConfig",'Config file not found.')

    for i in Required:
        if i not in Config:
            JRRlog.ErrorLog("ReadConfig",f"Missing required item: {i}")

    Config['Exchange']=Config['Exchange'].lower()
    Config['Asset']=Config['Asset'].upper()
    Config['Boundary']=float(Config['Boundary'])/100

    if "SellLots" not in Config:
        Config['SellLots']='Dynamic'

    if "OverSell" in Config:
        Config['OverSell']=float(Config['OverSell'])/100
    else:
        Config['OverSell']=20/100

    if "OrderType" not in Config:
        Config['OrderType']='Market'

    if "BuyStopHigh" in Config:
        Config['BuyStopHigh']=float(Config['BuyStopHigh'])
    else:
        Config['BuyStopHigh']=-1
    if "BuyStopLow" in Config:
        Config['BuyStopLow']=float(Config['BuyStopLow'])
    else:
        Config['BuyStopLow']=-1

    if "SellStopHigh" in Config:
        Config['SellStopHigh']=float(Config['SellStopHigh'])
    else:
        Config['SellStopHigh']=-1
    if "SellStopLow" in Config:
        Config['SellStopLow']=float(Config['SellStopLow'])
    else:
        Config['SellStopLow']=-1

    if "ExitProfit" in Config:
        Config['ExitProfit']=float(Config['ExitProfit'])
    else:
        Config['ExitProfit']=-1

    if "TakeProfit" in Config:
        Config['TakeProfit']=float(Config['TakeProfit'])
    else:
        Config['TakeProfit']=-1

    if 'Direction' not in Config:
        JRRlog.WriteSpotLog(Config['Exchange'],Config['Account'],Config['Asset'],Header)
        for i in Config:
            JRRlog.WriteSpotLog(Config['Exchange'],Config['Account'],Config['Asset'],f"|- {i}: {Config[i]}")
    else:
        direction=Config['Direction'].lower()
        JRRlog.WriteFutureLog(Config['Exchange'],Config['Account'],Config['Asset'],direction,Header)
        for i in Config:
            JRRlog.WriteFutureLog(Config['Exchange'],Config['Account'],Config['Asset'],direction,f"|- {i}: {Config[i]}")

    return(Config)

def TradeBuyAmount(Config,Trade,exchange,pair,pct,RetryLimit):
    minimum,mincost=JRRapi.GetMinimum(exchange,pair,False,False,RetryLimit)

    if Config['BuyLots'].lower()=='balance':
        Trade['BuyLots']=round(Balance2Lots(exchange,pair,pct,RetryLimit),8)
        Trade['BuyAmount']=round(Trade['BuyLots']*minimum,8)
    else:
        Trade['BuyLots']=Config['BuyLots']
        p=float(Trade['BuyLots'])
        if p<1:
            p=1
        Trade['BuyAmount']=round(minimum*p,8)

    return Trade

def TradeSellAmount(Config,Trade,exchange,pair,pct,RetryLimit):
    minimum,mincost=JRRapi.GetMinimum(exchange,pair,False,False,RetryLimit)

    if Config['SellLots'].lower()=='dynamic':
        if Trade['Counter']>0:
            pb=(Config['OverSell']/100)*(Trade['Counter']/(100*pct))*pct
            ba=float(Trade['BuyLots'])*minimum
            Trade['SellAmount']=round(ba+(ba*pb),8)
        else:
            Trade['SellAmount']=float(Trade['BuyAmount'])
    elif Config['SellLots'].lower()=='buylots':
        Trade['SellAmount']=float(Trade['BuyAmount'])
    else:
        Trade['SellAmount']=round(minimum*float(Config['SellLots']),8)

    return Trade

def CheckHighLow(c,l,h):
    if l==-1 and h==-1:
        return True

    if c>=l and h==-1:
        return True
    else:
        return False

    if l==-1 and c<=h:
        return True
    else:
        return False

    if c>=l and c<=h:
        return True
    else:
        return False
